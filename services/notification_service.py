import asyncio
import time
from sqlalchemy.orm import Session
from typing import Optional, Callable
from core.logger import get_logger

logger = get_logger("NotificationService")

class NotificationService:
    _occupancy_manager = None
    _loop = None
    _last_events = {}
    _pending_exits = {}
    _PENDING_EXIT_TTL = 120.0

    @classmethod
    def set_occupancy_manager(cls, manager):
        cls._occupancy_manager = manager

    @classmethod
    def set_event_loop(cls, loop):
        """Registra el event loop principal para permitir notificaciones desde hilos sincrónicos."""
        cls._loop = loop

    @classmethod
    def _dispatch(cls, coro_builder: Callable):
        """Programa una corrutina del manager en el loop principal.
        Soporta llamadas desde hilos sincrónicos (handlers sync de FastAPI) usando
        asyncio.run_coroutine_threadsafe sobre el loop de Uvicorn."""
        if not cls._occupancy_manager:
            return
        try:
            if cls._loop and cls._loop.is_running():
                try:
                    asyncio.run_coroutine_threadsafe(coro_builder(), cls._loop)
                    logger.debug("Scheduled notification on main loop")
                except Exception as e:
                    logger.error(f"Error scheduling notification: {e}")
                return

            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                try:
                    loop.create_task(coro_builder())
                except Exception as e:
                    logger.error(f"Error creating task in current loop: {e}")
            else:
                logger.warning("No event loop available to dispatch notification")
        except Exception as e:
            logger.error(f"Error al notificar: {e}")

    @classmethod
    def set_last_event(cls, sucursal_norm: str, event_type: str, plate: str, message: str, status: str = "ok"):
        """Almacena el último evento de detección para una sucursal."""
        cls._last_events[sucursal_norm] = {
            "type": event_type,
            "plate": plate,
            "message": message,
            "status": status,
            "timestamp": time.time()
        }

    @classmethod
    def get_last_event(cls, sucursal_norm: str) -> Optional[dict]:
        """Obtiene el último evento de detección para una sucursal."""
        ev = cls._last_events.get(sucursal_norm)
        if ev and (time.time() - ev["timestamp"]) < 10:
            return ev
        return None

    @classmethod
    def notify_occupancy_change(cls, db: Session = None, sucursal_norm: Optional[str] = None):
        """DISPARA LA NOTIFICACION DE AFORO DE FORMA ASINCRONA."""
        cls._dispatch(lambda: cls._occupancy_manager.broadcast_update(sucursal_norm=sucursal_norm, force_refresh=True))

    @classmethod
    def set_pending_exit(cls, sucursal_norm: str, payload: dict):
        """Registra una salida impaga detectada por ALPR para que el dashboard la muestre."""
        cls._pending_exits[sucursal_norm] = {"payload": payload, "timestamp": time.time()}

    @classmethod
    def get_pending_exit(cls, sucursal_norm: str) -> Optional[dict]:
        """Devuelve la salida impaga reciente de una sucursal (None si expiró)."""
        ev = cls._pending_exits.get(sucursal_norm)
        if ev and (time.time() - ev["timestamp"]) < cls._PENDING_EXIT_TTL:
            return ev["payload"]
        return None

    @classmethod
    def clear_pending_exit(cls, sucursal_norm: str):
        """Descarta la salida impaga pendiente de una sucursal (tras cobrarla en caja)."""
        cls._pending_exits.pop(sucursal_norm, None)

    @classmethod
    def notify_pending_exit(cls, sucursal_norm: str, payload: dict):
        """Avisa al dashboard que un vehiculo intento salir con deuda: abre el popup de cobro."""
        cls.set_pending_exit(sucursal_norm, payload)
        event = {"type": "PENDING_EXIT", "data": payload}
        cls._dispatch(lambda: cls._occupancy_manager.broadcast_event(sucursal_norm, event))
