from sqlalchemy import func
from sqlalchemy.orm import Session

import models

#--- REPOSITORIO DE CÁMARAS (GESTIÓN DE HARDWARE) ---


class CameraRepository:
    @staticmethod
    def get_all(db: Session) -> list:
        """OBTIENE TODAS LAS CÁMARAS REGISTRADAS ORDENADAS POR POSICIÓN MANUAL.

        `orden` NULL (sin ordenar) va al final; el id desempata y da un orden
        estable para las cámaras que comparten posición.
        """
        return (
            db.query(models.ParkingCamera)
            .order_by(func.coalesce(models.ParkingCamera.orden, 10 ** 9),
                      models.ParkingCamera.id)
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, camera_id: int) -> models.ParkingCamera:
        """OBTIENE UNA CÁMARA POR SU IDENTIFICADOR UNICO."""
        return db.query(models.ParkingCamera).filter(models.ParkingCamera.id == camera_id).first()