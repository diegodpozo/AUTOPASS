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
        """DISPARA LA NOTIFICACION DE AFORO DE FORMA ASINCRONA."""
        if cls._occupancy_manager:
            try:
                # OBTENEMOS EL LOOP ACTUAL PARA PROGRAMAR LA TAREA
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(cls._occupancy_manager.broadcast_update(db, sucursal_norm))
                else:
                    #SI NO HAY LOOP CORRIENDO (PRUEBA O SCRIPT), IGNORAMOS O CORREMOS UNO
                    pass
            except Exception as e:
                print(f"[NotificationService] Error al notificar: {e}")
