import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
from core.database import get_db
from core.security import get_local_manager, get_operational_user

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
def get_financial_summary(period: str = "total", start: str = None, end: str = None, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """Calcula el resumen de recaudación unificado (Estadías + Reservas)."""
    start_date, end_date = get_date_range(period, start, end)
    sucursal = admin.sucursal if admin.rol != "admin" else None

    # 1. Recaudación de AccessLogs (Estadías directas)
    q_logs = db.query(
        func.sum(models.AccessLog.costo_estadia),
        func.count(models.AccessLog.id)
    ).filter(models.AccessLog.pago_confirmado == True, models.AccessLog.costo_estadia > 0)
    
    if sucursal: q_logs = q_logs.filter(models.AccessLog.sucursal == sucursal)
    if start_date: q_logs = q_logs.filter(func.coalesce(models.AccessLog.fecha_pago, models.AccessLog.fecha_hora) >= start_date)
    if end_date: q_logs = q_logs.filter(func.coalesce(models.AccessLog.fecha_pago, models.AccessLog.fecha_hora) <= end_date)
    
    total_logs, count_logs = q_logs.first()
    total_logs = float(total_logs or 0.0)
    count_logs = count_logs or 0

    # 2. Recaudación de Reservations (Pagos anticipados)
    q_res = db.query(
        func.sum(models.Reservation.monto_total),
        func.count(models.Reservation.id)
    ).filter(models.Reservation.estado_pago == "Pagado")

    if sucursal: q_res = q_res.filter(models.Reservation.sucursal_nombre == sucursal)
    if start_date: q_res = q_res.filter(models.Reservation.fecha_inicio >= start_date)
    if end_date: q_res = q_res.filter(models.Reservation.fecha_inicio <= end_date)

    total_res, count_res = q_res.first()
    total_res = float(total_res or 0.0)
    count_res = count_res or 0

    total_final = round(total_logs + total_res, 2)
    count_final = count_logs + count_res

    return {
        "total_recaudado": total_final,
        "cantidad_pagos": count_final,
        "ticket_promedio": round(total_final / count_final, 2) if count_final > 0 else 0
    }

@router.get("/payment-history")
def get_payment_history(period: str = "total", start: str = None, end: str = None, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """Lista el historial de transacciones unificado (Estadías + Reservas)."""
    start_date, end_date = get_date_range(period, start, end)
    sucursal = admin.sucursal if admin.rol != "admin" else None

    # Obtener logs
    q_logs = db.query(models.AccessLog).filter(models.AccessLog.pago_confirmado == True, models.AccessLog.costo_estadia > 0)
    if sucursal: q_logs = q_logs.filter(models.AccessLog.sucursal == sucursal)
    if start_date: q_logs = q_logs.filter(func.coalesce(models.AccessLog.fecha_pago, models.AccessLog.fecha_hora) >= start_date)
    if end_date: q_logs = q_logs.filter(func.coalesce(models.AccessLog.fecha_pago, models.AccessLog.fecha_hora) <= end_date)
    logs = q_logs.all()

    # Obtener reservas
    q_res = db.query(models.Reservation).filter(models.Reservation.estado_pago == "Pagado")
    if sucursal: q_res = q_res.filter(models.Reservation.sucursal_nombre == sucursal)
    if start_date: q_res = q_res.filter(models.Reservation.fecha_inicio >= start_date)
    if end_date: q_res = q_res.filter(models.Reservation.fecha_inicio <= end_date)
    reservas = q_res.all()

    # Unificar formato
    history = []
    for l in logs:
        history.append({
            "id": f"L{l.id}",
            "fecha_pago": l.fecha_pago or l.fecha_hora,
            "patente_detectada": l.patente_detectada,
            "costo_estadia": l.costo_estadia,
            "tipo": "Estadía"
        })
    
    for r in reservas:
        history.append({
            "id": f"R{r.id}",
            "fecha_pago": r.fecha_inicio,
            "patente_detectada": r.patente,
            "costo_estadia": r.monto_total,
            "tipo": "Reserva"
        })

    history.sort(key=lambda x: x["fecha_pago"], reverse=True)
    return history

# --- AUDITORÍA DE ACCESOS ---

@router.get("/access")
def get_reports_access(patente: str = None, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """Consulta el historial de eventos ALPR. Aislamiento por sede."""
    q = db.query(models.AccessLog)
    
    if staff.rol != "admin":
        q = q.filter(models.AccessLog.sucursal == staff.sucursal)
        
    if patente: q = q.filter(models.AccessLog.patente_detectada.like(f"%{patente.upper()}%"))
    return q.order_by(models.AccessLog.id.desc()).all()
