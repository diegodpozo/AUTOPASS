from sqlalchemy.orm import Session

import models
from models.enums import UserRole

#--- REPOSITORIO DE SISTEMA (RESET / DATOS OPERATIVOS) ---


class SystemRepository:
    @staticmethod
    def reset_all_data(db: Session) -> None:
        """BORRA TODOS LOS DATOS OPERATIVOS Y CLIENTES REGISTRADOS (PARA REINICIO DEL SISTEMA)."""
        db.query(models.AccessLog).delete()
        db.query(models.ParkingAforo).delete()
        db.query(models.Reservation).delete()
        db.query(models.Vehicle).delete()
        db.query(models.User).filter(models.User.rol == UserRole.USER.value).delete()
        db.commit()