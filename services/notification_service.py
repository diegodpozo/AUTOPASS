import asyncio
import time
from sqlalchemy.orm import Session
from typing import Optional
from core.logger import get_logger

logger = get_logger("NotificationService")

class NotificationService:
    _occupancy_manager = None
    _loop = None
    _last_events = {}

    @classmethod
    def set_occupancy_manager(cls, manager):
        cls._occupancy_manager = manager

    @classmethod
    def set_event_loop(cls, loop):
        """Registra el event loop principal para permitir notificaciones desde hilos sincrónicos."""
        cls._loop = loop

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
        """DISPARA LA NOTIFICACION DE AFORO DE FORMA ASINCRONA.
        Si la llamada ocurre desde un hilo sincronico (FastAPI sync handler), se usa
        asyncio.run_coroutine_threadsafe para programar la tarea en el loop principal.
        """
        if not cls._occupancy_manager:
            return
        try:
            # Si hay un loop registrado (p.ej. el loop de Uvicorn), usalo con run_coroutine_threadsafe
            if cls._loop and cls._loop.is_running():
                try:
                    asyncio.run_coroutine_threadsafe(cls._occupancy_manager.broadcast_update(sucursal_norm=sucursal_norm, force_refresh=True), cls._loop)
                    logger.debug(f"Scheduled broadcast_update for sucursal={sucursal_norm}")
                except Exception as e:
                    logger.error(f"Error scheduling broadcast: {e}")
                return

            # Fallback: si hay un loop corriendo en este contexto (async), crear tarea
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                try:
                    loop.create_task(cls._occupancy_manager.broadcast_update(sucursal_norm=sucursal_norm, force_refresh=True))
                    logger.debug(f"Created task broadcast_update for sucursal={sucursal_norm} in current loop")
                except Exception as e:
                    logger.error(f"Error creating task in current loop: {e}")
            else:
                # No hay loop utilizable: ignorar (ejecuciones de script) o loguear
                logger.warning("No event loop available to notify occupancy change")
        except Exception as e:
            logger.error(f"Error al notificar: {e}")
