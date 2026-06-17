import os
import datetime
import base64
import asyncio
import subprocess
import sys
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List
from pydantic import BaseModel
import models
import unicodedata
from core.database import get_db
from core.security import get_super_admin, get_operational_user, decode_access_token
from core.config import settings

router = APIRouter(tags=["System & Health"])

# --- GESTIÓN DE PROCESOS DE CÁMARA (ALPR) ---
CAMERA_PROCESSES: Dict[str, subprocess.Popen] = {}

class CameraConfig(BaseModel):
    gate_id: str
    source: str

def get_sys_executable():
    return sys.executable

def stop_all_cameras():
    """Detiene todos los servicios ALPR activos. Llamado al apagar el servidor."""
    for gate_id in list(CAMERA_PROCESSES.keys()):
        try:
            proc = CAMERA_PROCESSES[gate_id]
            if proc.poll() is None:
                if os.name == 'nt':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    proc.terminate()
            print(f"[System] Cámara {gate_id} detenida correctamente.")
        except: pass
    CAMERA_PROCESSES.clear()

# --- GESTIÓN DE WEBSOCKETS CON AISLAMIENTO ---

def normalize_system_name(text: str):
    """Normalización idéntica a la del Frontend y ALPR Service."""
    if not text: return ""
    text = text.upper().replace("AUTOPASS ", "").strip()
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

class ConnectionManager:
    def __init__(self):
        # camera_id -> list of active websockets (viewers)
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # camera_id -> last frame (for new viewers)
        self.last_frames: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, camera_id: str, user: models.User):
        """Valida permisos antes de conectar."""
        # Aislamiento: El camera_id ya viene normalizado del frontend (ej: ITUZAINGO_ENTRADA)
        if user.rol != "admin":
            branch_prefix = camera_id.split('_')[0] if '_' in camera_id else ""
            user_branch_norm = normalize_system_name(user.sucursal)
            
            if branch_prefix and user_branch_norm and branch_prefix != user_branch_norm:
                print(f"[WS Auth] Bloqueado: Usuario de {user_branch_norm} intentó ver {branch_prefix}")
                await websocket.close(code=4003) # Forbidden
                return False

        await websocket.accept()
        if camera_id not in self.active_connections:
            self.active_connections[camera_id] = []
        self.active_connections[camera_id].append(websocket)
        
        if camera_id in self.last_frames:
            await websocket.send_text(self.last_frames[camera_id])
        return True

    def disconnect(self, websocket: WebSocket, camera_id: str):
        if camera_id in self.active_connections:
            try:
                self.active_connections[camera_id].remove(websocket)
            except ValueError: pass

    async def broadcast_frame(self, camera_id: str, frame_base64: str):
        self.last_frames[camera_id] = frame_base64
        if camera_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[camera_id]:
                try:
                    await connection.send_text(frame_base64)
                except:
                    disconnected.append(connection)
            
            for conn in disconnected:
                self.disconnect(conn, camera_id)

manager = ConnectionManager()

@router.websocket("/ws/video/{camera_id}")
async def websocket_video_endpoint(websocket: WebSocket, camera_id: str, token: str = Query(None)):
    """
    Endpoint WebSocket con seguridad por Token y Sucursal.
    """
    camera_id = camera_id.upper()
    user = None
    if token:
        try:
            # Validar token para viewers (Frontend)
            payload = decode_access_token(token)
            db = next(get_db())
            user = db.query(models.User).filter(models.User.email == payload.get("sub")).first()
        except: pass

    # Si no hay usuario (es un nodo ALPR) o es un usuario válido
    if not user:
        # Los nodos ALPR solo aceptan la conexión si vienen de una fuente permitida (esto se refina en firewall)
        # Para esta implementación, aceptamos el nodo y lo tratamos como "Sender"
        print(f"[WS] Nodo ALPR conectado: {camera_id}")
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                await manager.broadcast_frame(camera_id, data)
        except WebSocketDisconnect:
            print(f"[WS] Nodo ALPR desconectado: {camera_id}")
        except Exception as e:
            print(f"[WS] Error en nodo ALPR {camera_id}: {e}")
    else:
        # Es un espectador (Admin/Staff), validar sucursal
        print(f"[WS] Espectador conectado: {user.email} -> {camera_id}")
        success = await manager.connect(websocket, camera_id, user)
        if success:
            try:
                while True:
                    await websocket.receive_text() # Mantener viva pero ignorar subidas de viewers
            except WebSocketDisconnect:
                print(f"[WS] Espectador desconectado: {user.email} -> {camera_id}")
                manager.disconnect(websocket, camera_id)

