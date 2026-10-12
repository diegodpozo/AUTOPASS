import os
import sys
import subprocess
import threading
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import models
import schemas
from models.enums import UserRole
from core.database import get_db
from core.security import get_operational_user
from core.alpr_security import require_alpr_node
from core.logger import get_logger
from routes.system.common import CAMERA_PROCESSES, CameraConfig, normalize_system_name, misma_sucursal
from routes.system.common import manager as video_manager
from repositories.camera_repository import CameraRepository
from repositories.settings_repository import SettingsRepository
from repositories.branch_repository import BranchRepository

logger = get_logger("Cameras")

try:
    import locale
    _console_encoding = locale.getpreferredencoding(False) or "utf-8"
except Exception:
    _console_encoding = "utf-8"

def _schedule_async(coro):
    """PROGRAMA UNA COROUTINA EN EL LOOP PRINCIPAL DE UVICORN DESDE UN HILO SECUNDARIO."""
    try:
        from services.notification_service import NotificationService
        loop = NotificationService._loop
        if loop and loop.is_running():
            import asyncio
            asyncio.run_coroutine_threadsafe(coro, loop)
            return True
    except Exception:
        pass
    return False

def _stream_console_output(proc: subprocess.Popen, camera_id: str):
    """LEE EL STDOUT DEL SUBPROCESO ALPR EN UN HILO Y REENVIA CADA LINEA AL FRONT
    POR EL WEBSOCKET DE VIDEO DE ESA CAMARA. NO ALTERA EL FLUJO DE FRAMES NI LOS
    MENSAJES DE EVENTO EXISTENTES (ruta paralela puramente aditiva)."""
    try:
        for raw in iter(proc.stdout.readline, b""):
            line = raw.decode(_console_encoding, errors="replace").rstrip("\n").rstrip("\r")
            if line.strip():
                _schedule_async(video_manager.broadcast_console(camera_id, line))
        proc.stdout.close()
    except Exception as e:
        logger.debug(f"Fin del stream de consola {camera_id}: {e}")
    finally:
        try:
            proc.stdout = None
        except Exception:
            pass

router = APIRouter()

