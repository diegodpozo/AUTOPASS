from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from core.database import get_db
from core.security import get_operational_user
from services.billing_service import BillingService

router = APIRouter()

@router.get("/parking/branches", response_model=List[schemas.BranchPublicResponse])
def list_public_branches(db: Session = Depends(get_db)):
    """Retorna la lista de sucursales activas con su ocupación real para el mapa público."""
    branches = db.query(models.ParkingBranch).filter(models.ParkingBranch.activa == True).all()
    
    res = []
    for b in branches:
        aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == b.nombre).first()
        res.append({
            "id": b.id,
            "nombre": b.nombre,
            "direccion": b.direccion,
            "telefono": b.telefono,
            "horario": b.horario,
            "is_24h": b.is_24h,
            "logo_url": b.logo_url,
            "activa": b.activa,
            "latitude": b.latitude,
            "longitude": b.longitude,
            "ocupacion_actual": aforo.ocupacion_actual if aforo else 0,
            "capacidad_total": aforo.capacidad_total if aforo else 20
        })
    return res

@router.get("/parking/status", response_model=schemas.ParkingStatus)
def get_parking_status(db: Session = Depends(get_db), user: models.User = Depends(get_operational_user)):
    """Retorna la disponibilidad actual de plazas. Aislamiento por sede."""
    sucursal = user.sucursal if user.rol != "admin" else None
    
    a = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
    if not a: 
        return {"capacidad_total": 20, "ocupacion_actual": 0, "disponibilidad": 20}
    return {
        "capacidad_total": a.capacidad_total, 
        "ocupacion_actual": a.ocupacion_actual, 
        "disponibilidad": a.capacidad_total - a.ocupacion_actual
    }

@router.get("/parking/current-occupancy")
def current_occupancy(db: Session = Depends(get_db), user: models.User = Depends(get_operational_user)):
    """Lista vehículos estacionados en la sede del usuario con deuda calculada."""
    sucursal = user.sucursal if user.rol != "admin" else None
    
    q = db.query(models.AccessLog).filter(models.AccessLog.tipo_evento == "ENTRADA")
    if sucursal:
        q = q.filter(models.AccessLog.sucursal == sucursal)
        
    entradas = q.all()
    res = []
    for e in entradas:
        tiene_salida = db.query(models.AccessLog).filter(
            models.AccessLog.patente_detectada == e.patente_detectada, 
            models.AccessLog.tipo_evento == "SALIDA", 
            models.AccessLog.fecha_hora > e.fecha_hora,
            models.AccessLog.sucursal == e.sucursal
        ).first()
        
        if not tiene_salida:
            deuda = 0.0 if e.pago_confirmado else BillingService.calculate_debt(e.fecha_hora, db)
            res.append({
                "patente": e.patente_detectada, 
                "ingreso": e.fecha_hora, 
                "deuda": deuda, 
                "ya_pago": e.pago_confirmado, 
                "es_reserva": e.reserva_id is not None,
                "sucursal": e.sucursal
            })
    return res
