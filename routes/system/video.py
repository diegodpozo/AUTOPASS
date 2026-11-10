'''Expone el feed de video vía HTTP para que cualquier navegador web pueda ver la cámara en vivo'''



import os								# Importa `os` para armar y verificar rutas
import base64								# Importa `base64` para decodificar el frame JPEG
import time								# Importa `time` para pausar el generador MJPEG
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, Query
									# Importa de FastAPI routers, dependencias, errores
									# HTTP, request, WebSocket y `Query`
from fastapi.responses import StreamingResponse, FileResponse		# Importa `StreamingResponse` y `FileResponse`
from sqlalchemy.orm import Session					# Importa `Session` de SQLAlchemy
import models								# Importa `models` con las entidades ORM
from models.enums import UserRole					# Importa `UserRole` para comparar roles
from core.database import get_db					# Importa `get_db` (sesion por peticion)
from core.security import get_operational_user, decode_access_token	# Importa `get_operational_user` y
									# `decode_access_token`
from core.normalize import same_branch					# Importa `same_branch` para comparar sucursales
from core.config import settings					# Importa `settings` (configuracion central)
from core.logger import get_logger, mask_email				# Importa `get_logger` y `mask_email` para logs
from core.alpr_security import is_local_or_private as _is_local_or_private, is_trusted_alpr_node as _is_trusted_alpr_node
									# Importa helpers ALPR de red y nodo confiable
from routes.system.common import manager, normalize_system_name		# Importa `manager` y `normalize_system_name`
from repositories.user_repository import UserRepository			# Importa `UserRepository` (busqueda de usuarios)
from repositories.access_log_repository import AccessRepository		# Importa `AccessRepository` (logs de acceso)

logger = get_logger("VideoWS")						# Crea el logger `VideoWS` del modulo

router = APIRouter()							# Crea el `router` de FastAPI

@router.websocket("/ws/video/{camera_id}")				# Decorador del WebSocket `/ws/video/{camera_id}`
async def websocket_video_endpoint(websocket: WebSocket, camera_id: str, token: str = Query(None), node_secret: str = Query(None)):
									# Define el WebSocket con `camera_id`, `token` y
									# `node_secret`
    """Endpoint WebSocket con seguridad por token y aislamiento por sucursal.
    Los nodos ALPR se autentican por node_secret (si esta configurado) o red local/privada.
    Los espectadores requieren rol STAFF+."""
    camera_id = camera_id.upper()					# Normaliza el id de camara a mayusculas
    user = None								# Inicializa `user` en None
    if token:								# Si hay token JWT, intenta autenticar
        db = None							# Inicializa `db` en None para el `finally`
        try:								# Abre un `try` para decodificar el token
            payload = decode_access_token(token)			# Decodifica el JWT y obtiene el payload
            db = next(get_db())						# Abre una sesion de base de datos manualmente
            user = UserRepository.get_active_by_email(db, payload.get("sub"))
									# Busca el usuario activo por el email (`sub`)
        except Exception:						# Captura cualquier fallo de autenticacion
            pass							# Ignora el error; `user` queda en None
        finally:							# Ejecuta el cierre de la sesion pase lo que pase
            if db:							# Si se abrio una sesion, la cierra
                try:							# Abre un `try` para cerrar la sesion
                    db.close()						# Cierra la sesion de base de datos
                except Exception:					# Captura un error al cerrar la sesion
                    pass						# Ignora el error de cierre

    if not user:							# Si no hay usuario, asume nodo ALPR
        peer = websocket.client.host if websocket.client else ""	# Obtiene la IP del cliente (o cadena vacia)
        if not _is_trusted_alpr_node(peer, node_secret or ""):		# Verifica IP y `node_secret` del nodo ALPR
            logger.warning(f"Intento de conexión de nodo no autorizado: {camera_id} desde {peer}")
									# Registra el intento de conexion no autorizado
            await websocket.close(code=4403)				# Cierra el WebSocket con codigo 4403 (prohibido)
            return							# Corta el endpoint sin aceptar la conexion
        logger.info(f"Nodo ALPR conectado: {camera_id}")		# Registra la conexion del nodo ALPR
        await websocket.accept()					# Acepta el WebSocket del nodo ALPR
        try:								# Abre un `try` para recibir frames del nodo
            while True:							# Bucle infinito mientras el nodo siga conectado
                data = await websocket.receive_text()			# Espera el siguiente frame en texto (Base64)
                await manager.broadcast_frame(camera_id, data)		# Reenvia el frame a los espectadores de la camara
        except WebSocketDisconnect:					# Captura la desconexion normal del nodo
            logger.info(f"Nodo ALPR desconectado: {camera_id}")		# Registra la desconexion del nodo ALPR
        except Exception as e:						# Captura cualquier otro error del nodo
            logger.error(f"Error en nodo ALPR {camera_id}: {e}")	# Registra el error del nodo ALPR con su id
    else:								# Si hay usuario, lo trata como espectador
        if str(user.rol) not in [UserRole.ADMIN.value, UserRole.LOCAL_ADMIN.value, UserRole.STAFF.value]:
									# Verifica rol ADMIN, LOCAL_ADMIN o STAFF
            logger.warning(f"Conexión rechazada a video: role {user.rol} ({mask_email(user.email)})")
									# Registra rechazo con rol y email enmascarado
            await websocket.close(code=4403)				# Cierra el WebSocket con codigo 4403 (prohibido)
            return							# Corta el endpoint sin conectar al espectador
        logger.info(f"Espectador conectado: {mask_email(user.email)} -> {camera_id}")
									# Registra la conexion del espectador
        success = await manager.connect(websocket, camera_id, user)	# Registra al espectador en el manager de la camara
        if success:							# Si el manager acepto, mantiene la conexion
            try:							# Abre un `try` para escuchar al espectador
                while True:						# Bucle mientras el espectador siga conectado
                    await websocket.receive_text()			# Espera mensajes del espectador (no se usan)
            except WebSocketDisconnect:					# Captura la desconexion normal del espectador
                logger.info(f"Espectador desconectado: {mask_email(user.email)} -> {camera_id}")
									# Registra la desconexion del espectador
                manager.disconnect(websocket, camera_id)		# Quita al espectador del manager de la camara

