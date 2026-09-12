import datetime
import math
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, union_all, literal_column, or_, and_
import models
from models.enums import UserRole, ReservationStatus, PaymentStatus, AccessEventType
from services.billing_service import BillingService
from services.time_service import TimeService

CASH_METHODS = ("CAJA", "Caja", "Efectivo")

def _es_reembolso_parcial(col_estado, col_reembolsado):
    """Reembolsos: reservas reembolsadas completas O pagadas con reembolso parcial acumulado."""
    return or_(
        col_estado == PaymentStatus.REEMBOLSADO,
        and_(col_estado == PaymentStatus.PAGADO, col_reembolsado > 0)
    )

PAYMENT_METHOD_VARIANTS = {
    "CAJA": CASH_METHODS,
    "DIGITAL": ("DIGITAL", "SALDO", "Billetera", "BILLETERA", "BILLETERA AUTOPASS"),
    "MERCADOPAGO": ("MERCADOPAGO", "MERCADO PAGO", "Mercado Pago"),
    "TRANSFERENCIA": ("TRANSFERENCIA", "Transferencia"),
    "TARJETA": ("TARJETA", "Tarjeta"),
    "OTRO": ("OTRO", "Otro"),
}


def _canonical_method(m):
    """Normaliza un método guardado en BD al método canónico (None legacy = DIGITAL)."""
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

def _payment_method_filter(column, method: str):
    """Filtro SQL por método de pago canónico (all = sin filtro). NULL cuenta como DIGITAL."""
    if method == "all" or not method:
        return None
    if method == "DIGITAL":
        return or_(column.is_(None), column.notin_(CASH_METHODS))
    variants = PAYMENT_METHOD_VARIANTS.get(method)
    if variants:
        return column.in_(variants)
    return column == method

