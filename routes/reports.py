import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
from core.database import get_db
from core.security import get_local_manager, get_operational_user
from models.enums import UserRole, ReservationStatus, PaymentStatus, AccessEventType

router = APIRouter(prefix="/v1/reports", tags=["Reports & Analytics"])

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

# --- ANALÍTICA FINANCIERA ---

@router.get("/financial-summary")
def get_financial_summary(period: str = "total", start: str = None, end: str = None, vehicle_type: str = "all", payment_method: str = "all", db: Session = Depends(get_db), user: models.User = Depends(get_operational_user)):
    """Calcula el resumen de recaudación unificado. Soporta filtrado por tipo de vehículo y método de pago."""
    start_date, end_date = get_date_range(period, start, end)
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

    # 2. Recaudación de Reservations (Siempre Digital)
    q_res_pagos = db.query(
        func.sum(models.Reservation.monto_total),
        func.count(models.Reservation.id)
    ).join(models.Vehicle, models.Reservation.patente == models.Vehicle.patente, isouter=True)
    
    q_res_pagos = q_res_pagos.filter(models.Reservation.estado_pago.in_([PaymentStatus.PAGADO, PaymentStatus.REEMBOLSADO]))

    if vehicle_type != "all":
        q_res_pagos = q_res_pagos.filter(models.Vehicle.tipo == vehicle_type)
    
    # Si filtran por CAJA, las reservas no deberían sumar (son siempre digitales)
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

    # Reembolsos (Siempre Digital)
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

    # 3. Métricas de Cancelación (Siempre Digital en este contexto)
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

    # 4. Ingresos Proyectados (Solo vehiculos que siguen ADENTRO ahora mismo)
    # Por defecto, la proyeccion no discrimina metodo de pago futuro, pero filtramos por tipo si se pide
    q_parked = db.query(models.AccessLog).filter(models.AccessLog.tipo_evento == AccessEventType.ENTRADA)
    
    if vehicle_type != "all":
        q_parked = q_parked.filter(models.AccessLog.tipo_vehiculo == vehicle_type)

    if sucursal:
        target_name = sucursal.replace('AUTOPASS ', '').strip()
        q_parked = q_parked.filter(models.AccessLog.sucursal.like(f"%{target_name}%"))
    
    entradas = q_parked.all()
    deuda_proyectada = 0.0
    from services.billing_service import BillingService
    for e in entradas:
        tiene_salida = db.query(models.AccessLog.id).filter(models.AccessLog.patente_detectada == e.patente_detectada, models.AccessLog.tipo_evento == AccessEventType.SALIDA, models.AccessLog.fecha_hora > e.fecha_hora, models.AccessLog.sucursal == e.sucursal).first()
        if not tiene_salida and not e.pago_confirmado:
            # CORRECCIÓN: Pasar el tipo de vehículo del log para usar la tarifa correcta (Auto vs Moto)
            deuda_proyectada += BillingService.calculate_debt(e.fecha_hora, db, sucursal=e.sucursal, tipo_vehiculo=e.tipo_vehiculo)

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

@router.get("/payment-history")
def get_payment_history(period: str = "total", start: str = None, end: str = None, vehicle_type: str = "all", payment_method: str = "all", page: int = 1, limit: int = 20, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """Lista el historial de transacciones incluyendo Reembolsos con soporte para UNION ALL robusto."""
    from sqlalchemy import union_all, literal_column
    start_date, end_date = get_date_range(period, start, end)
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

    # 2. Reservas (Siempre Digital)
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

    # 3. Reembolsos (Siempre Digital)
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

    # Combinamos usando subqueries para evitar problemas de binding
    combined = union_all(q_logs, q_res, q_refunds).subquery()
    query = db.query(combined)
    
    if limit and limit > 0:
        results = query.order_by(combined.c.fecha.desc()).offset(offset).limit(limit).all()
    else:
        results = query.order_by(combined.c.fecha.desc()).all()

    return [{"id": r.id, "fecha_pago": r.fecha, "patente_detectada": r.patente, "costo_estadia": r.monto, "tipo": r.tipo, "metodo": r.metodo} for r in results]


# --- AUDITORÍA DE ACCESOS ---

@router.get("/access")
def get_reports_access(patente: str = None, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Consulta el historial de eventos ALPR."""
    q = db.query(models.AccessLog)
    if str(staff.rol) != UserRole.ADMIN.value:
        target_name = staff.sucursal.replace('AUTOPASS ', '').strip()
        q = q.filter(models.AccessLog.sucursal.like(f"%{target_name}%"))
    if patente: q = q.filter(models.AccessLog.patente_detectada.like(f"%{patente.upper()}%"))
    return q.order_by(models.AccessLog.id.desc()).all()