@router.post("/update-frame/{camera_id}")				# Decorador POST `/update-frame/{camera_id}`
async def update_frame_http(camera_id: str, request: Request, node_secret: str = Query(None)):
									# Define el endpoint HTTP con `camera_id`, request
									# y `node_secret`
    """Actualiza el frame de una camara. Solo acepta nodos ALPR autorizados."""
    peer = request.client.host if request.client else ""		# Obtiene la IP del cliente que envia el frame
    if not _is_trusted_alpr_node(peer, node_secret or ""):		# Valida IP y secreto del nodo ALPR
        raise HTTPException(status_code=403, detail="Nodo ALPR no autorizado")
									# Rechaza con 403 si el nodo no esta autorizado
    raw_body = await request.json()					# Lee el cuerpo JSON de la peticion
    if "image" in raw_body:						# Si el JSON trae una imagen, la reenvia
        await manager.broadcast_frame(camera_id, raw_body["image"])	# Publica el frame a los espectadores de la camara
    return {"status": "ok"}						# Confirma que el frame se proceso

@router.get("/video-feed/{camera_id}")					# Decorador GET `/video-feed/{camera_id}` (MJPEG)
async def video_feed_legacy(camera_id: str, staff: models.User = Depends(get_operational_user)):
									# Define el endpoint MJPEG para staff autenticado
    """Streaming de video MJPEG fallback."""
    if staff.rol != UserRole.ADMIN and staff.sucursal:			# Si no es ADMIN, limita a su sucursal
        branch_prefix = camera_id.split('_')[0]				# Extrae el prefijo de sucursal del id de camara
        # Comparar contra la sucursal normalizada (misma lógica que el WebSocket)
        if branch_prefix.upper() != normalize_system_name(staff.sucursal):
									# Compara el prefijo con la sucursal del staff
            raise HTTPException(status_code=403, detail="No tenés acceso a esta cámara")
									# Rechaza con 403 si la camara es de otra sede

    def gen_frames():							# Define el generador que produce los frames MJPEG
        while True:							# Bucle infinito de transmision al cliente
            frame_base64 = manager.last_frames.get(camera_id)		# Obtiene el ultimo frame conocido de la camara
            if frame_base64:						# Si hay un frame disponible, lo envia
                frame_bytes = base64.b64decode(frame_base64)		# Decodifica el frame de Base64 a bytes JPEG
                yield (b'--frame\r\n'					# Inicia el bloque MJPEG con el boundary `--frame`
                       b'Content-Type: image/jpeg\r\n'			# Declara el tipo de contenido del frame
                       b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
									# Calcula y declara el largo del frame JPEG
                       frame_bytes + b'\r\n')				# Agrega los bytes del frame y cierra el bloque
            time.sleep(0.1)						# Pausa 100 ms para no saturar el stream
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")
									# Devuelve el stream MJPEG con su boundary

