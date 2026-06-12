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
def get_financial_summary(period: str = "total", start: str = None, end: str = None, db: Session = Depends(get_db), user: models.User = Depends(get_operational_user)):
    """Calcula el resumen de recaudación unificado. Optimizado con filtros index-friendly."""
    start_date, end_date = get_date_range(period, start, end)
    sucursal = user.sucursal if user.rol != UserRole.ADMIN else None

    # 1. Recaudación de AccessLogs (Estadías ALPR)
    q_logs = db.query(
        func.sum(models.AccessLog.costo_estadia),
        func.count(models.AccessLog.id)
    ).filter(models.AccessLog.pago_confirmado == True, models.AccessLog.costo_estadia > 0)
    
    if sucursal: q_logs = q_logs.filter(models.AccessLog.sucursal == sucursal)
    
    if start_date:
        q_logs = q_logs.filter((models.AccessLog.fecha_pago >= start_date) | 
                               ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora >= start_date)))
    if end_date:
        q_logs = q_logs.filter((models.AccessLog.fecha_pago <= end_date) | 
                               ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora <= end_date)))
    
    total_logs, count_logs = q_logs.first()
    total_logs = float(total_logs or 0.0)
    count_logs = count_logs or 0

    # 2. Recaudación de Reservations (Bruto y Reembolsos)
    q_res_pagos = db.query(
        func.sum(models.Reservation.monto_total),
        func.count(models.Reservation.id)
    ).filter(models.Reservation.estado_pago.in_([PaymentStatus.PAGADO, PaymentStatus.REEMBOLSADO]))

    if sucursal: q_res_pagos = q_res_pagos.filter(models.Reservation.sucursal_nombre == sucursal)
    
    if start_date:
        q_res_pagos = q_res_pagos.filter(
            (models.Reservation.fecha_pago >= start_date) | 
            ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date))
        )
    if end_date:
        q_res_pagos = q_res_pagos.filter(
            (models.Reservation.fecha_pago <= end_date) | 
            ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date))
        )

    total_res_bruto, count_res = q_res_pagos.first()
    total_res_bruto = float(total_res_bruto or 0.0)
    count_res = count_res or 0

    # Calculamos reembolsos
    q_refunds = db.query(func.sum(models.Reservation.monto_reembolsado)).filter(models.Reservation.estado_pago == PaymentStatus.REEMBOLSADO)
    if sucursal: q_refunds = q_refunds.filter(models.Reservation.sucursal_nombre == sucursal)
    
    if start_date:
        q_refunds = q_refunds.filter(
            (models.Reservation.fecha_pago >= start_date) | 
            ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date))
        )
    if end_date:
        q_refunds = q_refunds.filter(
            (models.Reservation.fecha_pago <= end_date) | 
            ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date))
        )
    
    total_refunds = float(q_refunds.scalar() or 0.0)
    
    # Recaudación Neta de Reservas
    total_res_neto = max(0, total_res_bruto - total_refunds)

    # 3. Métricas de Cancelación e Incumplimiento
    q_cancelled = db.query(models.Reservation).filter(models.Reservation.estado_reserva == ReservationStatus.CANCELADA)
    q_total_res = db.query(func.count(models.Reservation.id))
    
    if sucursal:
        q_cancelled = q_cancelled.filter(models.Reservation.sucursal_nombre == sucursal)
        q_total_res = q_total_res.filter(models.Reservation.sucursal_nombre == sucursal)
    
    if start_date:
        q_cancelled = q_cancelled.filter(models.Reservation.fecha_inicio >= start_date)
        q_total_res = q_total_res.filter(models.Reservation.fecha_inicio >= start_date)

    cancelled_list = q_cancelled.all()
    count_cancelled = len(cancelled_list)
    count_total_res = q_total_res.scalar() or 0
    tasa_cancelacion = round((count_cancelled / count_total_res * 100), 1) if count_total_res > 0 else 0

    ingresos_incumplimiento = 0.0
    for c in cancelled_list:
        if c.estado_pago == PaymentStatus.CANCELADA:
            ingresos_incumplimiento += (c.monto_total or 0.0)
        elif c.estado_pago == PaymentStatus.REEMBOLSADO:
            ingresos_incumplimiento += max(0.0, (c.monto_total or 0.0) - (c.monto_reembolsado or 0.0))

    total_final = round(total_logs + total_res_neto, 2)
    count_final = count_logs + count_res

    # 4. Ingresos Proyectados
    q_parked = db.query(models.AccessLog).filter(models.AccessLog.tipo_evento == AccessEventType.ENTRADA)
    if sucursal: q_parked = q_parked.filter(models.AccessLog.sucursal == sucursal)
    
    entradas = q_parked.all()
    deuda_proyectada = 0.0
    from services.billing_service import BillingService
    
    for e in entradas:
        tiene_salida = db.query(models.AccessLog.id).filter(
            models.AccessLog.patente_detectada == e.patente_detectada,
            models.AccessLog.tipo_evento == AccessEventType.SALIDA,
            models.AccessLog.fecha_hora > e.fecha_hora,
            models.AccessLog.sucursal == e.sucursal
        ).first()
        
        if not tiene_salida and not e.pago_confirmado:
            deuda_proyectada += BillingService.calculate_debt(e.fecha_hora, db, sucursal=e.sucursal)

    return {
        "total_recaudado": total_final,
        "total_reembolsado": round(total_refunds, 2),
        "cantidad_pagos": count_final,
        "ticket_promedio": round(total_final / count_final, 2) if count_final > 0 else 0,
        "ingresos_proyectados": round(deuda_proyectada, 2),
        "tasa_cancelacion": tasa_cancelacion,
        "ingresos_incumplimiento": round(ingresos_incumplimiento, 2),
        "desglose": {
            "estadias": {
                "monto": total_logs,
                "cantidad": count_logs,
                "promedio": round(total_logs / count_logs, 2) if count_logs > 0 else 0
            },
            "reservas": {
                "monto": total_res_neto,
                "cantidad": count_res,
                "promedio": round(total_res_neto / count_res, 2) if count_res > 0 else 0
            }
        }
    }