# --- RESTO DE ENDPOINTS (Mantenidos igual pero con lógica de aislamiento aplicada) ---

@router.get("/health")
def get_health(db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    db_ok = True
    try: db.execute(text("SELECT 1"))
    except: db_ok = False
    
    now = datetime.datetime.now()
    alpr_status = {}
    
    # Aislamiento en el estado de salud
    if staff.rol == "admin":
        # Super admin ve todo
        for gate, ts in ALPR_HEARTBEATS.items():
            alpr_status[gate] = "ONLINE" if (now - ts).total_seconds() < 90 else "OFFLINE"
    else:
        # Staff solo ve sus cámaras
        prefix = f"{staff.sucursal.upper()}_" if staff.sucursal else ""
        gates_to_check = [f"{prefix}ENTRADA", f"{prefix}SALIDA"]
        for gate in gates_to_check:
            status = "OFFLINE"
            if gate in ALPR_HEARTBEATS:
                if (now - ALPR_HEARTBEATS[gate]).total_seconds() < 90: status = "ONLINE"
            alpr_status[gate] = status
        
    return {"database": "ONLINE" if db_ok else "OFFLINE", "alpr": alpr_status, "api": "ONLINE"}

@router.post("/reset")
def reset_system(db: Session = Depends(get_db), admin: models.User = Depends(get_super_admin)):
    IMAGE_DIR = settings.IMAGE_DIR
    db.query(models.AccessLog).delete()
    db.query(models.ParkingAforo).delete()
    db.query(models.Reservation).delete()
    db.query(models.Vehicle).delete()
    db.query(models.User).filter(models.User.rol == 'user').delete()
    db.commit()
    if os.path.exists(IMAGE_DIR):
        for f in os.listdir(IMAGE_DIR):
            try: os.unlink(os.path.join(IMAGE_DIR, f))
            except: pass
    return {"status": "ok"}

ALPR_HEARTBEATS = {}
@router.post("/heartbeat")
def alpr_heartbeat(gate_id: str):
    gate_id = gate_id.strip().upper()
    ALPR_HEARTBEATS[gate_id] = datetime.datetime.now()
    return {"status": "ok"}

@router.post("/update-frame/{camera_id}")
async def update_frame_http(camera_id: str, request: Request):
    raw_body = await request.json()
    if "image" in raw_body:
        await manager.broadcast_frame(camera_id, raw_body["image"])
    return {"status": "ok"}

@router.get("/video-feed/{camera_id}")
async def video_feed_legacy(camera_id: str, staff: models.User = Depends(get_operational_user)):
    """Fallback con validación de sucursal."""
    if staff.rol != "admin" and staff.sucursal:
        branch_prefix = camera_id.split('_')[0]
        if branch_prefix.upper() != staff.sucursal.upper():
            raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")

    def gen_frames():
        import time
        while True:
            frame_base64 = manager.last_frames.get(camera_id)
            if frame_base64:
                frame_bytes = base64.b64decode(frame_base64)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' + 
                       frame_bytes + b'\r\n')
            time.sleep(0.1)
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@router.get("/capture/{log_id}")
def get_capture(log_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    from fastapi.responses import FileResponse
    log = db.query(models.AccessLog).filter(models.AccessLog.id == log_id).first()
    if not log: raise HTTPException(status_code=404, detail="Log no encontrado")
    if staff.rol != "admin" and log.sucursal != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos")
    if log.imagen_path:
        full_path = os.path.abspath(os.path.join(settings.IMAGE_DIR, log.imagen_path))
        if os.path.exists(full_path): return FileResponse(full_path)
    return FileResponse(os.path.join("static", "images", "logo.png"))

# --- ENDPOINTS DE CONFIGURACIÓN Y CONTROL DE CÁMARAS ---

@router.get("/camera-config/{gate_id}")
def get_camera_config(gate_id: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    gate_id = gate_id.upper()
    # Aislamiento por sucursal
    if staff.rol != "admin" and staff.sucursal:
        branch_prefix = gate_id.split('_')[0]
        if branch_prefix != normalize_system_name(staff.sucursal):
             raise HTTPException(status_code=403, detail="No tenés acceso a esta configuración")
             
    setting = db.query(models.Settings).filter(
        models.Settings.clave == f"CAMERA_SOURCE_{gate_id}"
    ).first()
    
    source = setting.valor_str if setting else "0"
    is_running = gate_id in CAMERA_PROCESSES and CAMERA_PROCESSES[gate_id].poll() is None
    
    return {"gate_id": gate_id, "source": source, "is_running": is_running}

@router.post("/camera-config")
def set_camera_config(config: CameraConfig, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    gate_id = config.gate_id.upper()
    # Aislamiento
    if staff.rol != "admin":
        branch_prefix = normalize_system_name(staff.sucursal)
        if not gate_id.startswith(branch_prefix):
            raise HTTPException(status_code=403, detail="No tenés acceso a esta configuración")
            
    setting = db.query(models.Settings).filter(
        models.Settings.clave == f"CAMERA_SOURCE_{gate_id}"
    ).first()
    
    if not setting:
        setting = models.Settings(clave=f"CAMERA_SOURCE_{gate_id}", valor_str=config.source, sucursal=staff.sucursal)
        db.add(setting)
    else:
        setting.valor_str = config.source
    
    db.commit()
    return {"status": "ok", "message": "Configuración guardada"}

@router.post("/camera-service/{gate_id}/{action}")
def control_camera_service(gate_id: str, action: str, request: Request, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    gate_id = gate_id.upper()
    # Aislamiento
    if staff.rol != "admin":
        branch_prefix = normalize_system_name(staff.sucursal)
        if not gate_id.startswith(branch_prefix):
            raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")

    if action == "start":
        if gate_id in CAMERA_PROCESSES and CAMERA_PROCESSES[gate_id].poll() is None:
            return {"status": "error", "message": "Ya está en ejecución"}
            
        setting = db.query(models.Settings).filter(models.Settings.clave == f"CAMERA_SOURCE_{gate_id}").first()
        source = setting.valor_str if setting else "0"
        
        # Obtener la URL base del backend dinámicamente
        base_url = str(request.base_url).rstrip("/")
        
        env = os.environ.copy()
        env["GATE_ID"] = gate_id
        env["VIDEO_SOURCE"] = source
        env["GATE_TYPE"] = "entrada" if "ENTRADA" in gate_id else "salida"
        env["BACKEND_URL"] = base_url
        
        try:
            print(f"[*] Iniciando ALPR para {gate_id} con fuente: {source}")
            print(f"[*] Backend URL inyectada: {base_url}")
            proc = subprocess.Popen(
                [sys.executable, "alpr_service.py"],
                env=env,
                stdout=None, # Permitir que salga a la consola del server para debug
                stderr=None,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            CAMERA_PROCESSES[gate_id] = proc
            return {"status": "ok", "message": "Servicio iniciado"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    elif action == "stop":
        if gate_id not in CAMERA_PROCESSES:
            return {"status": "error", "message": "No está en ejecución"}
            
        proc = CAMERA_PROCESSES[gate_id]
        try:
            if proc.poll() is None:
                if os.name == 'nt':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    proc.terminate()
            if gate_id in CAMERA_PROCESSES:
                del CAMERA_PROCESSES[gate_id]
            return {"status": "ok", "message": "Servicio detenido"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    return {"status": "error", "message": "Acción no válida"}
