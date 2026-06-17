import asyncio
from sqlalchemy.orm import Session
from typing import Optional

class NotificationService:
    _occupancy_manager = None

    @classmethod
    def set_occupancy_manager(cls, manager):
        cls._occupancy_manager = manager

    @classmethod
    def notify_occupancy_change(cls, db: Session, sucursal_norm: Optional[str] = None):
        """Dispara la notificación de aforo de forma asíncrona."""
        if cls._occupancy_manager:
            try:
                # Obtenemos el loop actual para programar la tarea
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(cls._occupancy_manager.broadcast_update(db, sucursal_norm))
                else:
                    # Si no hay loop corriendo (test o script), ignoramos o corremos uno
                    pass
            except Exception as e:
                print(f"[NotificationService] Error al notificar: {e}")
