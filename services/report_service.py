import datetime
import math
import re
from sqlalchemy.orm import Session
import models
from models.enums import UserRole, PaymentStatus, AccessEventType, ReservationStatus
from models.types import parse_fecha
from services.billing_service import BillingService
from services.time_service import TimeService
from repositories.report_repository import (
    ReportRepository,
    PAYMENT_METHOD_VARIANTS,
    _canonical_method,
)
from repositories.vehicle_repository import VehicleRepository
from repositories.user_repository import UserRepository
from core.normalize import normalize_plate

SPANISH_MONTHS = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def get_date_range(period: str, start: str = None, end: str = None):
    """Devuelve (start_date, end_date) del periodo o del rango start/end dado."""
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


def _parse(value):
    """PARSEA UN TIMESTAMP FLEXIBLE (ISO con 'T', con/ sin segundos o con microsegundos)."""
    if not value:
        return None
    try:
        return parse_fecha(value)
    except ValueError:
        return None


def _boundary(s, is_end=False):
    """NORMALIZA UN BORDE DE RANGO (YYYY-MM-DD o timestamp) A INICIO O FIN DE DIA."""
    if not s:
        return None
    s = str(s).strip()
    if len(s) == 10:
        s = f"{s} 23:59:59" if is_end else f"{s} 00:00:00"
    return _parse(s)


