import os
import datetime
import base64
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import models
from core.database import get_db
from core.security import get_super_admin, get_operational_user
from core.config import settings

router = APIRouter(prefix="/v1/system", tags=["System & Health"])

# Buffer global para transmisión de video en vivo
video_feeds = {}

@router.post("/reset")
def reset_system(db: Session = Depends(get_db), admin: models.User = Depends(get_super_admin)):
    """Restablece el sistema eliminando todos los registros dinámicos y archivos multimedia."""
    IMAGE_DIR = settings.IMAGE_DIR
    db.query(models.AccessLog).delete()
    db.query(models.ParkingAforo).delete() # Reset de todos los aforos
    db.query(models.Reservation).delete()
    db.query(models.Vehicle).delete()
    db.query(models.User).filter(models.User.rol == 'user').delete() # Solo borrar clientes
    db.commit()
    
    if os.path.exists(IMAGE_DIR):
        for f in os.listdir(IMAGE_DIR): 
            try: os.unlink(os.path.join(IMAGE_DIR, f))
            except: pass
    return {"status": "ok"}

ALPR_HEARTBEATS = {}
@router.post("/heartbeat")
def alpr_heartbeat(gate_id: str):
    """Registra un pulso de vida de un servicio ALPR remoto."""
    gate_id = gate_id.strip().upper()
    ALPR_HEARTBEATS[gate_id] = datetime.datetime.now()
    return {"status": "ok"}

@router.get("/health")
def get_health(db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Retorna el estado de salud filtrado por sede (si no es global)."""
    db_ok = True
    try: db.execute(text("SELECT 1"))
    except: db_ok = False
    
    now = datetime.datetime.now()
    alpr_status = {}
    
    # En un sistema multi-sede, filtraríamos los heartbeats por prefijo de sede
    prefix = f"{staff.sucursal.upper()}_" if staff.rol != "admin" and staff.sucursal else ""
    
    gates_to_check = [f"{prefix}ENTRADA", f"{prefix}SALIDA"]
    if not prefix: gates_to_check = ["ENTRADA_PRINCIPAL", "SALIDA_PRINCIPAL"]

    for gate in gates_to_check:
        status = "OFFLINE"
        if gate in ALPR_HEARTBEATS:
            if (now - ALPR_HEARTBEATS[gate]).total_seconds() < 90: status = "ONLINE"
        alpr_status[gate] = status
        
    return {"database": "ONLINE" if db_ok else "OFFLINE", "alpr": alpr_status, "api": "ONLINE"}

# --- MANEJO DE VIDEO STREAMING ---

@router.post("/update-frame/{camera_id}")
async def update_frame(camera_id: str, request: Request):
    """Recibe un nuevo frame de video codificado en base64."""
    raw_body = await request.json()
    if "image" in raw_body:
        video_feeds[camera_id] = raw_body["image"]
    return {"status": "ok"}

def gen_frames(camera_id: str):
    """Generador para transmitir frames de video en formato multipart."""
    import time
    while True:
        frame_base64 = video_feeds.get(camera_id)
        if frame_base64:
            frame_bytes = base64.b64decode(frame_base64)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n'
                   b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' + 
                   frame_bytes + b'\r\n')
        else:
            time.sleep(0.1)
            continue
        time.sleep(0.01)

@router.get("/video-feed/{camera_id}")
async def video_feed(camera_id: str):
    """Endpoint para visualización de video en tiempo real vía MJPEG."""
    return StreamingResponse(gen_frames(camera_id),
                             media_type="multipart/x-mixed-replace; boundary=frame")

@router.get("/capture/{log_id}")
def get_capture(log_id: int, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Retorna la imagen capturada. Aislamiento por sede."""
    from fastapi.responses import FileResponse
    
    log = db.query(models.AccessLog).filter(models.AccessLog.id == log_id).first()
    if not log: raise HTTPException(status_code=404, detail="Log no encontrado")
    
    # Aislamiento por sede
    if staff.rol != "admin" and log.sucursal != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos para ver capturas de otra sede")

    # Intentar obtener la imagen del log
    if log.imagen_path:
        full_path = os.path.abspath(log.imagen_path)
        if os.path.exists(full_path):
            return FileResponse(full_path)
            
    # Fallback para demo
    fallback_dir = "captured_images/INICIO"
    if os.path.exists(fallback_dir):
        files = os.listdir(fallback_dir)
        if files:
            import random
            return FileResponse(os.path.join(fallback_dir, random.choice(files)))
    
    raise HTTPException(status_code=404, detail="Captura no encontrada")
