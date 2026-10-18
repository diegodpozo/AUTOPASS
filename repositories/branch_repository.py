from sqlalchemy import or_, and_
from sqlalchemy.orm import Session, joinedload

import models
from repositories.scoping import scope_by_organization

#--- REPOSITORIO DE SUCURSALES / SEDES (PISOS Y AFORO) ---


class BranchRepository:
    @staticmethod
    def get_all(db: Session, organization_id=None) -> list:
        """OBTIENE TODAS LAS SUCURSALES (SEDES). SI SE INDICA ORGANIZACION, SOLO LAS SUYAS."""
        query = db.query(models.ParkingBranch)
        return scope_by_organization(query, models.ParkingBranch, organization_id).all()

    @staticmethod
    def get_by_name_like(db: Session, nombre: str, organization_id=None) -> models.ParkingBranch:
        """OBTIENE UNA SUCURSAL POR NOMBRE APROXIMADO (ILIKE), OPCIONALMENTE ACOTADA A UNA ORGANIZACION."""
        query = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre.ilike(f"%{nombre}%"))
        return scope_by_organization(query, models.ParkingBranch, organization_id).first()

    @staticmethod
    def get_floor_by_id(db: Session, floor_id: int) -> models.ParkingFloor:
        """OBTIENE UN PISO POR SU IDENTIFICADOR UNICO."""
        return db.query(models.ParkingFloor).filter(models.ParkingFloor.id == floor_id).first()

    @staticmethod
    def get_by_name_with_floors(db: Session, nombre: str, organization_id=None) -> models.ParkingBranch:
        """OBTIENE UNA SUCURSAL CON SUS PISOS CARGADOS (OPCIONALMENTE ACOTADA A UNA ORGANIZACION)."""
        query = (
            db.query(models.ParkingBranch)
            .options(joinedload(models.ParkingBranch.floors))
            .filter(models.ParkingBranch.nombre == nombre)
        )
        return scope_by_organization(query, models.ParkingBranch, organization_id).first()

    @staticmethod
    def get_by_name(db: Session, nombre: str, organization_id=None) -> models.ParkingBranch:
        """OBTIENE UNA SUCURSAL POR NOMBRE EXACTO (OPCIONALMENTE ACOTADA A UNA ORGANIZACION)."""
        query = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == nombre)
        return scope_by_organization(query, models.ParkingBranch, organization_id).first()

    @staticmethod
    def get_id_by_name(db: Session, nombre: str, organization_id=None):
        """DEVUELVE EL ID DE LA SUCURSAL POR NOMBRE EXACTO (None si no existe).

        Si se indica organizacion, acota la busqueda a esa empresa (necesario al
        permitir nombres repetidos entre organizaciones distintas). Sin
        organizacion, si el nombre es ambiguo (dos empresas con la misma sede)
        devuelve None en vez de elegir una al azar: no es atribuible a nadie."""
        if not nombre:
            return None
        query = db.query(models.ParkingBranch.id).filter(models.ParkingBranch.nombre == nombre)
        if organization_id is not None:
            query = query.filter(models.ParkingBranch.organization_id == organization_id)
        filas = query.limit(2).all()
        return filas[0][0] if len(filas) == 1 else None

    @staticmethod
    def resolve_id_by_name(db: Session, nombre: str, organization_id=None):
        """RESUELVE UNA SEDE POR NOMBRE NORMALIZADO SIN CRUZAR ORGANIZACIONES."""
        from core.normalize import normalize_branch_name
        if not nombre:
            return None
        exact = BranchRepository.get_id_by_name(db, nombre, organization_id)
        if exact is not None:
            return exact
        clave = normalize_branch_name(nombre)
        query = db.query(models.ParkingBranch)
        if organization_id is not None:
            query = query.filter(models.ParkingBranch.organization_id == organization_id)
        matches = [b for b in query.all() if normalize_branch_name(b.nombre) == clave]
        return matches[0].id if len(matches) == 1 else None

    def get_first_active(db: Session, organization_id=None) -> models.ParkingBranch:
        """OBTIENE LA PRIMERA SUCURSAL ACTIVA (FALLBACK SIN NOMBRE ESPECIFICADO).
        Con `organization_id` se acota a las sedes de esa empresa."""
        query = db.query(models.ParkingBranch).filter(models.ParkingBranch.activa == True)
        return scope_by_organization(query, models.ParkingBranch, organization_id).first()

    @staticmethod
    def get_all_active(db: Session, organization_id=None) -> list:
        """OBTIENE TODAS LAS SUCURSALES ACTIVAS (opcionalmente de una organizacion)."""
        query = db.query(models.ParkingBranch).filter(models.ParkingBranch.activa == True)
        return scope_by_organization(query, models.ParkingBranch, organization_id).all()

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
    def get_aforo_by_branch_id(db: Session, branch_id) -> models.ParkingAforo:
        """OBTIENE EL AFORO DE UNA SUCURSAL POR SU ID (evita la ambiguedad del nombre)."""
        return db.query(models.ParkingAforo).filter(
            models.ParkingAforo.sucursal_id == branch_id
        ).first()

    @staticmethod
    def get_all_aforos(db: Session) -> list:
        """OBTIENE TODOS LOS REGISTROS DE AFORO/CAPACIDADES."""
        return db.query(models.ParkingAforo).all()

    @staticmethod
    def get_other_by_name(db: Session, nombre: str, branch_id: int, organization_id=None) -> models.ParkingBranch:
        """OBTIENE UNA SUCURSAL CON ESE NOMBRE, DISTINTA A LA INDICADA (OPCIONALMENTE POR ORGANIZACION)."""
        query = db.query(models.ParkingBranch).filter(
            models.ParkingBranch.nombre == nombre,
            models.ParkingBranch.id != branch_id
        )
        return scope_by_organization(query, models.ParkingBranch, organization_id).first()
