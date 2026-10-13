from sqlalchemy import or_, and_
from sqlalchemy.orm import Session, joinedload

import models

#--- REPOSITORIO DE SUCURSALES / SEDES (PISOS Y AFORO) ---


class BranchRepository:
    @staticmethod
    def get_all(db: Session) -> list:
        """OBTIENE TODAS LAS SUCURSALES (SEDES)."""
        return db.query(models.ParkingBranch).all()

    @staticmethod
    def get_by_name_like(db: Session, nombre: str) -> models.ParkingBranch:
        """OBTIENE UNA SUCURSAL POR NOMBRE APROXIMADO (ILIKE)."""
        return db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre.ilike(f"%{nombre}%")).first()

    @staticmethod
    def get_floor_by_id(db: Session, floor_id: int) -> models.ParkingFloor:
        """OBTIENE UN PISO POR SU IDENTIFICADOR UNICO."""
        return db.query(models.ParkingFloor).filter(models.ParkingFloor.id == floor_id).first()

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
    def get_id_by_name(db: Session, nombre: str):
        """DEVUELVE EL ID DE LA SUCURSAL POR NOMBRE EXACTO (None si no existe)."""
        if not nombre:
            return None
        return db.query(models.ParkingBranch.id).filter(models.ParkingBranch.nombre == nombre).scalar()

    @staticmethod
    def get_first_active(db: Session) -> models.ParkingBranch:
        """OBTIENE LA PRIMERA SUCURSAL ACTIVA (FALLBACK SIN NOMBRE ESPECIFICADO)."""
        return db.query(models.ParkingBranch).filter(models.ParkingBranch.activa == True).first()

    @staticmethod
    def get_all_active(db: Session) -> list:
        """OBTIENE TODAS LAS SUCURSALES ACTIVAS."""
        return db.query(models.ParkingBranch).filter(models.ParkingBranch.activa == True).all()

    @staticmethod
    def get_all_active_with_location(db: Session) -> list:
        """OBTIENE SUCURSALES ACTIVAS CON SUS PISOS (JOINEDLOAD), SOLO LAS QUE TIENEN COORDENADAS."""
        return (
            db.query(models.ParkingBranch)
            .options(joinedload(models.ParkingBranch.floors))
            .filter(
                models.ParkingBranch.activa == True,
                models.ParkingBranch.latitude != None,
                models.ParkingBranch.longitude != None
            )
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, branch_id: int) -> models.ParkingBranch:
        """OBTIENE UNA SUCURSAL POR SU IDENTIFICADOR UNICO."""
        return db.query(models.ParkingBranch).filter(models.ParkingBranch.id == branch_id).first()

    @staticmethod
    def get_aforo_by_sucursal(db: Session, sucursal: str) -> models.ParkingAforo:
        """OBTIENE EL AFORO (CAPACIDADES) DE UNA SUCURSAL POR `sucursal_id` (None = global)."""
        branch_id = BranchRepository.get_id_by_name(db, sucursal) if sucursal else None
        return db.query(models.ParkingAforo).filter(
            models.ParkingAforo.sucursal_id == branch_id
        ).first()

    @staticmethod
    def get_all_aforos(db: Session) -> list:
        """OBTIENE TODOS LOS REGISTROS DE AFORO/CAPACIDADES."""
        return db.query(models.ParkingAforo).all()

    @staticmethod
    def get_other_by_name(db: Session, nombre: str, branch_id: int) -> models.ParkingBranch:
        """OBTIENE UNA SUCURSAL CON ESE NOMBRE, DISTINTA A LA INDICADA."""
        return db.query(models.ParkingBranch).filter(
            models.ParkingBranch.nombre == nombre,
            models.ParkingBranch.id != branch_id
        ).first()