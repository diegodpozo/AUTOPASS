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
        # Si tiene pisos, sumamos sus capacidades
        if b.floors:
            cap_total = sum(f.capacidad_total for f in b.floors)
            occ_total = sum(f.ocupacion_actual for f in b.floors)
            cap_motos = sum(f.capacidad_motos for f in b.floors)
            occ_motos = sum(f.ocupacion_motos for f in b.floors)
            floors_data = [schemas.FloorResponse.from_orm(f) for f in b.floors]
        else:
            aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == b.nombre).first()
            cap_total = aforo.capacidad_total if aforo else 20
            occ_total = aforo.ocupacion_actual if aforo else 0
            cap_motos = aforo.capacidad_motos if aforo else 10
            occ_motos = aforo.ocupacion_motos if aforo else 0
            floors_data = []

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
            "ocupacion_actual": occ_total,
            "capacidad_total": cap_total,
            "ocupacion_motos": occ_motos,
            "capacidad_motos": cap_motos,
            "floors": floors_data
        })
    return res

@router.get("/parking/status", response_model=schemas.ParkingStatus)
def get_parking_status(db: Session = Depends(get_db), user: models.User = Depends(get_operational_user)):
    """Retorna la disponibilidad actual de plazas. Aislamiento por sede y soporte para pisos."""
    sucursal_nombre = user.sucursal if user.rol != "admin" else None
    
    # Buscar sucursal por nombre para acceder a sus pisos
    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == sucursal_nombre).first()
    
    if branch and branch.floors:
        cap_total = sum(f.capacidad_total for f in branch.floors)
        occ_total = sum(f.ocupacion_actual for f in branch.floors)
        cap_motos = sum(f.capacidad_motos for f in branch.floors)
        occ_motos = sum(f.ocupacion_motos for f in branch.floors)
    else:
        a = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal_nombre).first()
        if not a: 
            return {
                "capacidad_total": 20, "ocupacion_actual": 0, "disponibilidad": 20,
                "capacidad_motos": 10, "ocupacion_motos": 0, "disponibilidad_motos": 10
            }
        cap_total = a.capacidad_total
        occ_total = a.ocupacion_actual
        cap_motos = a.capacidad_motos
        occ_motos = a.ocupacion_motos

    return {
        "capacidad_total": cap_total, 
        "ocupacion_actual": occ_total, 
        "capacidad_motos": cap_motos,
        "ocupacion_motos": occ_motos,
        "disponibilidad": cap_total - occ_total,
        "disponibilidad_motos": cap_motos - occ_motos
    }

@router.get("/parking/current-occupancy")
def current_occupancy(db: Session = Depends(get_db), user: models.User = Depends(get_operational_user)):
    """Lista vehículos estacionados en la sede del usuario con deuda calculada. Optimizado para unicidad y orden."""
    sucursal = user.sucursal if user.rol != "admin" else None
    
    # 1. Obtenemos las entradas más recientes por patente en la sede
    # Usamos una subconsulta para encontrar el ID máximo de ENTRADA por patente
    from sqlalchemy import func
    subq = db.query(
        models.AccessLog.patente_detectada,
        func.max(models.AccessLog.id).label("max_id")
    ).filter(models.AccessLog.tipo_evento == "ENTRADA")
    
    if sucursal:
        subq = subq.filter(models.AccessLog.sucursal == sucursal)
    
    subq = subq.group_by(models.AccessLog.patente_detectada).subquery()
    
    # 2. Consultamos los detalles de esas entradas
    entradas = db.query(models.AccessLog).join(
        subq, models.AccessLog.id == subq.c.max_id
    ).order_by(models.AccessLog.fecha_hora.desc()).all()
        
    res = []
    for e in entradas:
        # 3. Verificamos si esa entrada específica ya tiene una salida posterior
        tiene_salida = db.query(models.AccessLog.id).filter(
            models.AccessLog.patente_detectada == e.patente_detectada, 
            models.AccessLog.tipo_evento == "SALIDA", 
            models.AccessLog.fecha_hora > e.fecha_hora,
            models.AccessLog.sucursal == e.sucursal
        ).first()
        
        if not tiene_salida:
            # Ahora pasamos la sucursal para que el cálculo de deuda sea exacto por sede
            deuda = 0.0 if e.pago_confirmado else BillingService.calculate_debt(e.fecha_hora, db, sucursal=e.sucursal, tipo_vehiculo=e.tipo_vehiculo)
            
            floor_name = None
            if e.floor:
                floor_name = e.floor.nombre

            res.append({
                "patente": e.patente_detectada, 
                "tipo_vehiculo": e.tipo_vehiculo,
                "ingreso": e.fecha_hora, 
                "deuda": deuda, 
                "ya_pago": e.pago_confirmado, 
                "es_reserva": e.reserva_id is not None,
                "sucursal": e.sucursal,
                "floor_nombre": floor_name
            })
    return res