class ReportService:
    """Servicio de Inteligencia de Negocio para analítica financiera y auditoría de accesos."""

    @staticmethod
    def get_date_range(period: str, start: str = None, end: str = None):
        start_date = start
        end_date = end
        if period != "total" and not start:
            now = datetime.datetime.now()
            if period == "day":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            elif period == "week":
                start_date = (now - datetime.timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            elif period == "month":
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
            elif period == "year":
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        return start_date, end_date

    @classmethod
    def get_financial_summary(
        cls,
        db: Session,
        user: models.User,
        period: str = "total",
        start: str = None,
        end: str = None,
        vehicle_type: str = "all",
        payment_method: str = "all"
    ) -> dict:
        """Calcula el resumen de recaudación unificado por sucursal, tipo de vehículo y método de pago."""
        start_date, end_date = cls.get_date_range(period, start, end)
        sucursal = user.sucursal if str(user.rol) != UserRole.ADMIN.value else None

        # 1. Recaudación de AccessLogs (Estadías ALPR)
        def _logs_agg(method: str = "all"):
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
                target_name = sucursal.replace('AUTOPASS ', '').strip()
                q = q.filter(models.AccessLog.sucursal.like(f"%{target_name}%"))

            if start_date:
                q = q.filter((models.AccessLog.fecha_pago >= start_date) |
                               ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora >= start_date)))
            if end_date:
                q = q.filter((models.AccessLog.fecha_pago <= end_date) |
                               ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora <= end_date)))
            return q.first()

        total_logs, count_logs = _logs_agg(payment_method)
        total_logs = float(total_logs or 0.0)
        count_logs = count_logs or 0

        if payment_method == "CAJA":
            total_efectivo = float(_logs_agg("CAJA")[0] or 0.0)
            total_digital_logs = 0.0
        elif payment_method == "DIGITAL":
            total_efectivo = 0.0
            total_digital_logs = float(_logs_agg("DIGITAL")[0] or 0.0)
        elif payment_method in PAYMENT_METHOD_VARIANTS:
            total_efectivo = 0.0
            total_digital_logs = float(_logs_agg(payment_method)[0] or 0.0)
        else:
            total_efectivo = float(_logs_agg("CAJA")[0] or 0.0)
            total_digital_logs = float(_logs_agg("DIGITAL")[0] or 0.0)

        # 2. Recaudación de Reservations (método real de pago; legacy NULL = DIGITAL)
        q_res_pagos = db.query(
            func.sum(models.Reservation.monto_total),
            func.count(models.Reservation.id)
        ).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)
        
        q_res_pagos = q_res_pagos.filter(models.Reservation.estado_pago.in_([PaymentStatus.PAGADO, PaymentStatus.REEMBOLSADO]))

        if vehicle_type != "all":
            q_res_pagos = q_res_pagos.filter(models.Vehicle.tipo == vehicle_type)
        
        if sucursal:
            target_name = sucursal.replace('AUTOPASS ', '').strip()
            q_res_pagos = q_res_pagos.filter(models.Reservation.sucursal_nombre.like(f"%{target_name}%"))

        if start_date:
            q_res_pagos = q_res_pagos.filter((models.Reservation.fecha_pago >= start_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
        if end_date:
            q_res_pagos = q_res_pagos.filter((models.Reservation.fecha_pago <= end_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))

        filtro_res = _payment_method_filter(models.Reservation.metodo_pago, payment_method)
        if filtro_res is not None:
            q_res_pagos = q_res_pagos.filter(filtro_res)

        total_res_bruto, count_res = q_res_pagos.first()
        total_res_bruto = float(total_res_bruto or 0.0)
        count_res = count_res or 0
        
        # Reembolsos
        q_refunds = db.query(func.sum(models.Reservation.monto_reembolsado)).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)
        q_refunds = q_refunds.filter(_es_reembolso_parcial(models.Reservation.estado_pago, models.Reservation.monto_reembolsado))
        
        if vehicle_type != "all":
            q_refunds = q_refunds.filter(models.Vehicle.tipo == vehicle_type)
            
        if sucursal:
            target_name = sucursal.replace('AUTOPASS ', '').strip()
            q_refunds = q_refunds.filter(models.Reservation.sucursal_nombre.like(f"%{target_name}%"))
        
        if start_date:
            q_refunds = q_refunds.filter((models.Reservation.fecha_pago >= start_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
        if end_date:
            q_refunds = q_refunds.filter((models.Reservation.fecha_pago <= end_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))

        filtro_ref = _payment_method_filter(models.Reservation.metodo_pago, payment_method)
        if filtro_ref is not None:
            q_refunds = q_refunds.filter(filtro_ref)
        
        total_refunds = float(q_refunds.scalar() or 0.0)
        
        total_res_neto = max(0, total_res_bruto - total_refunds)

        # 3. Métricas de Cancelación
        if payment_method == "CAJA":
            tasa_cancelacion = 0
            ingresos_incumplimiento = 0.0
        else:
            q_cancelled = db.query(models.Reservation).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True).filter(models.Reservation.estado_reserva == ReservationStatus.CANCELADA)
            q_total_res = db.query(func.count(models.Reservation.id)).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)
            
            if vehicle_type != "all":
                q_cancelled = q_cancelled.filter(models.Vehicle.tipo == vehicle_type)
                q_total_res = q_total_res.filter(models.Vehicle.tipo == vehicle_type)

            if sucursal:
                target_name = sucursal.replace('AUTOPASS ', '').strip()
                q_cancelled = q_cancelled.filter(models.Reservation.sucursal_nombre.like(f"%{target_name}%"))
                q_total_res = q_total_res.filter(models.Reservation.sucursal_nombre.like(f"%{target_name}%"))
            
            if start_date:
                q_cancelled = q_cancelled.filter(models.Reservation.fecha_inicio >= start_date)
                q_total_res = q_total_res.filter(models.Reservation.fecha_inicio >= start_date)
            if end_date:
                q_cancelled = q_cancelled.filter(models.Reservation.fecha_inicio <= end_date)
                q_total_res = q_total_res.filter(models.Reservation.fecha_inicio <= end_date)

            cancelled_list = q_cancelled.all()
            count_cancelled = len(cancelled_list)
            count_total_res = q_total_res.scalar() or 0
            tasa_cancelacion = round((count_cancelled / count_total_res * 100), 1) if count_total_res > 0 else 0

            ingresos_incumplimiento = 0.0
            for c in cancelled_list:
                if c.estado_pago == PaymentStatus.CANCELADO:
                    ingresos_incumplimiento += (c.monto_total or 0.0)
                elif c.estado_pago == PaymentStatus.REEMBOLSADO:
                    ingresos_incumplimiento += max(0.0, (c.monto_total or 0.0) - (c.monto_reembolsado or 0.0))

        total_final = round(total_logs + total_res_neto, 2)
        count_final = count_logs + count_res

        # 4. Ingresos Proyectados (autos físicamente presentes)
        #    UNA SOLA QUERY con NOT EXISTS: entradas sin salida posterior y sin pago confirmado.
        Log = models.AccessLog
        Salida = aliased(models.AccessLog)
        q_parked = db.query(Log).filter(
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
            q_parked = q_parked.filter(Log.tipo_vehiculo == vehicle_type)

        if sucursal:
            target_name = sucursal.replace('AUTOPASS ', '').strip()
            q_parked = q_parked.filter(Log.sucursal.like(f"%{target_name}%"))
        
        entradas = q_parked.all()
        deuda_proyectada = 0.0
        # Cache de tarifas por (sucursal, tipo) para no repetir queries de Settings por vehículo
        rate_cache = {}
        for e in entradas:
            key = (e.sucursal, e.tipo_vehiculo)
            if key not in rate_cache:
                rate_cache[key] = BillingService.get_30min_rate(db, sucursal=e.sucursal, tipo_vehiculo=e.tipo_vehiculo)
            tarifa_30min = rate_cache[key]
            delta = TimeService.now() - datetime.datetime.fromisoformat(e.fecha_hora)
            bloques_a_cobrar = max(1, math.ceil(delta.total_seconds() / 1800))
            deuda_proyectada += bloques_a_cobrar * tarifa_30min

        # 5. Desglose por método de pago (estadías + reservas netas)
        desglose_metodos = {k: {"monto": 0.0, "cantidad": 0} for k in PAYMENT_METHOD_VARIANTS}

        q_grp_logs = db.query(
            models.AccessLog.metodo_pago,
            func.sum(models.AccessLog.costo_estadia),
            func.count(models.AccessLog.id)
        ).filter(models.AccessLog.pago_confirmado == True, models.AccessLog.costo_estadia > 0)
        if vehicle_type != "all":
            q_grp_logs = q_grp_logs.filter(models.AccessLog.tipo_vehiculo == vehicle_type)
        if sucursal:
            target_name = sucursal.replace('AUTOPASS ', '').strip()
            q_grp_logs = q_grp_logs.filter(models.AccessLog.sucursal.like(f"%{target_name}%"))
        if start_date:
            q_grp_logs = q_grp_logs.filter((models.AccessLog.fecha_pago >= start_date) | ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora >= start_date)))
        if end_date:
            q_grp_logs = q_grp_logs.filter((models.AccessLog.fecha_pago <= end_date) | ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora <= end_date)))
        for m, monto, cnt in q_grp_logs.group_by(models.AccessLog.metodo_pago).all():
            canon = _canonical_method(m)
            if canon in desglose_metodos:
                desglose_metodos[canon]["monto"] += float(monto or 0.0)
                desglose_metodos[canon]["cantidad"] += cnt or 0

        q_grp_res = db.query(
            models.Reservation.metodo_pago,
            func.sum(models.Reservation.monto_total),
            func.count(models.Reservation.id)
        ).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)
        q_grp_res = q_grp_res.filter(models.Reservation.estado_pago.in_([PaymentStatus.PAGADO, PaymentStatus.REEMBOLSADO]))
        if vehicle_type != "all":
            q_grp_res = q_grp_res.filter(models.Vehicle.tipo == vehicle_type)
        if sucursal:
            target_name = sucursal.replace('AUTOPASS ', '').strip()
            q_grp_res = q_grp_res.filter(models.Reservation.sucursal_nombre.like(f"%{target_name}%"))
        if start_date:
            q_grp_res = q_grp_res.filter((models.Reservation.fecha_pago >= start_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
        if end_date:
            q_grp_res = q_grp_res.filter((models.Reservation.fecha_pago <= end_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))
        for m, monto, cnt in q_grp_res.group_by(models.Reservation.metodo_pago).all():
            canon = _canonical_method(m)
            if canon in desglose_metodos:
                desglose_metodos[canon]["monto"] += float(monto or 0.0)
                desglose_metodos[canon]["cantidad"] += cnt or 0

        q_grp_ref = db.query(
            models.Reservation.metodo_pago,
            func.sum(func.coalesce(models.Reservation.monto_reembolsado, 0.0)),
            func.count(models.Reservation.id)
        ).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)
        q_grp_ref = q_grp_ref.filter(_es_reembolso_parcial(models.Reservation.estado_pago, models.Reservation.monto_reembolsado))
        if vehicle_type != "all":
            q_grp_ref = q_grp_ref.filter(models.Vehicle.tipo == vehicle_type)
        if sucursal:
            target_name = sucursal.replace('AUTOPASS ', '').strip()
            q_grp_ref = q_grp_ref.filter(models.Reservation.sucursal_nombre.like(f"%{target_name}%"))
        if start_date:
            q_grp_ref = q_grp_ref.filter((models.Reservation.fecha_pago >= start_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
        if end_date:
            q_grp_ref = q_grp_ref.filter((models.Reservation.fecha_pago <= end_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))
        for m, monto, _ in q_grp_ref.group_by(models.Reservation.metodo_pago).all():
            canon = _canonical_method(m)
            if canon in desglose_metodos:
                desglose_metodos[canon]["monto"] -= float(monto or 0.0)

        desglose_metodos = [
            {"metodo": k, "monto": round(v["monto"], 2), "cantidad": v["cantidad"]}
            for k, v in desglose_metodos.items()
            if v["monto"] != 0.0
        ]

        return {
            "total_recaudado": total_final,
            "total_reembolsado": round(total_refunds, 2),
            "cantidad_pagos": count_final,
            "ticket_promedio": round(total_final / count_final, 2) if count_final > 0 else 0,
            "ingresos_proyectados": round(deuda_proyectada, 2),
            "tasa_cancelacion": tasa_cancelacion,
            "ingresos_incumplimiento": round(ingresos_incumplimiento, 2),
            "recaudado_efectivo": round(total_efectivo, 2),
            "recaudado_digital": round(total_digital_logs + total_res_neto, 2),
            "desglose": {
                "estadias": {"monto": total_logs, "cantidad": count_logs, "promedio": round(total_logs / count_logs, 2) if count_logs > 0 else 0},
                "reservas": {"monto": total_res_neto, "cantidad": count_res, "promedio": round(total_res_neto / count_res, 2) if count_res > 0 else 0}
            },
            "desglose_metodos": desglose_metodos
        }

    @classmethod
    def get_payment_history(
        cls,
        db: Session,
        admin: models.User,
        period: str = "total",
        start: str = None,
        end: str = None,
        vehicle_type: str = "all",
        payment_method: str = "all",
        page: int = 1,
        limit: int = 20
    ) -> list:
        """Obtiene el historial unificado de pagos (estadías, reservas y reembolsos)."""
        start_date, end_date = cls.get_date_range(period, start, end)
        sucursal = admin.sucursal if str(admin.rol) != UserRole.ADMIN.value else None
        offset = (page - 1) * limit

        # 1. Estadías
        q_logs = db.query(
            literal_column("'L' || CAST(access_logs.id AS TEXT)").label("id"),
            func.coalesce(models.AccessLog.fecha_pago, models.AccessLog.fecha_hora).label("fecha"),
            models.AccessLog.patente_detectada.label("patente"),
            models.AccessLog.costo_estadia.label("monto"),
            literal_column("'Estadía'").label("tipo"),
            models.AccessLog.metodo_pago.label("metodo")
        ).filter(models.AccessLog.pago_confirmado == True, models.AccessLog.costo_estadia > 0)
        
        if vehicle_type != "all": q_logs = q_logs.filter(models.AccessLog.tipo_vehiculo == vehicle_type)
        filtro_logs = _payment_method_filter(models.AccessLog.metodo_pago, payment_method)
        if filtro_logs is not None:
            q_logs = q_logs.filter(filtro_logs)

        if sucursal:
            target_name = sucursal.replace('AUTOPASS ', '').strip()
            q_logs = q_logs.filter(models.AccessLog.sucursal.like(f"%{target_name}%"))
        if start_date: q_logs = q_logs.filter((models.AccessLog.fecha_pago >= start_date) | ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora >= start_date)))
        if end_date: q_logs = q_logs.filter((models.AccessLog.fecha_pago <= end_date) | ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora <= end_date)))

        # 2. Reservas
        q_res = db.query(
            literal_column("'R' || CAST(reservations.id AS TEXT)").label("id"),
            func.coalesce(models.Reservation.fecha_pago, models.Reservation.fecha_inicio).label("fecha"),
            models.Reservation.patente.label("patente"),
            models.Reservation.monto_total.label("monto"),
            literal_column("'Reserva'").label("tipo"),
            func.coalesce(models.Reservation.metodo_pago, "DIGITAL").label("metodo")
        ).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)
        
        q_res = q_res.filter(models.Reservation.estado_pago == PaymentStatus.PAGADO)
        if vehicle_type != "all": q_res = q_res.filter(models.Vehicle.tipo == vehicle_type)
        if sucursal:
            target_name = sucursal.replace('AUTOPASS ', '').strip()
            q_res = q_res.filter(models.Reservation.sucursal_nombre.like(f"%{target_name}%"))
        if start_date: q_res = q_res.filter((models.Reservation.fecha_pago >= start_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
        if end_date: q_res = q_res.filter((models.Reservation.fecha_pago <= end_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))
        filtro_res_hist = _payment_method_filter(models.Reservation.metodo_pago, payment_method)
        if filtro_res_hist is not None:
            q_res = q_res.filter(filtro_res_hist)

        # 3. Reembolsos
        q_refunds = db.query(
            literal_column("'REF' || CAST(reservations.id AS TEXT)").label("id"),
            func.coalesce(models.Reservation.fecha_pago, models.Reservation.fecha_inicio).label("fecha"),
            models.Reservation.patente.label("patente"),
            (models.Reservation.monto_reembolsado * -1).label("monto"),
            literal_column("'Reembolso'").label("tipo"),
            func.coalesce(models.Reservation.metodo_pago, "DIGITAL").label("metodo")
        ).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)
        
        q_refunds = q_refunds.filter(_es_reembolso_parcial(models.Reservation.estado_pago, models.Reservation.monto_reembolsado))
        if vehicle_type != "all": q_refunds = q_refunds.filter(models.Vehicle.tipo == vehicle_type)
        if sucursal:
            target_name = sucursal.replace('AUTOPASS ', '').strip()
            q_refunds = q_refunds.filter(models.Reservation.sucursal_nombre.like(f"%{target_name}%"))
        if start_date: q_refunds = q_refunds.filter((models.Reservation.fecha_pago >= start_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
        if end_date: q_refunds = q_refunds.filter((models.Reservation.fecha_pago <= end_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))
        filtro_ref_hist = _payment_method_filter(models.Reservation.metodo_pago, payment_method)
        if filtro_ref_hist is not None:
            q_refunds = q_refunds.filter(filtro_ref_hist)

        combined = union_all(q_logs, q_res, q_refunds).subquery()
        query = db.query(combined)
        
        if limit and limit > 0:
            results = query.order_by(combined.c.fecha.desc()).offset(offset).limit(limit).all()
        else:
            results = query.order_by(combined.c.fecha.desc()).all()

        return [{"id": r.id, "fecha_pago": r.fecha, "patente_detectada": r.patente, "costo_estadia": r.monto, "tipo": r.tipo, "metodo": r.metodo} for r in results]

    @classmethod
    def get_access_logs(cls, db: Session, staff: models.User, patente: str = None) -> list:
        """Obtiene historial de accesos ALPR filtrado por sucursal y patente opcional."""
        q = db.query(models.AccessLog)
        if str(staff.rol) != UserRole.ADMIN.value:
            target_name = staff.sucursal.replace('AUTOPASS ', '').strip()
            q = q.filter(models.AccessLog.sucursal.like(f"%{target_name}%"))
        if patente:
            q = q.filter(models.AccessLog.patente_detectada.like(f"%{patente.upper()}%"))
        logs = q.order_by(models.AccessLog.id.desc()).all()

        # RESOLVER USUARIO (REGISTRADO O INVITADO) POR PATENTE
        patentes = [l.patente_detectada for l in logs if l.patente_detectada]
        user_by_plate = {}
        if patentes:
            vehicles = db.query(models.Vehicle).filter(
                models.Vehicle.patente.in_(patentes)
            ).all()
            user_ids = [v.user_id for v in vehicles if v.user_id]
            users_map = {}
            if user_ids:
                users = db.query(models.User).filter(
                    models.User.id.in_(user_ids)
                ).all()
                users_map = {u.id: u for u in users}
            for v in vehicles:
                u = users_map.get(v.user_id)
                if u:
                    user_by_plate[v.patente] = " ".join(filter(None, [u.nombre, u.apellido])).strip() or u.email

        result = []
        for l in logs:
            d = {c.name: getattr(l, c.name) for c in l.__table__.columns}
            d["usuario"] = user_by_plate.get(l.patente_detectada)
            d["es_registrado"] = bool(d["usuario"])
            result.append(d)
        return result

    @classmethod
    def get_ocr_stats(cls, db: Session, staff: models.User, limit: int = 100) -> dict:
        """Estadísticas de tiempos de procesamiento OCR."""
        q = db.query(models.AccessLog).filter(models.AccessLog.ocr_time.isnot(None))
        if str(staff.rol) != UserRole.ADMIN.value:
            target_name = staff.sucursal.replace('AUTOPASS ', '').strip()
            q = q.filter(models.AccessLog.sucursal.like(f"%{target_name}%"))
        
        logs = q.order_by(models.AccessLog.id.desc()).limit(limit).all()
        
        ocr_times = [l.ocr_time for l in logs if l.ocr_time is not None]
        
        if not ocr_times:
            return {"logs": [], "stats": {"count": 0, "avg_ocr": 0, "min_ocr": 0, "max_ocr": 0, "p90_ocr": 0}}
        
        sorted_times = sorted(ocr_times)
        p90_idx = int(len(sorted_times) * 0.9)

        return {
            "logs": [{
                "id": l.id,
                "patente": l.patente_detectada,
                "tipo_evento": l.tipo_evento,
                "fecha_hora": l.fecha_hora,
                "ocr_time": round(l.ocr_time, 3) if l.ocr_time else None,
                "sucursal": l.sucursal
            } for l in logs],
            "stats": {
                "count": len(ocr_times),
                "avg_ocr": round(sum(ocr_times) / len(ocr_times), 3),
                "min_ocr": round(min(ocr_times), 3),
                "max_ocr": round(max(ocr_times), 3),
                "p90_ocr": round(sorted_times[p90_idx], 3) if p90_idx < len(sorted_times) else round(sorted_times[-1], 3)
            }
        }

    @classmethod
    def get_ocr_activity(cls, db: Session, staff: models.User) -> dict:
        """Serie cronológica COMPLETA de tiempos OCR (desde el primer dato hasta el último),
        para el gráfico móvil de la página de estadísticas OCR."""
        q = db.query(models.AccessLog).filter(models.AccessLog.ocr_time.isnot(None))
        if str(staff.rol) != UserRole.ADMIN.value:
            target_name = staff.sucursal.replace("AUTOPASS ", "").strip()
            q = q.filter(models.AccessLog.sucursal.like(f"%{target_name}%"))

        logs = q.order_by(models.AccessLog.id.asc()).all()
        points = [{
            "fecha_hora": l.fecha_hora,
            "ocr_time": round(l.ocr_time, 3),
            "patente": l.patente_detectada,
            "sucursal": l.sucursal,
            "tipo_evento": l.tipo_evento
        } for l in logs if l.ocr_time is not None]

        return {
            "count": len(points),
            "first_datetime": points[0]["fecha_hora"] if points else None,
            "last_datetime": points[-1]["fecha_hora"] if points else None,
            "points": points
        }

    @classmethod
    def get_access_activity(cls, db: Session, admin: models.User, desde: str = None, hasta: str = None) -> dict:
        """Serie temporal horaria continua de accesos (ENTRADA/SALIDA) para el apartado Métricas.
        Va desde el primer registro disponible hasta la hora actual, completando huecos con cero
        para que el gráfico pueda moverse y retroceder hasta el primer dato. Acepta un rango
        opcional desde/hasta (fechas YYYY-MM-DD o timestamps) para acotar la serie."""
        from core.time import localnow

        filters = []
        if str(admin.rol) != UserRole.ADMIN.value and admin.sucursal:
            target_name = admin.sucursal.replace("AUTOPASS ", "").strip()
            filters.append(models.AccessLog.sucursal.like(f"%{target_name}%"))

        rows = db.query(
            models.AccessLog.fecha_hora,
            models.AccessLog.tipo_evento
        ).filter(*filters).all()

        def _parse(s):
            if not s:
                return None
            norm = str(s).replace("T", " ").strip()
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                try:
                    return datetime.datetime.strptime(norm, fmt)
                except ValueError:
                    continue
            return None

        def _hour_key(dt):
            return dt.strftime("%Y-%m-%d %H:00")

        def _boundary(s, is_end=False):
            if not s:
                return None
            s = str(s).strip()
            if len(s) == 10:
                s = f"{s} 23:59:59" if is_end else f"{s} 00:00:00"
            return _parse(s)

        f_desde = _boundary(desde, is_end=False)
        f_hasta = _boundary(hasta, is_end=True)

        if f_desde and f_hasta and f_desde > f_hasta:
            return {
                "first_bucket": None,
                "first_datetime": None,
                "last_bucket": None,
                "now_bucket": None,
                "buckets": [],
                "totals": {"entrada": 0, "salida": 0, "total": 0}
            }

        now = localnow().replace(minute=0, second=0, microsecond=0)

        counts = {}
        first_dt = None
        for fecha_hora, tipo_evento in rows:
            dt = _parse(fecha_hora)
            if dt is None:
                continue
            if f_desde and dt < f_desde:
                continue
            if f_hasta and dt > f_hasta:
                continue
            if first_dt is None or dt < first_dt:
                first_dt = dt
            key = _hour_key(dt)
            ev = (tipo_evento or "").upper()
            if ev in ("ENTRADA", "SALIDA"):
                count_key = (key, ev)
                counts[count_key] = counts.get(count_key, 0) + 1

        if first_dt is None:
            return {
                "first_bucket": None,
                "first_datetime": None,
                "last_bucket": None,
                "now_bucket": None,
                "buckets": [],
                "totals": {"entrada": 0, "salida": 0, "total": 0}
            }

        end_limit = now
        if f_hasta and f_hasta < now:
            end_limit = f_hasta

        buckets = []
        totals = {"entrada": 0, "salida": 0, "total": 0}

        start_limit = datetime.datetime(1, 1, 1)
        if f_desde:
            start_limit = f_desde.replace(minute=0, second=0, microsecond=0)
        cur = max(
            datetime.datetime(first_dt.year, first_dt.month, first_dt.day, first_dt.hour),
            start_limit
        )
        while cur <= end_limit:
            key = _hour_key(cur)
            e = counts.get((key, "ENTRADA"), 0)
            s = counts.get((key, "SALIDA"), 0)
            buckets.append({"label": key, "entrada": e, "salida": s, "total": e + s})
            totals["entrada"] += e
            totals["salida"] += s
            totals["total"] += e + s
            cur += datetime.timedelta(hours=1)

        return {
            "first_bucket": _hour_key(first_dt),
            "first_datetime": first_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "last_bucket": buckets[-1]["label"] if buckets else None,
            "now_bucket": end_limit.strftime("%Y-%m-%d %H:00"),
            "buckets": buckets,
            "totals": totals
        }
