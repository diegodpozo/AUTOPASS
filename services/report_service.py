import datetime
import math
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, union_all, literal_column
import models
from models.enums import UserRole, ReservationStatus, PaymentStatus, AccessEventType
from services.billing_service import BillingService
from services.time_service import TimeService

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
        q_logs = db.query(
            func.sum(models.AccessLog.costo_estadia),
            func.count(models.AccessLog.id)
        ).filter(models.AccessLog.pago_confirmado == True, models.AccessLog.costo_estadia > 0)
        
        if vehicle_type != "all":
            q_logs = q_logs.filter(models.AccessLog.tipo_vehiculo == vehicle_type)
        
        if payment_method != "all":
            q_logs = q_logs.filter(models.AccessLog.metodo_pago == payment_method)
        
        if sucursal:
            target_name = sucursal.replace('AUTOPASS ', '').strip()
            q_logs = q_logs.filter(models.AccessLog.sucursal.like(f"%{target_name}%"))
        
        if start_date:
            q_logs = q_logs.filter((models.AccessLog.fecha_pago >= start_date) | 
                                   ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora >= start_date)))
        if end_date:
            q_logs = q_logs.filter((models.AccessLog.fecha_pago <= end_date) | 
                                   ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora <= end_date)))
        
        total_logs, count_logs = q_logs.first()
        total_logs = float(total_logs or 0.0)
        count_logs = count_logs or 0

        # 2. Recaudación de Reservations (Siempre DIGITAL)
        q_res_pagos = db.query(
            func.sum(models.Reservation.monto_total),
            func.count(models.Reservation.id)
        ).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)
        
        q_res_pagos = q_res_pagos.filter(models.Reservation.estado_pago.in_([PaymentStatus.PAGADO, PaymentStatus.REEMBOLSADO]))

        if vehicle_type != "all":
            q_res_pagos = q_res_pagos.filter(models.Vehicle.tipo == vehicle_type)
        
        if payment_method == "CAJA":
            total_res_bruto, count_res = 0.0, 0
        else:
            if sucursal:
                target_name = sucursal.replace('AUTOPASS ', '').strip()
                q_res_pagos = q_res_pagos.filter(models.Reservation.sucursal_nombre.like(f"%{target_name}%"))
            
            if start_date:
                q_res_pagos = q_res_pagos.filter((models.Reservation.fecha_pago >= start_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
            if end_date:
                q_res_pagos = q_res_pagos.filter((models.Reservation.fecha_pago <= end_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))

            total_res_bruto, count_res = q_res_pagos.first()
            total_res_bruto = float(total_res_bruto or 0.0)
            count_res = count_res or 0

        # Reembolsos
        if payment_method == "CAJA":
            total_refunds = 0.0
        else:
            q_refunds = db.query(func.sum(models.Reservation.monto_reembolsado)).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)
            q_refunds = q_refunds.filter(models.Reservation.estado_pago == PaymentStatus.REEMBOLSADO)
            
            if vehicle_type != "all":
                q_refunds = q_refunds.filter(models.Vehicle.tipo == vehicle_type)
                
            if sucursal:
                target_name = sucursal.replace('AUTOPASS ', '').strip()
                q_refunds = q_refunds.filter(models.Reservation.sucursal_nombre.like(f"%{target_name}%"))
            
            if start_date:
                q_refunds = q_refunds.filter((models.Reservation.fecha_pago >= start_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
            if end_date:
                q_refunds = q_refunds.filter((models.Reservation.fecha_pago <= end_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))
            
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
                rate_cache[key] = BillingService.get_hourly_rate(db, sucursal=e.sucursal, tipo_vehiculo=e.tipo_vehiculo)
            precio_hora = rate_cache[key]
            delta = TimeService.now() - datetime.datetime.fromisoformat(e.fecha_hora)
            bloques_a_cobrar = max(1, math.ceil(delta.total_seconds() / 3600))
            deuda_proyectada += bloques_a_cobrar * precio_hora

        return {
            "total_recaudado": total_final,
            "total_reembolsado": round(total_refunds, 2),
            "cantidad_pagos": count_final,
            "ticket_promedio": round(total_final / count_final, 2) if count_final > 0 else 0,
            "ingresos_proyectados": round(deuda_proyectada, 2),
            "tasa_cancelacion": tasa_cancelacion,
            "ingresos_incumplimiento": round(ingresos_incumplimiento, 2),
            "desglose": {
                "estadias": {"monto": total_logs, "cantidad": count_logs, "promedio": round(total_logs / count_logs, 2) if count_logs > 0 else 0},
                "reservas": {"monto": total_res_neto, "cantidad": count_res, "promedio": round(total_res_neto / count_res, 2) if count_res > 0 else 0}
            }
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
        if payment_method != "all": q_logs = q_logs.filter(models.AccessLog.metodo_pago == payment_method)

        if sucursal:
            target_name = sucursal.replace('AUTOPASS ', '').strip()
            q_logs = q_logs.filter(models.AccessLog.sucursal.like(f"%{target_name}%"))
        if start_date: q_logs = q_logs.filter((models.AccessLog.fecha_pago >= start_date) | ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora >= start_date)))
        if end_date: q_logs = q_logs.filter((models.AccessLog.fecha_pago <= end_date) | ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora <= end_date)))

        # 2. Reservas
        if payment_method == "CAJA":
            q_res = db.query(
                literal_column("'R'").label("id"),
                literal_column("'1900-01-01'").label("fecha"),
                literal_column("''").label("patente"),
                literal_column("0.0").label("monto"),
                literal_column("''").label("tipo"),
                literal_column("''").label("metodo")
            ).filter(literal_column("1=0"))
        else:
            q_res = db.query(
                literal_column("'R' || CAST(reservations.id AS TEXT)").label("id"),
                func.coalesce(models.Reservation.fecha_pago, models.Reservation.fecha_inicio).label("fecha"),
                models.Reservation.patente.label("patente"),
                models.Reservation.monto_total.label("monto"),
                literal_column("'Reserva'").label("tipo"),
                literal_column("'DIGITAL'").label("metodo")
            ).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)
            
            q_res = q_res.filter(models.Reservation.estado_pago == PaymentStatus.PAGADO)
            if vehicle_type != "all": q_res = q_res.filter(models.Vehicle.tipo == vehicle_type)
            if sucursal:
                target_name = sucursal.replace('AUTOPASS ', '').strip()
                q_res = q_res.filter(models.Reservation.sucursal_nombre.like(f"%{target_name}%"))
            if start_date: q_res = q_res.filter((models.Reservation.fecha_pago >= start_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
            if end_date: q_res = q_res.filter((models.Reservation.fecha_pago <= end_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))

        # 3. Reembolsos
        if payment_method == "CAJA":
            q_refunds = db.query(
                literal_column("'REF'").label("id"),
                literal_column("'1900-01-01'").label("fecha"),
                literal_column("''").label("patente"),
                literal_column("0.0").label("monto"),
                literal_column("''").label("tipo"),
                literal_column("''").label("metodo")
            ).filter(literal_column("1=0"))
        else:
            q_refunds = db.query(
                literal_column("'REF' || CAST(reservations.id AS TEXT)").label("id"),
                func.coalesce(models.Reservation.fecha_pago, models.Reservation.fecha_inicio).label("fecha"),
                models.Reservation.patente.label("patente"),
                (models.Reservation.monto_reembolsado * -1).label("monto"),
                literal_column("'Reembolso'").label("tipo"),
                literal_column("'DIGITAL'").label("metodo")
            ).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)
            
            q_refunds = q_refunds.filter(models.Reservation.estado_pago == PaymentStatus.REEMBOLSADO)
            if vehicle_type != "all": q_refunds = q_refunds.filter(models.Vehicle.tipo == vehicle_type)
            if sucursal:
                target_name = sucursal.replace('AUTOPASS ', '').strip()
                q_refunds = q_refunds.filter(models.Reservation.sucursal_nombre.like(f"%{target_name}%"))
            if start_date: q_refunds = q_refunds.filter((models.Reservation.fecha_pago >= start_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date)))
            if end_date: q_refunds = q_refunds.filter((models.Reservation.fecha_pago <= end_date) | ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date)))

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
        return q.order_by(models.AccessLog.id.desc()).all()

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

        bt_times = [l.backend_time for l in logs if l.backend_time is not None]

        return {
            "logs": [{
                "id": l.id,
                "patente": l.patente_detectada,
                "tipo_evento": l.tipo_evento,
                "fecha_hora": l.fecha_hora,
                "ocr_time": round(l.ocr_time, 3) if l.ocr_time else None,
                "backend_time": round(l.backend_time, 3) if l.backend_time else None,
                "sucursal": l.sucursal
            } for l in logs],
            "stats": {
                "count": len(ocr_times),
                "avg_ocr": round(sum(ocr_times) / len(ocr_times), 3),
                "min_ocr": round(min(ocr_times), 3),
                "max_ocr": round(max(ocr_times), 3),
                "p90_ocr": round(sorted_times[p90_idx], 3) if p90_idx < len(sorted_times) else round(sorted_times[-1], 3),
                "avg_backend": round(sum(bt_times) / len(bt_times), 3) if bt_times else 0
            }
        }
