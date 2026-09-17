from sqlalchemy.orm import Session, joinedload

import models

#--- REPOSITORIO DE SUCURSALES / SEDES (PISOS Y AFORO) ---


class BranchRepository:
    @staticmethod
    def get_by_name_with_floors(db: Session, nombre: str) -> models.ParkingBranch:
        """OBTIENE UNA SUCURSAL CON SUS PISOS CARGADOS."""
        return (
            db.query(models.ParkingBranch)
            .options(joinedload(models.ParkingBranch.floors))
            .filter(models.ParkingBranch.nombre == nombre)
            .first()
        )

    @staticmethod
    def get_by_name(db: Session, nombre: str) -> models.ParkingBranch:
        """OBTIENE UNA SUCURSAL POR NOMBRE EXACTO."""
        return db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == nombre).first()

    @staticmethod
    def get_aforo_by_sucursal(db: Session, sucursal: str) -> models.ParkingAforo:
        """OBTIENE EL AFORO (CAPACIDADES) DE UNA SUCURSAL."""
        return db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()