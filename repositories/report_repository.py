from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, union_all, literal_column, or_, and_

import models
from models.enums import ReservationStatus, PaymentStatus, AccessEventType

#--- REPOSITORIO DE REPORTES E INTELIGENCIA DE NEGOCIO (CONSULTAS AGREGADAS) ---

CASH_METHODS = ("CAJA", "Caja", "Efectivo")

PAYMENT_METHOD_VARIANTS = {
    "CAJA": CASH_METHODS,
    "DIGITAL": ("DIGITAL", "SALDO", "Billetera", "BILLETERA", "BILLETERA AUTOPASS"),
    "MERCADOPAGO": ("MERCADOPAGO", "MERCADO PAGO", "Mercado Pago"),
    "TRANSFERENCIA": ("TRANSFERENCIA", "Transferencia"),
    "TARJETA": ("TARJETA", "Tarjeta"),
    "OTRO": ("OTRO", "Otro"),
}


def _canonical_method(m):
    """NORMALIZA UN METODO GUARDADO EN BD AL METODO CANONICO (None legacy = DIGITAL)."""
    if m is None:
        return "DIGITAL"
    for canon, variants in PAYMENT_METHOD_VARIANTS.items():
        if m in variants:
            return canon
    norm = str(m).upper().replace(" ", "")
    for canon, variants in PAYMENT_METHOD_VARIANTS.items():
        if norm in tuple(v.upper().replace(" ", "") for v in variants):
            return canon
    return "DIGITAL"


def _es_reembolso_parcial(col_estado, col_reembolsado):
    """REEMBOLSOS: RESERVAS REEMBOLSADAS COMPLETAS O PAGADAS CON REEMBOLSO PARCIAL ACUMULADO."""
    return or_(
        col_estado == PaymentStatus.REEMBOLSADO,
        and_(col_estado == PaymentStatus.PAGADO, col_reembolsado > 0)
    )


def _payment_method_filter(column, method: str):
    """FILTRO SQL POR METODO DE PAGO CANONICO (all = sin filtro). NULL CUENTA COMO DIGITAL."""
    if method == "all" or not method:
        return None
    if method == "DIGITAL":
        return or_(column.is_(None), column.notin_(CASH_METHODS))
    variants = PAYMENT_METHOD_VARIANTS.get(method)
    if variants:
        return column.in_(variants)
    return column == method


def _branch_filter(column, sucursal: str):
    """FILTRO SQL DE AISLAMIENTO POR SUCURSAL (SUBCADENA 'AUTOPASS ' NORMALIZADA)."""
    if not sucursal:
        return None
    target_name = sucursal.replace('AUTOPASS ', '').strip()
    return column.like(f"%{target_name}%")