class ReportService:
    """Servicio de Inteligencia de Negocio para analítica financiera y auditoría de accesos."""

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
        start_date, end_date = get_date_range(period, start, end)
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
            if tarifa_30min is None:
                continue
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
        start_date, end_date = get_date_range(period, start, end)
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
        # OJO: los logs guardan la patente NORMALIZADA ("AB123CD") y el alta de vehiculo
        # la guarda CON formato visual ("AB 123 CD", ver user_service). Por eso la
        # busqueda es por patente normalizada y el mapeo se indexa por la misma clave.
        # Se genera una clave POR LOG (vacia si no hay patente) para que el zip de abajo
        # nunca se desalinee.
        patente_keys = [
            normalize_plate(l.normalized_patente or l.patente_detectada or "") for l in logs
        ]
        user_by_plate = {}
        normas = list(dict.fromkeys(k for k in patente_keys if k))
        if normas:
            vehicles = VehicleRepository.get_by_normalized_patentes(db, normas)
            user_ids = [v.user_id for v in vehicles if v.user_id]
            users_map = {}
            if user_ids:
                users_map = {u.id: u for u in UserRepository.get_by_ids(db, user_ids)}
            for v in vehicles:
                u = users_map.get(v.user_id)
                if u:
                    user_by_plate[normalize_plate(v.patente)] = " ".join(
                        filter(None, [u.nombre, u.apellido])
                    ).strip() or u.email

        result = []
        for l, key in zip(logs, patente_keys):
            d = {c.name: getattr(l, c.name) for c in l.__table__.columns}
            d["usuario"] = user_by_plate.get(key)
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

        def _hour_key(dt):
            return dt.strftime("%Y-%m-%d %H:00")

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

    @staticmethod
    def _open_hours_de(db: Session, sucursal=None) -> tuple:
        """HORAS DE APERTURA (apertura, cierre) DE LAS SUCURSALES SELECCIONADAS (union para TODAS).
        Parsing tolerante: '07:00 a 23:00', '07:00 UN 23:00' o '---' + flag is_24h. Cierre 00 => 23."""
        branches = []
        if sucursal:
            branches = [db.query(models.ParkingBranch).filter(
                models.ParkingBranch.nombre == sucursal,
                models.ParkingBranch.activa.is_(True)).first()]
        else:
            branches = db.query(models.ParkingBranch).filter(models.ParkingBranch.activa.is_(True)).all()

        spans = []
        for b in branches:
            if b is None or b.is_24h:
                spans.append((0, 23))
                continue
            nums = re.findall(r"(\d{1,2})\s*:\s*(\d{2})", b.horario or "")
            if not nums:
                spans.append((0, 23))
                continue
            h_ini = int(nums[0][0])
            h_fin = int(nums[-1][0])
            if h_fin == 0:
                h_fin = 23
            if h_fin < h_ini:
                spans.append((0, 23))
            else:
                spans.append((h_ini, h_fin))
        if not spans:
            spans = [(0, 23)]
        return min(s[0] for s in spans), max(s[1] for s in spans)

    @classmethod
    def get_traffic_heatmap(cls, db: Session, admin: models.User, sucursal: str = None,
                            desde: str = None, hasta: str = None) -> dict:
        """MAPA DE CALOR DIARIO: COLUMNAS = DIA DEL MES (1-31, agregado del rango), FILAS = HORAS DE APERTURA.
        Solo cuenta ENTRADAS. Para LOCAL_ADMIN queda acotado a su sede; el ADMIN global puede pedir una
        sucursal o todas. Incluye totales por día (abajo) y por hora (última columna)."""
        suc_real = admin.sucursal if str(admin.rol) != UserRole.ADMIN.value and admin.sucursal else sucursal
        h_ini, h_fin = cls._open_hours_de(db, sucursal=suc_real)
        n_horas = h_fin - h_ini + 1
        rows = ReportRepository.access_event_rows(db, sucursal=suc_real)

        entradas = []
        for fecha_hora, tipo_evento in rows:
            if (tipo_evento or "").upper() != AccessEventType.ENTRADA.value:
                continue
            dt = _parse(fecha_hora)
            if dt is not None:
                entradas.append(dt)

        f_desde = _boundary(desde, is_end=False)
        f_hasta = _boundary(hasta, is_end=True)
        if entradas:
            if f_desde is None:
                f_desde = entradas[0].replace(hour=0, minute=0, second=0, microsecond=0)
            if f_hasta is None:
                f_hasta = max(e for e in entradas)
        if f_desde is None:
            f_desde = TimeService.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if f_hasta is None:
            f_hasta = TimeService.now()
        if f_desde > f_hasta:
            f_desde, f_hasta = f_hasta, f_desde

        dias = []
        cur = f_desde.replace(hour=0, minute=0, second=0, microsecond=0)
        while cur <= f_hasta:
            dias.append(cur)
            cur += datetime.timedelta(days=1)

        index_por_fecha = {d.strftime("%Y-%m-%d"): i for i, d in enumerate(dias)}
        meses = []
        prev = None
        for i, d in enumerate(dias):
            clave = (d.year, d.month)
            if prev != clave:
                prev = clave
                meses.append({"label": f"{SPANISH_MONTHS[d.month]} {d.year}", "start": i, "count": 1})
            else:
                meses[-1]["count"] += 1

        matrix = [[0] * len(dias) for _ in range(n_horas)]
        for dt in entradas:
            if dt < f_desde or dt > f_hasta:
                continue
            if dt.hour < h_ini or dt.hour > h_fin:
                continue
            col = index_por_fecha.get(dt.strftime("%Y-%m-%d"))
            if col is None:
                continue
            matrix[dt.hour - h_ini][col] += 1

        return {
            "horas_labels": [f"{h:02d}:00" for h in range(h_ini, h_fin + 1)],
            "hora_ini": h_ini,
            "hora_fin": h_fin,
            "dias": [d.strftime("%Y-%m-%d") for d in dias],
            "meses": meses,
            "matrix": matrix,
            "totals_per_day": [sum(matrix[r][c] for r in range(n_horas)) for c in range(len(dias))],
            "totals_per_hour": [sum(row) for row in matrix],
            "total_entradas": sum(sum(row) for row in matrix),
            "max": max((c for row in matrix for c in row), default=0),
            "sucursal": suc_real,
            "is_24h": h_ini == 0 and h_fin == 23,
            "desde": f_desde.strftime("%Y-%m-%d"),
            "hasta": f_hasta.strftime("%Y-%m-%d")
        }

    @classmethod
    def get_occupancy_summary(cls, db: Session, admin: models.User, sucursal: str = None,
                              desde: str = None, hasta: str = None) -> dict:
        """OCUPACION DE RESERVAS VS CAPACIDAD POR HORA DEL DIA (PROMEDIO DEL RANGO) + KPIs DE RESERVAS.
        Incluye no-show: reservas pagadas vencidas sin evento ENTRADA ALPR de esa patente en la sede."""
        from services.availability import capacidad_reservas

        suc_real = admin.sucursal if str(admin.rol) != UserRole.ADMIN.value and admin.sucursal else sucursal
        f_desde = _boundary(desde, is_end=False)
        f_hasta = _boundary(hasta, is_end=True)
        if suc_real and f_desde and f_hasta and f_desde > f_hasta:
            f_desde, f_hasta = f_hasta, f_desde

        rows = ReportRepository.reservation_activity_rows(
            db, sucursal=suc_real,
            start_date=f_desde.strftime("%Y-%m-%d") if f_desde else None,
            end_date=f_hasta.strftime("%Y-%m-%d") if f_hasta else None
        )

        # --- KPIs DE RESERVAS ---
        filtro_reserva = [
            ("PAGADAS", lambda r: r.estado_pago == PaymentStatus.PAGADO.value),
            ("PENDIENTES", lambda r: r.estado_pago == PaymentStatus.PENDIENTE.value),
            ("CANCELADAS", lambda r: r.estado_reserva == ReservationStatus.CANCELADA.value),
            ("ACTIVAS", lambda r: r.estado_reserva == ReservationStatus.ACTIVA.value),
        ]
        contadores = {k: sum(1 for r in rows if fn(r)) for k, fn in filtro_reserva}
        total = len(rows)
        monto_pagado = sum(r[4] or 0 for r in rows if r[3] == PaymentStatus.PAGADO.value)

        # --- NO-SHOW SOBRE RESERVAS PAGADAS VENCIDAS ---
        ahora = TimeService.now()
        pagadas_vencidas = [
            r for r in rows
            if r[3] == PaymentStatus.PAGADO.value and _parse(r[1]) and _parse(r[1]) < ahora
        ]
        no_show = 0
        if pagadas_vencidas:
            entradas = {
                (p.upper().replace(" ", ""), _parse(f))
                for (p, f) in ReportRepository.entrance_patent_events(
                    db, sucursal=suc_real,
                    start_date=f"{f_desde.strftime('%Y-%m-%d')}" if f_desde else None,
                    end_date=f"{f_hasta.strftime('%Y-%m-%d')}" if f_hasta else None
                )
            }
            for r in pagadas_vencidas:
                pat_norm = (r[6] or "").upper().replace(" ", "")
                r_ini = _parse(r[0])
                r_fin = _parse(r[1])
                if not pat_norm or not r_ini or not r_fin:
                    continue
                hay_entrada = any(
                    p == pat_norm and r_ini <= f <= r_fin
                    for (p, f) in entradas
                )
                if not hay_entrada:
                    no_show += 1

        # --- OCUPACION MEDIA POR HORA DEL DIA (PROMEDIADA SOBRE LOS DIAS DEL RANGO) ---
        sucursales = [suc_real] if suc_real else [
            b.nombre for b in db.query(models.ParkingBranch).filter(models.ParkingBranch.activa.is_(True)).all()
        ]
        hora_ini = f_desde.replace(minute=0, second=0, microsecond=0) if f_desde else ahora - datetime.timedelta(days=30)
        hora_fin = f_hasta.replace(minute=0, second=0, microsecond=0) if f_hasta else ahora
        if hora_fin <= hora_ini:
            hora_fin = hora_ini + datetime.timedelta(days=30)
        dias = max(1, ((hora_fin - hora_ini).days + 1))

        tipos = ["Auto", "Moto", "Camioneta"]
        capacidad = {t: sum(capacidad_reservas(db, s, t) for s in sucursales) for t in tipos}
        serie = {t: [0.0] * 24 for t in tipos}

        for r in rows:
            tipo = (r[5] or "").strip().title()
            if tipo not in tipos:
                tipo = "Auto"
            r_ini = _parse(r[0])
            r_fin = _parse(r[1])
            if not r_ini or not r_fin:
                continue
            dia = hora_ini
            while dia <= hora_fin:
                if r_ini <= dia < r_fin:
                    serie[tipo][dia.hour] += 1
                dia += datetime.timedelta(days=1)

        por_tipo = {}
        for t in tipos:
            serie_pct = [
                round(min(100.0, serie[t][h] / max(1, dias) / capacidad[t] * 100), 1)
                if capacidad[t] else 0.0
                for h in range(24)
            ]
            por_tipo[t] = {
                "capacidad": capacidad[t],
                "promedio_absoluto": [round(serie[t][h] / max(1, dias), 2) for h in range(24)],
                "porcentaje": serie_pct
            }

        return {
            "sucursal": suc_real,
            "desde": f_desde.strftime("%Y-%m-%d") if f_desde else None,
            "hasta": f_hasta.strftime("%Y-%m-%d") if f_hasta else None,
            "dias_evaluados": dias,
            "kpi": {
                "total": total,
                "pagadas": contadores["PAGADAS"],
                "pendientes": contadores["PENDIENTES"],
                "canceladas": contadores["CANCELADAS"],
                "activas": contadores["ACTIVAS"],
                "tasa_pago": round(contadores["PAGADAS"] / total * 100, 1) if total else 0,
                "tasa_cancelacion": round(contadores["CANCELADAS"] / total * 100, 1) if total else 0,
                "no_show": no_show,
                "monto_pagado": round(monto_pagado, 2),
                "ticket_promedio": round(monto_pagado / contadores["PAGADAS"], 2) if contadores["PAGADAS"] else 0,
            },
            "por_tipo": por_tipo,
            "horas": list(range(24))
        }
