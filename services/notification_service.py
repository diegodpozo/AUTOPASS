import asyncio
from sqlalchemy.orm import Session
from typing import Optional

class NotificationService:
    _occupancy_manager = None
    _loop = None

    @classmethod
    def set_occupancy_manager(cls, manager):
        cls._occupancy_manager = manager

    @classmethod
    def set_event_loop(cls, loop):
        """Registra el event loop principal para permitir notificaciones desde hilos sincrónicos."""
        cls._loop = loop

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
                    asyncio.run_coroutine_threadsafe(cls._occupancy_manager.broadcast_update(sucursal_norm=sucursal_norm), cls._loop)
                    print(f"[NotificationService] Scheduled broadcast_update for sucursal={sucursal_norm}")
                except Exception as e:
                    print(f"[NotificationService] Error scheduling broadcast: {e}")
                return

            # Fallback: si hay un loop corriendo en este contexto (async), crear tarea
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                try:
                    loop.create_task(cls._occupancy_manager.broadcast_update(sucursal_norm=sucursal_norm))
                    print(f"[NotificationService] Created task broadcast_update for sucursal={sucursal_norm} in current loop")
                except Exception as e:
                    print(f"[NotificationService] Error creating task in current loop: {e}")
            else:
                # No hay loop utilizable: ignorar (ejecuciones de script) o loguear
                print("[NotificationService] No event loop available to notify occupancy change")
        except Exception as e:
            print(f"[NotificationService] Error al notificar: {e}")