class ReportRepository:
    @staticmethod
    def paid_logs_aggregate(db: Session, sucursal=None, vehicle_type="all",
                            start_date=None, end_date=None, method="all"):
        """RECAUDACION DE ESTADIAS ALPR: (suma, cantidad) DE PAGOS CONFIRMADOS CON COSTO MAYOR A 0."""
        q = db.query(
            func.sum(models.AccessLog.costo_estadia),
            func.count(models.AccessLog.id)
        ).filter(models.AccessLog.pago_confirmado == True, models.AccessLog.costo_estadia > 0)

        filtro = _payment_method_filter(models.AccessLog.metodo_pago, method)
        if filtro is not None:
            q = q.filter(filtro)

        if vehicle_type != "all":
            q = q.filter(models.AccessLog.tipo_vehiculo == vehicle_type)

        if sucursal:
            q = q.filter(_branch_filter(models.AccessLog.sucursal, sucursal))

        if start_date:
            q = q.filter((models.AccessLog.fecha_pago >= start_date) |
                           ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora >= start_date)))
        if end_date:
            q = q.filter((models.AccessLog.fecha_pago <= end_date) |
                           ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora <= end_date)))
        return q.first()

    @staticmethod
    def paid_reservations_aggregate(db: Session, sucursal=None, vehicle_type="all",
                                    start_date=None, end_date=None, method="all") -> tuple:
        """RECAUDACION DE RESERVAS (bruto, cantidad): (suma monto_total, count) DE PAGADAS/REEMBOLSADAS."""
        q = db.query(
            func.sum(models.Reservation.monto_total),
            func.count(models.Reservation.id)
        ).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)

        q = q.filter(models.Reservation.estado_pago.in_([PaymentStatus.PAGADO, PaymentStatus.REEMBOLSADO]))

        if vehicle_type != "all":
            q = q.filter(models.Vehicle.tipo == vehicle_type)

        if sucursal:
            q = q.filter(_branch_filter(models.Reservation.sucursal_nombre, sucursal))

        if start_date:
            q = q.filter((models.Reservation.fecha_pago >= start_date) |
                           ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
        if end_date:
            q = q.filter((models.Reservation.fecha_pago <= end_date) |
                           ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))

        filtro = _payment_method_filter(models.Reservation.metodo_pago, method)
        if filtro is not None:
            q = q.filter(filtro)

        return q.first()

    @staticmethod
    def refunds_total(db: Session, sucursal=None, vehicle_type="all",
                      start_date=None, end_date=None, method="all") -> float:
        """SUMA DE REEMBOLSOS (parciales o completos) APLICANDO LOS MISMOS FILTROS DE RECAUDACION."""
        q = db.query(func.sum(models.Reservation.monto_reembolsado)).join(
            models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True
        )
        q = q.filter(_es_reembolso_parcial(models.Reservation.estado_pago, models.Reservation.monto_reembolsado))

        if vehicle_type != "all":
            q = q.filter(models.Vehicle.tipo == vehicle_type)

        if sucursal:
            q = q.filter(_branch_filter(models.Reservation.sucursal_nombre, sucursal))

        if start_date:
            q = q.filter((models.Reservation.fecha_pago >= start_date) |
                           ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
        if end_date:
            q = q.filter((models.Reservation.fecha_pago <= end_date) |
                           ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))

        filtro = _payment_method_filter(models.Reservation.metodo_pago, method)
        if filtro is not None:
            q = q.filter(filtro)

        return q.scalar()

    @staticmethod
    def cancelled_reservations(db: Session, sucursal=None, vehicle_type="all",
                               start_date=None, end_date=None) -> list:
        """RESERVAS CANCELADAS (para tasa de cancelacion e ingresos por incumplimiento)."""
        q = db.query(models.Reservation).join(
            models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True
        ).filter(models.Reservation.estado_reserva == ReservationStatus.CANCELADA)

        if vehicle_type != "all":
            q = q.filter(models.Vehicle.tipo == vehicle_type)

        if sucursal:
            q = q.filter(_branch_filter(models.Reservation.sucursal_nombre, sucursal))

        if start_date:
            q = q.filter(models.Reservation.fecha_inicio >= start_date)
        if end_date:
            q = q.filter(models.Reservation.fecha_inicio <= end_date)

        return q.all()

    @staticmethod
    def total_reservations_count(db: Session, sucursal=None, vehicle_type="all",
                                 start_date=None, end_date=None) -> int:
        """TOTAL DE RESERVAS (denominador de la tasa de cancelacion)."""
        q = db.query(func.count(models.Reservation.id)).join(
            models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True
        )

        if vehicle_type != "all":
            q = q.filter(models.Vehicle.tipo == vehicle_type)

        if sucursal:
            q = q.filter(_branch_filter(models.Reservation.sucursal_nombre, sucursal))

        if start_date:
            q = q.filter(models.Reservation.fecha_inicio >= start_date)
        if end_date:
            q = q.filter(models.Reservation.fecha_inicio <= end_date)

        return q.scalar() or 0

    @staticmethod
    def unpaid_entries_without_exit(db: Session, sucursal=None, vehicle_type="all") -> list:
        """ENTRADAS SIN SALIDA POSTERIOR Y SIN PAGO CONFIRMADO (AUTOS FISICAMENTE PRESENTES, DEUDA PROYECTADA)."""
        Log = models.AccessLog
        Salida = aliased(models.AccessLog)
        q = db.query(Log).filter(
            Log.tipo_evento == AccessEventType.ENTRADA,
            Log.pago_confirmado == False,
            ~db.query(Salida.id).filter(
                Salida.patente_detectada == Log.patente_detectada,
                Salida.tipo_evento == AccessEventType.SALIDA,
                Salida.fecha_hora > Log.fecha_hora,
                Salida.sucursal == Log.sucursal
            ).exists()
        )

        if vehicle_type != "all":
            q = q.filter(Log.tipo_vehiculo == vehicle_type)

        if sucursal:
            q = q.filter(_branch_filter(Log.sucursal, sucursal))

        return q.all()

    @staticmethod
    def grouped_logs_by_method(db: Session, sucursal=None, vehicle_type="all",
                               start_date=None, end_date=None) -> list:
        """DESGLOSE DE ESTADIAS POR METODO DE PAGO: (metodo_pago, suma, cantidad)."""
        q = db.query(
            models.AccessLog.metodo_pago,
            func.sum(models.AccessLog.costo_estadia),
            func.count(models.AccessLog.id)
        ).filter(models.AccessLog.pago_confirmado == True, models.AccessLog.costo_estadia > 0)
        if vehicle_type != "all":
            q = q.filter(models.AccessLog.tipo_vehiculo == vehicle_type)
        if sucursal:
            q = q.filter(_branch_filter(models.AccessLog.sucursal, sucursal))
        if start_date:
            q = q.filter((models.AccessLog.fecha_pago >= start_date) |
                           ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora >= start_date)))
        if end_date:
            q = q.filter((models.AccessLog.fecha_pago <= end_date) |
                           ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora <= end_date)))
        return q.group_by(models.AccessLog.metodo_pago).all()

    @staticmethod
    def grouped_reservations_by_method(db: Session, sucursal=None, vehicle_type="all",
                                       start_date=None, end_date=None) -> list:
        """DESGLOSE DE RESERVAS PAGADAS/REEMBOLSADAS POR METODO: (metodo_pago, suma, cantidad)."""
        q = db.query(
            models.Reservation.metodo_pago,
            func.sum(models.Reservation.monto_total),
            func.count(models.Reservation.id)
        ).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)
        q = q.filter(models.Reservation.estado_pago.in_([PaymentStatus.PAGADO, PaymentStatus.REEMBOLSADO]))
        if vehicle_type != "all":
            q = q.filter(models.Vehicle.tipo == vehicle_type)
        if sucursal:
            q = q.filter(_branch_filter(models.Reservation.sucursal_nombre, sucursal))
        if start_date:
            q = q.filter((models.Reservation.fecha_pago >= start_date) |
                           ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
        if end_date:
            q = q.filter((models.Reservation.fecha_pago <= end_date) |
                           ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))
        return q.group_by(models.Reservation.metodo_pago).all()

    @staticmethod
    def grouped_refunds_by_method(db: Session, sucursal=None, vehicle_type="all",
                                  start_date=None, end_date=None) -> list:
        """DESGLOSE DE REEMBOLSOS POR METODO: (metodo_pago, suma reembolsada, cantidad)."""
        q = db.query(
            models.Reservation.metodo_pago,
            func.sum(func.coalesce(models.Reservation.monto_reembolsado, 0.0)),
            func.count(models.Reservation.id)
        ).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)
        q = q.filter(_es_reembolso_parcial(models.Reservation.estado_pago, models.Reservation.monto_reembolsado))
        if vehicle_type != "all":
            q = q.filter(models.Vehicle.tipo == vehicle_type)
        if sucursal:
            q = q.filter(_branch_filter(models.Reservation.sucursal_nombre, sucursal))
        if start_date:
            q = q.filter((models.Reservation.fecha_pago >= start_date) |
                           ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
        if end_date:
            q = q.filter((models.Reservation.fecha_pago <= end_date) |
                           ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))
        return q.group_by(models.Reservation.metodo_pago).all()

    @staticmethod
    def payment_history(db: Session, sucursal=None, vehicle_type="all",
                        start_date=None, end_date=None, method="all",
                        offset: int = 0, limit: int = 20) -> list:
        """HISTORIAL UNIFICADO DE PAGOS (ESTADIAS + RESERVAS + REEMBOLSOS) PAGINADO."""
        # 1. ESTADIAS
        q_logs = db.query(
            literal_column("'L' || CAST(access_logs.id AS TEXT)").label("id"),
            func.coalesce(models.AccessLog.fecha_pago, models.AccessLog.fecha_hora).label("fecha"),
            models.AccessLog.patente_detectada.label("patente"),
            models.AccessLog.costo_estadia.label("monto"),
            literal_column("'Estadía'").label("tipo"),
            models.AccessLog.metodo_pago.label("metodo")
        ).filter(models.AccessLog.pago_confirmado == True, models.AccessLog.costo_estadia > 0)

        if vehicle_type != "all":
            q_logs = q_logs.filter(models.AccessLog.tipo_vehiculo == vehicle_type)
        filtro_logs = _payment_method_filter(models.AccessLog.metodo_pago, method)
        if filtro_logs is not None:
            q_logs = q_logs.filter(filtro_logs)
        if sucursal:
            q_logs = q_logs.filter(_branch_filter(models.AccessLog.sucursal, sucursal))
        if start_date:
            q_logs = q_logs.filter((models.AccessLog.fecha_pago >= start_date) |
                                   ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora >= start_date)))
        if end_date:
            q_logs = q_logs.filter((models.AccessLog.fecha_pago <= end_date) |
                                   ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora <= end_date)))

        # 2. RESERVAS
        q_res = db.query(
            literal_column("'R' || CAST(reservations.id AS TEXT)").label("id"),
            func.coalesce(models.Reservation.fecha_pago, models.Reservation.fecha_inicio).label("fecha"),
            models.Reservation.patente.label("patente"),
            models.Reservation.monto_total.label("monto"),
            literal_column("'Reserva'").label("tipo"),
            func.coalesce(models.Reservation.metodo_pago, "DIGITAL").label("metodo")
        ).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)

        q_res = q_res.filter(models.Reservation.estado_pago == PaymentStatus.PAGADO)
        if vehicle_type != "all":
            q_res = q_res.filter(models.Vehicle.tipo == vehicle_type)
        if sucursal:
            q_res = q_res.filter(_branch_filter(models.Reservation.sucursal_nombre, sucursal))
        if start_date:
            q_res = q_res.filter((models.Reservation.fecha_pago >= start_date) |
                                 ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
        if end_date:
            q_res = q_res.filter((models.Reservation.fecha_pago <= end_date) |
                                 ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))
        filtro_res = _payment_method_filter(models.Reservation.metodo_pago, method)
        if filtro_res is not None:
            q_res = q_res.filter(filtro_res)

        # 3. REEMBOLSOS
        q_refunds = db.query(
            literal_column("'REF' || CAST(reservations.id AS TEXT)").label("id"),
            func.coalesce(models.Reservation.fecha_pago, models.Reservation.fecha_inicio).label("fecha"),
            models.Reservation.patente.label("patente"),
            (models.Reservation.monto_reembolsado * -1).label("monto"),
            literal_column("'Reembolso'").label("tipo"),
            func.coalesce(models.Reservation.metodo_pago, "DIGITAL").label("metodo")
        ).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)

        q_refunds = q_refunds.filter(_es_reembolso_parcial(models.Reservation.estado_pago, models.Reservation.monto_reembolsado))
        if vehicle_type != "all":
            q_refunds = q_refunds.filter(models.Vehicle.tipo == vehicle_type)
        if sucursal:
            q_refunds = q_refunds.filter(_branch_filter(models.Reservation.sucursal_nombre, sucursal))
        if start_date:
            q_refunds = q_refunds.filter((models.Reservation.fecha_pago >= start_date) |
                                         ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
        if end_date:
            q_refunds = q_refunds.filter((models.Reservation.fecha_pago <= end_date) |
                                         ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))
        filtro_ref = _payment_method_filter(models.Reservation.metodo_pago, method)
        if filtro_ref is not None:
            q_refunds = q_refunds.filter(filtro_ref)

        combined = union_all(q_logs, q_res, q_refunds).subquery()
        query = db.query(combined)

        if limit and limit > 0:
            results = query.order_by(combined.c.fecha.desc()).offset(offset).limit(limit).all()
        else:
            results = query.order_by(combined.c.fecha.desc()).all()
        return results

    @staticmethod
    def access_logs_history(db: Session, sucursal=None, patente=None, limit: int = 300) -> list:
        """HISTORIAL DE ACCESOS ALPR FILTRADO POR SUCURSAL Y PATENTE OPCIONAL.

        Limite server-side (default 300): evita traer la tabla completa en el
        dashboard operativo (rutas A5) — el `IN ()` de patentes resultante
        explota en SQLite (>999 vars) y bordea el limite de Postgres (65535).
        """
        q = db.query(models.AccessLog)
        if sucursal:
            q = q.filter(_branch_filter(models.AccessLog.sucursal, sucursal))
        if patente:
            q = q.filter(models.AccessLog.patente_detectada.like(f"%{patente.upper()}%"))
        return q.order_by(models.AccessLog.id.desc()).limit(limit).all()

    @staticmethod
    def logs_with_ocr(db: Session, sucursal=None, limit=100, ascending=False) -> list:
        """LOGS CON TIEMPO OCR MEDIDO (TOP `limit` DESCENDENTE o serie ASCENDENTE COMPLETA)."""
        q = db.query(models.AccessLog).filter(models.AccessLog.ocr_time.isnot(None))
        if sucursal:
            q = q.filter(_branch_filter(models.AccessLog.sucursal, sucursal))
        if ascending:
            q = q.order_by(models.AccessLog.id.asc())
        else:
            q = q.order_by(models.AccessLog.id.desc()).limit(limit)
        return q.all()

    @staticmethod
    def access_event_rows(db: Session, sucursal=None) -> list:
        """PARES (fecha_hora, tipo_evento) DE TODOS LOS ACCESOS PARA LA SERIE TEMPORAL."""
        filters = []
        if sucursal:
            filters.append(_branch_filter(models.AccessLog.sucursal, sucursal))
        return db.query(models.AccessLog.fecha_hora, models.AccessLog.tipo_evento).filter(*filters).all()

    @staticmethod
    def reservation_activity_rows(db: Session, sucursal=None, start_date=None, end_date=None) -> list:
        """TUPLAS (fecha_inicio, fecha_fin, estado_reserva, estado_pago, monto_total, tipo_vehiculo, patente)
        DE RESERVAS QUE TOCAN EL RANGO [start_date, end_date]."""
        q = db.query(
            models.Reservation.fecha_inicio, models.Reservation.fecha_fin,
            models.Reservation.estado_reserva, models.Reservation.estado_pago,
            models.Reservation.monto_total, models.Reservation.tipo_vehiculo,
            models.Reservation.patente
        )
        if sucursal:
            q = q.filter(_branch_filter(models.Reservation.sucursal_nombre, sucursal))
        if start_date:
            q = q.filter(models.Reservation.fecha_fin >= start_date)
        if end_date:
            q = q.filter(models.Reservation.fecha_inicio <= end_date)
        return q.all()

    @staticmethod
    def entrance_patent_events(db: Session, sucursal=None, start_date=None, end_date=None) -> list:
        """PARES (normalized_patente, fecha_hora) DE EVENTOS ENTRADA ALPR (PARA DETECTAR NO-SHOW)."""
        q = db.query(models.AccessLog.normalized_patente, models.AccessLog.fecha_hora).filter(
            models.AccessLog.tipo_evento == AccessEventType.ENTRADA.value
        )
        if sucursal:
            q = q.filter(_branch_filter(models.AccessLog.sucursal, sucursal))
        if start_date:
            q = q.filter(models.AccessLog.fecha_hora >= start_date)
        if end_date:
            q = q.filter(models.AccessLog.fecha_hora <= end_date)
        return q.all()