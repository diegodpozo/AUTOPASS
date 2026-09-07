import os
import base64
import time
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
import models
from models.enums import UserRole
from core.database import get_db
from core.security import get_operational_user, decode_access_token
from core.config import settings
from core.logger import get_logger
from routes.system.common import manager, normalize_system_name

logger = get_logger("VideoWS")

router = APIRouter()

@router.websocket("/ws/video/{camera_id}")
async def websocket_video_endpoint(websocket: WebSocket, camera_id: str, token: str = Query(None)):
    """Endpoint WebSocket con seguridad por token y aislamiento por sucursal."""
    camera_id = camera_id.upper()
    user = None
    if token:
        try:
            payload = decode_access_token(token)
            db = next(get_db())
            user = db.query(models.User).filter(models.User.email == payload.get("sub")).first()
        except Exception:
            pass

    if not user:
        logger.info(f"Nodo ALPR conectado: {camera_id}")
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                await manager.broadcast_frame(camera_id, data)
        except WebSocketDisconnect:
            logger.info(f"Nodo ALPR desconectado: {camera_id}")
        except Exception as e:
            logger.error(f"Error en nodo ALPR {camera_id}: {e}")
    else:
        logger.info(f"Espectador conectado: {user.email} -> {camera_id}")
        success = await manager.connect(websocket, camera_id, user)
        if success:
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                logger.info(f"Espectador desconectado: {user.email} -> {camera_id}")
                manager.disconnect(websocket, camera_id)

@router.post("/update-frame/{camera_id}")
async def update_frame_http(camera_id: str, request: Request):
    raw_body = await request.json()
    if "image" in raw_body:
        await manager.broadcast_frame(camera_id, raw_body["image"])
    return {"status": "ok"}

@router.get("/video-feed/{camera_id}")
async def video_feed_legacy(camera_id: str, staff: models.User = Depends(get_operational_user)):
    """Streaming de video MJPEG fallback."""
    if staff.rol != "admin" and staff.sucursal:
        branch_prefix = camera_id.split('_')[0]
        # Comparar contra la sucursal normalizada (misma lógica que el WebSocket)
        if branch_prefix.upper() != normalize_system_name(staff.sucursal):
            raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")

    def gen_frames():
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

def _user_from_token(token: str, db: Session):
    """Resuelve el usuario autenticado desde un JWT (query o header)."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    user = db.query(models.User).filter(
        models.User.email == payload.get("sub"),
        models.User.is_deleted == False
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    if str(user.rol) not in [UserRole.ADMIN.value, UserRole.LOCAL_ADMIN.value, UserRole.STAFF.value]:
        raise HTTPException(status_code=403, detail="Acceso restringido a personal autorizado")
    return user

@router.get("/capture/{log_id}")
def get_capture(log_id: int, request: Request, token: str = Query(None), db: Session = Depends(get_db)):
    """Imagen capturada de un log. Acepta el token por query (para <img>) o por header Bearer."""
    staff = None
    auth_header = request.headers.get("Authorization", "")
    if token:
        staff = _user_from_token(token, db)
    elif auth_header.lower().startswith("bearer "):
        staff = _user_from_token(auth_header[7:], db)
    else:
        raise HTTPException(status_code=401, detail="No autenticado")

    log = db.query(models.AccessLog).filter(models.AccessLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log no encontrado")
    if str(staff.rol) != UserRole.ADMIN.value and log.sucursal != staff.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos")
    if log.imagen_path:
        full_path = os.path.abspath(os.path.join(settings.IMAGE_DIR, log.imagen_path))
        if os.path.exists(full_path):
            return FileResponse(full_path)
    return FileResponse(os.path.join("static", "images", "logo.png"))
