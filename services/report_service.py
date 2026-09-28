import datetime
import math
from sqlalchemy.orm import Session
import models
from models.enums import UserRole, PaymentStatus, AccessEventType
from services.billing_service import BillingService
from services.time_service import TimeService
from repositories.report_repository import (
    ReportRepository,
    PAYMENT_METHOD_VARIANTS,
    _canonical_method,
)
from repositories.vehicle_repository import VehicleRepository
from repositories.user_repository import UserRepository


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
            total, count = ReportRepository.paid_logs_aggregate(
                db, sucursal=sucursal, vehicle_type=vehicle_type,
                start_date=start_date, end_date=end_date, method=method
            )
            return (total or 0, count or 0)

        total_logs, count_logs = _logs_agg(payment_method)
        total_logs = float(total_logs)
        count_logs = count_logs or 0

        if payment_method == "CAJA":
            total_efectivo = float(_logs_agg("CAJA")[0])
            total_digital_logs = 0.0
        elif payment_method == "DIGITAL":
            total_efectivo = 0.0
            total_digital_logs = float(_logs_agg("DIGITAL")[0])
        elif payment_method in PAYMENT_METHOD_VARIANTS:
            total_efectivo = 0.0
            total_digital_logs = float(_logs_agg(payment_method)[0])
        else:
            total_efectivo = float(_logs_agg("CAJA")[0])
            total_digital_logs = float(_logs_agg("DIGITAL")[0])

        # 2. Recaudación de Reservations (método real de pago; legacy NULL = DIGITAL)
        total_res_bruto, count_res = ReportRepository.paid_reservations_aggregate(
            db, sucursal=sucursal, vehicle_type=vehicle_type,
            start_date=start_date, end_date=end_date, method=payment_method
        )
        total_res_bruto = float(total_res_bruto or 0.0)
        count_res = count_res or 0

        # Reembolsos
        total_refunds = float(
            ReportRepository.refunds_total(
                db, sucursal=sucursal, vehicle_type=vehicle_type,
                start_date=start_date, end_date=end_date, method=payment_method
            ) or 0.0
        )

        total_res_neto = max(0, total_res_bruto - total_refunds)

        # 3. Métricas de Cancelación
        if payment_method == "CAJA":
            tasa_cancelacion = 0
            ingresos_incumplimiento = 0.0
        else:
            cancelled_list = ReportRepository.cancelled_reservations(
                db, sucursal=sucursal, vehicle_type=vehicle_type,
                start_date=start_date, end_date=end_date
            )
            count_cancelled = len(cancelled_list)
            count_total_res = ReportRepository.total_reservations_count(
                db, sucursal=sucursal, vehicle_type=vehicle_type,
                start_date=start_date, end_date=end_date
            )
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
        entradas = ReportRepository.unpaid_entries_without_exit(
            db, sucursal=sucursal, vehicle_type=vehicle_type
        )
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

        for m, monto, cnt in ReportRepository.grouped_logs_by_method(
            db, sucursal=sucursal, vehicle_type=vehicle_type,
            start_date=start_date, end_date=end_date
        ):
            canon = _canonical_method(m)
            if canon in desglose_metodos:
                desglose_metodos[canon]["monto"] += float(monto or 0.0)
                desglose_metodos[canon]["cantidad"] += cnt or 0

        for m, monto, cnt in ReportRepository.grouped_reservations_by_method(
            db, sucursal=sucursal, vehicle_type=vehicle_type,
            start_date=start_date, end_date=end_date
        ):
            canon = _canonical_method(m)
            if canon in desglose_metodos:
                desglose_metodos[canon]["monto"] += float(monto or 0.0)
                desglose_metodos[canon]["cantidad"] += cnt or 0

        for m, monto, _cnt in ReportRepository.grouped_refunds_by_method(
            db, sucursal=sucursal, vehicle_type=vehicle_type,
            start_date=start_date, end_date=end_date
        ):
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

        results = ReportRepository.payment_history(
            db, sucursal=sucursal, vehicle_type=vehicle_type,
            start_date=start_date, end_date=end_date, method=payment_method,
            offset=offset, limit=limit
        )

        return [{"id": r.id, "fecha_pago": r.fecha, "patente_detectada": r.patente, "costo_estadia": r.monto, "tipo": r.tipo, "metodo": r.metodo} for r in results]

    @classmethod
    def get_access_logs(cls, db: Session, staff: models.User, patente: str = None, limit: int = 300) -> list:
        """Obtiene historial de accesos ALPR filtrado por sucursal y patente opcional."""
        sucursal = staff.sucursal if str(staff.rol) != UserRole.ADMIN.value else None
        logs = ReportRepository.access_logs_history(db, sucursal=sucursal, patente=patente, limit=limit)

        # RESOLVER USUARIO (REGISTRADO O INVITADO) POR PATENTE
        patentes = list(dict.fromkeys(l.patente_detectada for l in logs if l.patente_detectada))
        user_by_plate = {}
        if patentes:
            vehicles = VehicleRepository.get_by_patentes(db, patentes)
            user_ids = [v.user_id for v in vehicles if v.user_id]
            users_map = {}
            if user_ids:
                users_map = {u.id: u for u in UserRepository.get_by_ids(db, user_ids)}
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
        sucursal = staff.sucursal if str(staff.rol) != UserRole.ADMIN.value else None
        logs = ReportRepository.logs_with_ocr(db, sucursal=sucursal, limit=limit, ascending=False)

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
        sucursal = staff.sucursal if str(staff.rol) != UserRole.ADMIN.value else None
        logs = ReportRepository.logs_with_ocr(db, sucursal=sucursal, ascending=True)

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

        sucursal = admin.sucursal if str(admin.rol) != UserRole.ADMIN.value and admin.sucursal else None
        rows = ReportRepository.access_event_rows(db, sucursal=sucursal)

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
            if ev in (AccessEventType.ENTRADA, AccessEventType.SALIDA):
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