def _user_from_token(token: str, db: Session):				# Define `_user_from_token` desde un JWT
    """Resuelve el usuario autenticado desde un JWT (query o header)."""
    payload = decode_access_token(token)				# Decodifica el token JWT
    if not payload:							# Si el token no es valido o expiro, rechaza
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
									# Responde 401 por token invalido o expirado
    user = UserRepository.get_active_by_email(db, payload.get("sub"))	# Busca el usuario activo por el email del token
    if not user:							# Si el usuario no existe o esta inactivo, rechaza
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
									# Responde 401 por usuario inexistente
    if str(user.rol) not in [UserRole.ADMIN.value, UserRole.LOCAL_ADMIN.value, UserRole.STAFF.value]:
									# Verifica rol ADMIN, LOCAL_ADMIN o STAFF
        raise HTTPException(status_code=403, detail="Acceso restringido a personal autorizado")
									# Responde 403 si el rol no esta autorizado
    return user								# Devuelve el usuario autenticado

@router.get("/capture/{log_id}")					# Decorador GET `/capture/{log_id}`
def get_capture(log_id: int, request: Request, token: str = Query(None), db: Session = Depends(get_db)):
									# Define el endpoint que sirve la imagen del log
    """Imagen capturada de un log. Acepta el token por query (para <img>) o por header Bearer."""
    staff = None							# Inicializa `staff` en None
    auth_header = request.headers.get("Authorization", "")		# Lee el header `Authorization` (vacio si no viene)
    if token:								# Si hay token en la query, autentica por esa via
        staff = _user_from_token(token, db)				# Resuelve el usuario desde el token de la query
    elif auth_header.lower().startswith("bearer "):			# Si el header es Bearer, autentica con ese token
        staff = _user_from_token(auth_header[7:], db)			# Extrae el token del header Bearer y lo valida
    else:								# Si no hay token ni header Bearer, rechaza
        raise HTTPException(status_code=401, detail="No autenticado")	# Responde 401 si falta autenticacion

    log = AccessRepository.get_by_id(db, log_id)			# Busca el log de acceso por su id
    if not log:								# Si el log no existe, responde 404
        raise HTTPException(status_code=404, detail="Log no encontrado")
									# Responde 404 por log inexistente
    if str(staff.rol) != UserRole.ADMIN.value and not same_branch(log.sucursal, staff.sucursal):
									# Un no-ADMIN solo ve logs de su sucursal
        raise HTTPException(status_code=403, detail="No tenés permisos")
									# Responde 403 si el log es de otra sucursal
    if log.imagen_path:							# Si el log tiene imagen, intenta servirla
        full_path = os.path.abspath(os.path.join(settings.IMAGE_DIR, log.imagen_path))
									# Construye la ruta absoluta dentro de `IMAGE_DIR`
        if os.path.exists(full_path):					# Si el archivo existe en disco, lo devuelve
            return FileResponse(full_path)				# Responde con la imagen del log
    return FileResponse(os.path.join("static", "images", "logo.png"))	# Si no hay imagen, devuelve el logo por defecto