@router.get("/payment-history")
def get_payment_history(
    period: str = "total", 
    start: str = None, 
    end: str = None, 
    page: int = 1, 
    limit: int = 20, 
    db: Session = Depends(get_db), 
    admin: models.User = Depends(get_local_manager)
):
    """Lista el historial de transacciones incluyendo Reembolsos con Paginación SQL."""
    from sqlalchemy import union_all, literal_column
    
    start_date, end_date = get_date_range(period, start, end)
    sucursal = admin.sucursal if admin.rol != UserRole.ADMIN else None
    offset = (page - 1) * limit

    # 1. Estadías
    q_logs = db.query(
        literal_column("'L' || CAST(id AS TEXT)").label("id"),
        func.coalesce(models.AccessLog.fecha_pago, models.AccessLog.fecha_hora).label("fecha"),
        models.AccessLog.patente_detectada.label("patente"),
        models.AccessLog.costo_estadia.label("monto"),
        literal_column("'Estadía'").label("tipo")
    ).filter(models.AccessLog.pago_confirmado == True, models.AccessLog.costo_estadia > 0)

    if sucursal: q_logs = q_logs.filter(models.AccessLog.sucursal == sucursal)
    if start_date:
        q_logs = q_logs.filter((models.AccessLog.fecha_pago >= start_date) | 
                               ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora >= start_date)))
    if end_date:
        q_logs = q_logs.filter((models.AccessLog.fecha_pago <= end_date) | 
                               ((models.AccessLog.fecha_pago == None) & (models.AccessLog.fecha_hora <= end_date)))

    # 2. Reservas Pagas
    q_res = db.query(
        literal_column("'R' || CAST(id AS TEXT)").label("id"),
        func.coalesce(models.Reservation.fecha_pago, models.Reservation.fecha_inicio).label("fecha"),
        models.Reservation.patente.label("patente"),
        models.Reservation.monto_total.label("monto"),
        literal_column("'Reserva'").label("tipo")
    ).filter(models.Reservation.estado_pago == PaymentStatus.PAGADO)

    if sucursal: q_res = q_res.filter(models.Reservation.sucursal_nombre == sucursal)
    if start_date:
        q_res = q_res.filter(
            (models.Reservation.fecha_pago >= start_date) | 
            ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date))
        )
    if end_date:
        q_res = q_res.filter(
            (models.Reservation.fecha_pago <= end_date) | 
            ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date))
        )

    # 3. Reembolsos (Monto Negativo)
    q_refunds = db.query(
        literal_column("'REF' || CAST(id AS TEXT)").label("id"),
        func.coalesce(models.Reservation.fecha_pago, models.Reservation.fecha_inicio).label("fecha"),
        models.Reservation.patente.label("patente"),
        (models.Reservation.monto_reembolsado * -1).label("monto"),
        literal_column("'Reembolso'").label("tipo")
    ).filter(models.Reservation.estado_pago == PaymentStatus.REEMBOLSADO)

    if sucursal: q_refunds = q_refunds.filter(models.Reservation.sucursal_nombre == sucursal)
    if start_date:
        q_refunds = q_refunds.filter(
            (models.Reservation.fecha_pago >= start_date) | 
            ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio >= start_date))
        )
    if end_date:
        q_refunds = q_refunds.filter(
            (models.Reservation.fecha_pago <= end_date) | 
            ((models.Reservation.fecha_pago == None) & (models.Reservation.fecha_inicio <= end_date))
        )

    # Combinamos todos con UNION ALL
    combined_query = union_all(q_logs.statement, q_res.statement, q_refunds.statement).alias("combined_payments")
    
    if limit and limit > 0:
        results = db.query(combined_query).order_by(combined_query.c.fecha.desc()).offset(offset).limit(limit).all()
    else:
        results = db.query(combined_query).order_by(combined_query.c.fecha.desc()).all()

    return [
        {
            "id": r.id,
            "fecha_pago": r.fecha,
            "patente_detectada": r.patente,
            "costo_estadia": r.monto,
            "tipo": r.tipo
        } for r in results
    ]

# --- AUDITORÍA DE ACCESOS ---

@router.get("/access")
def get_reports_access(patente: str = None, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Consulta el historial de eventos ALPR. Aislamiento por sede."""
    q = db.query(models.AccessLog)
    
    if staff.rol != UserRole.ADMIN:
        q = q.filter(models.AccessLog.sucursal == staff.sucursal)
        
    if patente: q = q.filter(models.AccessLog.patente_detectada.like(f"%{patente.upper()}%"))
    return q.order_by(models.AccessLog.id.desc()).all()
