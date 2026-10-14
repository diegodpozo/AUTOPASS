from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, func
import models
from models.enums import PaymentStatus, ReservationStatus
from repositories.branch_repository import BranchRepository

#--- REPOSITORIO DE RESERVAS (ACCESO UN DATOS) ---

class ReservationRepository:
    @staticmethod
    def _org_branch_predicate(db: Session, organization_id):
        """PREDICADO SQL P/ RESERVAS DE TODAS LAS SEDES DE UNA ORGANIZACION (multi-tenant)."""
        from sqlalchemy import false
        ids = [
            r[0] for r in db.query(models.ParkingBranch.id).filter(
                models.ParkingBranch.organization_id == organization_id
            ).all()
        ]
        if not ids:
            return false()
        return models.Reservation.sucursal_id.in_(ids)

    @staticmethod
    def _sucursal_id_predicate(db: Session, sucursal_nombre: str, include_global: bool = False, organization_id=None):
        """PREDICADO SQL PARA FILTRAR RESERVAS POR SUCURSAL CON PRIORIDAD POR `sucursal_id` Y
        FALLBACK POR NOMBRE (registros legacy/test sin id). Con `include_global` tambien incluye
        reservas globales (sin sucursal), igual que la logica original por nombre.
        Con `organization_id` la sede debe pertenecer a esa empresa (evita cruzar organizaciones)."""
        from sqlalchemy import false
        suc_id = models.Reservation.sucursal_id
        name_col = models.Reservation.sucursal_nombre
        if not sucursal_nombre:
            return name_col.is_(None)
        branch_id = BranchRepository.get_id_by_name(db, sucursal_nombre, organization_id)
        if not branch_id and organization_id is not None:
            return false()
        if branch_id:
            if include_global:
                return or_(suc_id == branch_id, and_(suc_id.is_(None), or_(name_col == sucursal_nombre, name_col.is_(None))))
            return or_(suc_id == branch_id, and_(suc_id.is_(None), name_col == sucursal_nombre))
        if include_global:
            return or_(name_col == sucursal_nombre, name_col.is_(None))
        return name_col == sucursal_nombre

    @staticmethod
    def _otra_sucursal_predicate(db: Session, sucursal_nombre: str):
        """PREDICADO P/ RESERVAS DE OTRA SUCURSAL (excluye la sucursal target y las globales)."""
        suc_id = models.Reservation.sucursal_id
        name_col = models.Reservation.sucursal_nombre
        branch_id = BranchRepository.get_id_by_name(db, sucursal_nombre)
        if branch_id:
            return ~or_(suc_id == branch_id, name_col == sucursal_nombre)
        return name_col != sucursal_nombre

    @staticmethod
    def get_by_id(db: Session, res_id: int) -> models.Reservation:
        """BUSCA UNA RESERVA POR SU IDENTIFICADOR UNICO."""
        return db.query(models.Reservation).filter(models.Reservation.id == res_id).first()

    @staticmethod
    def get_by_user_and_id(db: Session, user_id: int, res_id: int) -> models.Reservation:
        """BUSCA UNA RESERVA ESPECIFICA VINCULADA A UN USUARIO DETERMINADO."""
        return db.query(models.Reservation).filter(
            and_(models.Reservation.id == res_id, models.Reservation.user_id == user_id)
        ).first()

    @staticmethod
    def get_past_reservations(db: Session, user_id: int, now_str: str):
        """OBTIENE LAS RESERVAS VENCIDAS QUE AUN NO HAN SIDO COMPLETADAS."""
        return db.query(models.Reservation).filter(
            models.Reservation.user_id == user_id,
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE.value, ReservationStatus.ACTIVA.value]),
            models.Reservation.fecha_fin < now_str
        ).all()

    @staticmethod
    def get_all_by_user(db: Session, user_id: int):
        """RETORNA EL HISTORIAL COMPLETO DE RESERVAS DE UN USUARIO."""
        return db.query(models.Reservation).filter(
            models.Reservation.user_id == user_id
        ).order_by(models.Reservation.id.desc()).all()

    @staticmethod
    def get_active_overlapping(db: Session, sucursal_nombre: str, desde_str: str, hasta_str: str, exclude_id: int = None):
        """RESERVAS ACTIVAS/PENDIENTES SOLAPADAS EN EL RANGO [desde, hasta) DE UNA SUCURSAL."""
        q = db.query(models.Reservation).filter(
            ReservationRepository._sucursal_id_predicate(db, sucursal_nombre),
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE.value, ReservationStatus.ACTIVA.value]),
            models.Reservation.estado_pago.in_([PaymentStatus.PENDIENTE.value, PaymentStatus.PAGADO.value]),
            models.Reservation.fecha_inicio < hasta_str,
            models.Reservation.fecha_fin > desde_str
        )
        if exclude_id:
            q = q.filter(models.Reservation.id != exclude_id)
        return q.all()

    @staticmethod
    def get_overlap_by_patente(db: Session, patente_norm: str, sucursal_nombre: str, desde_str: str, hasta_str: str, exclude_id: int = None):
        """RESERVA ACTIVA DE UNA PATENTE (normalizada) QUE SE SUPERPONE CON EL RANGO EN LA SUCURSAL."""
        q = db.query(models.Reservation).filter(
            func.replace(func.upper(models.Reservation.patente), ' ', '') == patente_norm,
            ReservationRepository._sucursal_id_predicate(db, sucursal_nombre),
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE.value, ReservationStatus.ACTIVA.value]),
            models.Reservation.estado_pago.in_([PaymentStatus.PENDIENTE.value, PaymentStatus.PAGADO.value]),
            models.Reservation.fecha_inicio < hasta_str,
            models.Reservation.fecha_fin > desde_str
        )
        if exclude_id is not None:
            q = q.filter(models.Reservation.id != exclude_id)
        return q.first()

    @staticmethod
    def get_user_overlap_other_branch(db: Session, user_id: int, sucursal_nombre: str, desde_str: str, hasta_str: str):
        """RESERVA ACTIVA/PENDIENTE DEL USUARIO QUE SE SUPERPONE CON EL RANGO EN OTRA SUCURSAL."""
        return db.query(models.Reservation).filter(
            models.Reservation.user_id == user_id,
            ReservationRepository._otra_sucursal_predicate(db, sucursal_nombre),
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE.value, ReservationStatus.ACTIVA.value]),
            models.Reservation.estado_pago.in_([PaymentStatus.PENDIENTE.value, PaymentStatus.PAGADO.value]),
            models.Reservation.fecha_inicio < hasta_str,
            models.Reservation.fecha_fin > desde_str
        ).first()

    @staticmethod
    def get_expired(db: Session, now_str: str):
        """RESERVAS PENDIENTES/ACTIVAS CUYA FECHA FIN YA PASO."""
        return db.query(models.Reservation).filter(
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE, ReservationStatus.ACTIVA]),
            models.Reservation.fecha_fin < now_str
        ).all()

    @staticmethod
    def get_paid_current_by_sucursal(db: Session, sucursal_nombre: str, now_str: str):
        """RESERVAS PAGADAS EN VIGENCIA (ACTIVAS O PENDIENTES CON SU HORARIO ACTUAL) DE UNA SUCURSAL."""
        return db.query(models.Reservation).filter(
            ReservationRepository._sucursal_id_predicate(db, sucursal_nombre),
            models.Reservation.estado_pago == PaymentStatus.PAGADO,
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE, ReservationStatus.ACTIVA]),
            models.Reservation.fecha_inicio <= now_str,
            models.Reservation.fecha_fin >= now_str
        ).all()

    @staticmethod
    def get_pending_reminders(db: Session, inicio_min: str, inicio_max: str):
        """RESERVAS VIGENTES SIN RECORDATORIO ENVIADO CUYO INICIO CAE DENTRO DE LA VENTANA DE AVISO."""
        return db.query(models.Reservation).filter(
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE, ReservationStatus.ACTIVA]),
            models.Reservation.fecha_inicio >= inicio_min,
            models.Reservation.fecha_inicio <= inicio_max,
            models.Reservation.recordatorio_confirmado == False
        ).options(selectinload(models.Reservation.user)).all()

    @staticmethod
    def get_pending_started(db: Session, now_str: str):
        """RESERVAS PENDIENTES CUYO HORARIO DE INICIO YA LLEGO (Y LA FECHA FIN AUN NO)."""
        return db.query(models.Reservation).filter(
            models.Reservation.estado_reserva == ReservationStatus.PENDIENTE,
            models.Reservation.fecha_inicio <= now_str,
            models.Reservation.fecha_fin >= now_str
        ).options(selectinload(models.Reservation.user)).all()

    @staticmethod
    def get_unpaid_overdue(db: Session, fecha_limite: str):
        """RESERVAS IMPAGAS VIGENTES CUYO INICIO SUPERO LA GRACIA DE CANCELACION AUTOMATICA."""
        return db.query(models.Reservation).filter(
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE, ReservationStatus.ACTIVA]),
            models.Reservation.estado_pago == PaymentStatus.PENDIENTE,
            models.Reservation.fecha_inicio < fecha_limite
        ).options(selectinload(models.Reservation.user)).all()

    @staticmethod
    def get_active_by_user(db: Session, user_id: int, now_str: str) -> models.Reservation:
        """RESERVA VIGENTE (PENDIENTE/ACTIVA Y FECHA FIN AUN NO VENCIDA) DE UN USUARIO."""
        return db.query(models.Reservation).filter(
            models.Reservation.user_id == user_id,
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE, ReservationStatus.ACTIVA]),
            models.Reservation.fecha_fin >= now_str
        ).first()

    @staticmethod
    def get_active_by_clean_patente(db: Session, patente_clean: str, now_str: str) -> models.Reservation:
        """RESERVA VIGENTE (PENDIENTE/ACTIVA Y FECHA FIN AUN NO VENCIDA) DE UNA PATENTE SIN ESPACIOS."""
        return db.query(models.Reservation).filter(
            func.replace(func.upper(models.Reservation.patente), ' ', '') == patente_clean,
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE, ReservationStatus.ACTIVA]),
            models.Reservation.fecha_fin >= now_str
        ).first()

    @staticmethod
    def get_active_by_sucursal(db: Session, sucursal_nombre: str, now_str: str) -> models.Reservation:
        """RESERVA VIGENTE (PENDIENTE/ACTIVA Y FECHA FIN AUN NO VENCIDA) EN UNA SUCURSAL."""
        return db.query(models.Reservation).filter(
            ReservationRepository._sucursal_id_predicate(db, sucursal_nombre),
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE, ReservationStatus.ACTIVA]),
            models.Reservation.fecha_fin >= now_str
        ).first()

    @staticmethod
    def get_by_ids(db: Session, res_ids) -> list:
        """OBTIENE LAS RESERVAS CUYOS IDENTIFICADORES ESTAN EN LA LISTA."""
        if not res_ids:
            return []
        return db.query(models.Reservation).filter(models.Reservation.id.in_(res_ids)).all()

    @staticmethod
    def get_by_id(db: Session, res_id: int, user_id: int = None):
        """BUSCA UNA RESERVA POR ID; si `user_id` se pasa, la filtra por dueño."""
        q = db.query(models.Reservation).filter(models.Reservation.id == res_id)
        if user_id is not None:
            q = q.filter(models.Reservation.user_id == user_id)
        return q.first()

    @staticmethod
    def get_active_in_range_by_normalized_patente(db: Session, patente_norm: str, now_str: str, sucursal: str) -> models.Reservation:
        """RESERVA PENDIENTE/ACTIVA DE UNA PATENTE NORMALIZADA VIGENTE EN EL RANGO EN LA SUCURSAL (o global)."""
        return db.query(models.Reservation).filter(
            func.replace(func.upper(models.Reservation.patente), ' ', '') == patente_norm,
            models.Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE.value, ReservationStatus.ACTIVA.value]),
            models.Reservation.fecha_inicio <= now_str,
            models.Reservation.fecha_fin >= now_str
        ).filter(
            ReservationRepository._sucursal_id_predicate(db, sucursal, include_global=True)
        ).first()

    @staticmethod
    def _filtered_base_query(db: Session, estado: str = None, sucursal: str = None, staff_sucursal: str = None, normalized_staff: bool = False, organization_id=None):
        q = db.query(models.Reservation)
        if estado:
            q = q.filter(models.Reservation.estado_reserva == estado)
        if staff_sucursal is not None:
            branch_id = BranchRepository.get_id_by_name(db, staff_sucursal)
            if branch_id:
                q = q.filter(models.Reservation.sucursal_id == branch_id)
            elif normalized_staff:
                staff_suc = staff_sucursal or ""
                norm_col = func.trim(func.replace(func.lower(models.Reservation.sucursal_nombre), 'autopass ', ''))
                norm_staff = staff_suc.lower().replace('autopass ', '').strip()
                q = q.filter((models.Reservation.sucursal_nombre == staff_suc) | (norm_col == norm_staff))
            else:
                q = q.filter(models.Reservation.sucursal_nombre == staff_sucursal)
        elif sucursal:
            q = q.filter(ReservationRepository._sucursal_id_predicate(db, sucursal, organization_id=organization_id))
        elif organization_id is not None:
            q = q.filter(ReservationRepository._org_branch_predicate(db, organization_id))
        return q

    @staticmethod
    def list_filtered(db: Session, estado: str = None, sucursal: str = None, staff_sucursal: str = None, organization_id=None):
        """RESERVAS FILTRADAS POR ESTADO Y SUCURSAL (staff_sucursal primero, luego sucursal), ordenadas por id desc."""
        return ReservationRepository._filtered_base_query(
            db, estado=estado, sucursal=sucursal, staff_sucursal=staff_sucursal, organization_id=organization_id
        ).options(selectinload(models.Reservation.user)).order_by(models.Reservation.id.desc()).all()

    @staticmethod
    def latest_id_and_count(db: Session, since_id: int = None, staff_sucursal: str = None, organization_id=None):
        """(id_maximo, count_reservas_con_id > since_id) con filtro de sucursal normalizado si staff_sucursal."""
        q = ReservationRepository._filtered_base_query(db, staff_sucursal=staff_sucursal, normalized_staff=True, organization_id=organization_id)
        latest_id = q.with_entities(func.max(models.Reservation.id)).scalar() or 0
        count = 0
        if since_id is not None:
            count = q.filter(models.Reservation.id > since_id).count()
        return latest_id, count

    @staticmethod
    def save(db: Session, reservation: models.Reservation):
        """PERSISTE UNA NUEVA RESERVA O CAMBIOS EN UNA EXISTENTE."""
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        return reservation
