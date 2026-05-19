import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import models, auth
from database import get_db

router = APIRouter(prefix="/v1/reports", tags=["Reports & Analytics"])

# --- ANALÍTICA FINANCIERA ---

@router.get("/financial-summary")
def get_financial_summary(period: str = "total", start: str = None, end: str = None, db: Session = Depends(get_db), admin: models.User = Depends(auth.get_local_manager)):
    """Calcula el resumen de recaudación. Los locales solo ven su sede."""
    q_base = db.query(func.sum(models.AccessLog.costo_estadia)).filter(models.AccessLog.pago_confirmado == True)
    q_count = db.query(models.AccessLog).filter(models.AccessLog.pago_confirmado == True, models.AccessLog.costo_estadia > 0)
    
    # Aislamiento por sede
    if admin.rol != "admin":
        q_base = q_base.filter(models.AccessLog.sucursal == admin.sucursal)
        q_count = q_count.filter(models.AccessLog.sucursal == admin.sucursal)
        
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
        
    if start_date:
        q_base = q_base.filter(models.AccessLog.fecha_hora >= start_date)
        q_count = q_count.filter(models.AccessLog.fecha_hora >= start_date)
    if end_date:
        q_base = q_base.filter(models.AccessLog.fecha_hora <= end_date)
        q_count = q_count.filter(models.AccessLog.fecha_hora <= end_date)

    total = q_base.scalar() or 0.0
    cantidad = q_count.count()
    
    return {
        "total_recaudado": round(float(total), 2), 
        "cantidad_pagos": cantidad, 
        "ticket_promedio": round(float(total)/cantidad, 2) if cantidad > 0 else 0
    }

@router.get("/payment-history")
def get_payment_history(period: str = "total", start: str = None, end: str = None, db: Session = Depends(get_db), admin: models.User = Depends(auth.get_local_manager)):
    """Lista el historial de transacciones. Aislamiento por sede."""
    q = db.query(models.AccessLog).filter(models.AccessLog.pago_confirmado == True, models.AccessLog.costo_estadia > 0)
    
    if admin.rol != "admin":
        q = q.filter(models.AccessLog.sucursal == admin.sucursal)
        
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
        
    if start_date: q = q.filter(models.AccessLog.fecha_hora >= start_date)
    if end_date: q = q.filter(models.AccessLog.fecha_hora <= end_date)

    return q.order_by(models.AccessLog.id.desc()).all()

# --- AUDITORÍA DE ACCESOS ---

@router.get("/access")
def get_reports_access(patente: str = None, db: Session = Depends(get_db), staff: models.User = Depends(auth.get_operational_user)):
    """Consulta el historial de eventos ALPR. Aislamiento por sede."""
    q = db.query(models.AccessLog)
    
    if staff.rol != "admin":
        q = q.filter(models.AccessLog.sucursal == staff.sucursal)
        
    if patente: q = q.filter(models.AccessLog.patente_detectada.like(f"%{patente.upper()}%"))
    return q.order_by(models.AccessLog.id.desc()).all()
