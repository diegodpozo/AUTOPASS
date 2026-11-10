"""
Rutas de WebSocket y control de Hardware para AUTOPASS.
Permite conectar puentes remotos (como la laptop con Arduino Uno conectada por USB)
a través de Cloudflare Tunnel o Tailscale.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from core.logger import get_logger
from core.config import settings
from core.alpr_security import is_trusted_alpr_node
from core.security import decode_access_token, is_operational_role
from core.database import get_db
from repositories.user_repository import UserRepository
from services.hardware_service import HardwareService

logger = get_logger("HardwareWS")

router = APIRouter()


@router.websocket("/ws/hardware")
async def websocket_hardware_endpoint(
    websocket: WebSocket,
    secret: str = Query(None, alias="node_secret"),
    token: str = Query(None)
):
    """
    Endpoint WebSocket para puentes de hardware (ej: laptop con Arduino conectada via Cloudflare/Tailscale).
    Autentica por secret (ALPR_NODE_SECRET / SECRET_KEY / red privada) o por token JWT de usuario operativo.
    """
    user = None
    if token:
        db = None
        try:
            payload = decode_access_token(token)
            db = next(get_db())
            user = UserRepository.get_active_by_email(db, payload.get("sub"))
        except Exception:
            pass
        finally:
            if db:
                try:
                    db.close()
                except Exception:
                    pass

    # Si no es usuario operativo autenticado por JWT, verificar secreto o red privada
    if not (user and is_operational_role(user.rol)):
        peer = websocket.client.host if websocket.client else ""
        node_sec = secret or websocket.query_params.get("secret") or websocket.query_params.get("node_secret") or ""
        
        trusted = is_trusted_alpr_node(peer, node_sec)
        # Permitir también SECRET_KEY como fallback de administración
        if not trusted and settings.SECRET_KEY and node_sec == settings.SECRET_KEY:
            trusted = True

        if not trusted:
            logger.warning(f"[HARDWARE WS] Conexión de hardware rechazada desde {peer} (secreto o token inválido)")
            await websocket.close(code=4403)
            return

    await websocket.accept()
    await HardwareService.register_ws(websocket)
    try:
        await websocket.send_json({"type": "info", "message": "AUTOPASS Hardware Bridge conectado"})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"[HARDWARE WS] Excepción en loop de hardware: {e}")
    finally:
        await HardwareService.unregister_ws(websocket)