@router.get("/camera-config/{gate_id}")
def get_camera_config(gate_id: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    gate_id = gate_id.upper()
    if staff.rol != UserRole.ADMIN and staff.sucursal:
        branch_prefix = gate_id.split('_')[0]
        if branch_prefix != normalize_system_name(staff.sucursal):
            raise HTTPException(status_code=403, detail="No tenés acceso a esta configuración")
             
    setting = SettingsRepository.get_by_clave(db, f"CAMERA_SOURCE_{gate_id}")
    
    source = setting.valor_str if setting else "0"
    is_running = gate_id in CAMERA_PROCESSES and CAMERA_PROCESSES[gate_id].poll() is None
    
    return {"gate_id": gate_id, "source": source, "is_running": is_running}

@router.post("/camera-config")
def set_camera_config(config: CameraConfig, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    gate_id = config.gate_id.upper()
    if staff.rol != UserRole.ADMIN:
        branch_prefix = normalize_system_name(staff.sucursal)
        if not gate_id.startswith(branch_prefix):
            raise HTTPException(status_code=403, detail="No tenés acceso a esta configuración")
            
    setting = SettingsRepository.get_by_clave(db, f"CAMERA_SOURCE_{gate_id}")
    
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
    if staff.rol != UserRole.ADMIN:
        branch_prefix = normalize_system_name(staff.sucursal)
        if not gate_id.startswith(branch_prefix):
            raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")

    if action == "start":
        if gate_id in CAMERA_PROCESSES and CAMERA_PROCESSES[gate_id].poll() is None:
            return {"status": "error", "message": "Ya está en ejecución"}
            
        setting = SettingsRepository.get_by_clave(db, f"CAMERA_SOURCE_{gate_id}")
        source = setting.valor_str if setting else "0"
        # El ALPR corre en la misma máquina que el backend: conectar por localhost
        # (no a través de un túnel) para evitar el doble-hop de los frames de video.
        base_url = f"http://127.0.0.1:{request.url.port or 8000}"
        
        env = os.environ.copy()
        env["GATE_ID"] = gate_id
        env["VIDEO_SOURCE"] = source
        if "QR" in gate_id.upper():
            env["GATE_TYPE"] = "qr"
        else:
            env["GATE_TYPE"] = "entrada" if "ENTRADA" in gate_id else "salida"
        env["BACKEND_URL"] = base_url
        env["PYTHONUNBUFFERED"] = "1"
        
        try:
            logger.info(f"Iniciando ALPR para {gate_id} con fuente: {source}")
            proc = subprocess.Popen(
                [sys.executable, "alpr_service.py"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            CAMERA_PROCESSES[gate_id] = proc
            threading.Thread(target=_stream_console_output, args=(proc, gate_id), daemon=True).start()
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

@router.get("/cameras", response_model=List[schemas.CameraResponse])
def get_cameras(db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    query = CameraRepository.get_all(db)
    if staff.rol != UserRole.ADMIN and staff.sucursal:
        query = [c for c in query if misma_sucursal(c, staff)]
    cameras = query
    res = []
    for c in cameras:
        norm_suc = normalize_system_name(c.sucursal) if c.sucursal else "GLOBAL"
        proc_id = f"{norm_suc}_{c.tipo}_{c.id}".upper()
        is_running = proc_id in CAMERA_PROCESSES and CAMERA_PROCESSES[proc_id].poll() is None
        res.append(schemas.CameraResponse(
            id=c.id,
            nombre=c.nombre,
            tipo=c.tipo,
            source=c.source,
            activa=c.activa,
            sucursal=c.sucursal,
            is_running=is_running
        ))
    return res

@router.post("/cameras", response_model=schemas.CameraResponse)
def create_camera(data: schemas.CameraCreate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    sucursal = staff.sucursal if staff.rol != UserRole.ADMIN else data.sucursal
    new_cam = models.ParkingCamera(
        nombre=data.nombre,
        tipo=data.tipo.upper(),
        source=data.source,
        sucursal=sucursal,
        activa=data.activa
    )
    db.add(new_cam)
    db.commit()
    db.refresh(new_cam)
    return schemas.CameraResponse(
        id=new_cam.id,
        nombre=new_cam.nombre,
        tipo=new_cam.tipo,
        source=new_cam.source,
        activa=new_cam.activa,
        sucursal=new_cam.sucursal,
        is_running=False
    )

@router.put("/cameras/{camera_id}", response_model=schemas.CameraResponse)
def update_camera(camera_id: int, data: schemas.CameraCreate, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    camera = CameraRepository.get_by_id(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    if staff.rol != UserRole.ADMIN and not misma_sucursal(camera, staff):
        raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")
    camera.nombre = data.nombre
    camera.tipo = data.tipo.upper()
    camera.source = data.source
    camera.activa = data.activa
    if staff.rol == UserRole.ADMIN:
        camera.sucursal = data.sucursal
    db.commit()
    db.refresh(camera)
    
    norm_suc = normalize_system_name(camera.sucursal) if camera.sucursal else "GLOBAL"
    proc_id = f"{norm_suc}_{camera.tipo}_{camera.id}".upper()
    is_running = proc_id in CAMERA_PROCESSES and CAMERA_PROCESSES[proc_id].poll() is None
    
    return schemas.CameraResponse(
        id=camera.id,
        nombre=camera.nombre,
        tipo=camera.tipo,
        source=camera.source,
        activa=camera.activa,
        sucursal=camera.sucursal,
        is_running=is_running
    )

@router.delete("/cameras/{camera_id}")
def delete_camera(camera_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    camera = CameraRepository.get_by_id(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    if staff.rol != UserRole.ADMIN and not misma_sucursal(camera, staff):
        raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")
        
    norm_suc = normalize_system_name(camera.sucursal) if camera.sucursal else "GLOBAL"
    proc_id = f"{norm_suc}_{camera.tipo}_{camera.id}".upper()
    if proc_id in CAMERA_PROCESSES:
        proc = CAMERA_PROCESSES[proc_id]
        try:
            if proc.poll() is None:
                if os.name == 'nt':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    proc.terminate()
        except Exception:
            pass
        del CAMERA_PROCESSES[proc_id]
        
    db.delete(camera)
    db.commit()
    return {"status": "ok", "message": "Cámara eliminada"}

@router.post("/cameras/{camera_id}/control/{action}")
def control_dynamic_camera_service(camera_id: int, action: str, request: Request, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    camera = CameraRepository.get_by_id(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Cámara no encontrada")
    if staff.rol != UserRole.ADMIN and not misma_sucursal(camera, staff):
        raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")
        
    norm_suc = normalize_system_name(camera.sucursal) if camera.sucursal else "GLOBAL"
    proc_id = f"{norm_suc}_{camera.tipo}_{camera.id}".upper()
    
    if action == "start":
        if proc_id in CAMERA_PROCESSES and CAMERA_PROCESSES[proc_id].poll() is None:
            return {"status": "error", "message": "Ya está en ejecución"}
            
        # El ALPR corre en la misma máquina que el backend: conectar por localhost
        # (no a través de un túnel) para evitar el doble-hop de los frames de video.
        base_url = f"http://127.0.0.1:{request.url.port or 8000}"
        env = os.environ.copy()
        env["GATE_ID"] = proc_id
        env["VIDEO_SOURCE"] = camera.source
        gt = camera.tipo.lower()
        if "qr" in gt:
            env["GATE_TYPE"] = "qr"
        elif "egreso" in gt or "salida" in gt:
            env["GATE_TYPE"] = "salida"
        elif "patente" in gt or "entrada" in gt:
            env["GATE_TYPE"] = "entrada"
        else:
            env["GATE_TYPE"] = gt
        env["BACKEND_URL"] = base_url
        env["PYTHONUNBUFFERED"] = "1"
        
        try:
            logger.info(f"Iniciando ALPR para {camera.nombre} ({proc_id}) con fuente: {camera.source}")
            proc = subprocess.Popen(
                [sys.executable, "alpr_service.py"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            CAMERA_PROCESSES[proc_id] = proc
            threading.Thread(target=_stream_console_output, args=(proc, proc_id), daemon=True).start()
            return {"status": "ok", "message": f"Servicio para {camera.nombre} iniciado"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    elif action == "stop":
        if proc_id not in CAMERA_PROCESSES:
            return {"status": "error", "message": "No está en ejecución"}
            
        proc = CAMERA_PROCESSES[proc_id]
        try:
            if proc.poll() is None:
                if os.name == 'nt':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    proc.terminate()
            if proc_id in CAMERA_PROCESSES:
                del CAMERA_PROCESSES[proc_id]
            return {"status": "ok", "message": f"Servicio para {camera.nombre} detenido"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    return {"status": "error", "message": "Acción no válida"}

@router.post("/camera-reading/{gate_id}", dependencies=[Depends(require_alpr_node)])
def notify_camera_reading(gate_id: str, db: Session = Depends(get_db)):
    """NOTIFICA AL DASHBOARD QUE LA CAMARA ESTA LEYENDO ACTIVAMENTE UNA PATENTE.
    Solo nodos ALPR autorizados (secret o red local): evita spoofing del estado operativo."""
    from core.normalize import normalize_user_name as normalize_name
    from services.notification_service import NotificationService
    sucursal = None
    if '_' in gate_id:
        suc_short = normalize_name(gate_id.split('_')[0])
        try:
            branches = BranchRepository.get_all(db)
            for b in branches:
                if normalize_name(b.nombre) == suc_short:
                    sucursal = b.nombre
                    break
        except Exception:
            pass
    suc_norm = normalize_name(sucursal) if sucursal else "GLOBAL"
    NotificationService.set_last_event(suc_norm, "READING", "", "LEYENDO PATENTE...", "reading")
    return {"status": "ok"}
