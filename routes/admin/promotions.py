from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from models.enums import UserRole
from core.database import get_db
from core.security import get_local_manager
from repositories.promotion_repository import PromotionRepository
from repositories.redemption_repository import RedemptionRepository

router = APIRouter()

@router.get("/promotions", response_model=List[schemas.PromotionResponse])
def list_promotions_admin(db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """LISTA TODAS LAS PROMOCIONES. LOS LOCALES SOLO VEN LAS DE SU SEDE."""
    promos = PromotionRepository.get_all(
        db, sucursal=admin.sucursal if admin.rol != UserRole.ADMIN else None
    )
    for p in promos:
        if p.activa is None:
            p.activa = True
            
    return promos

@router.post("/promotions")
def create_promotion(data: schemas.PromotionCreate, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """CREA UNA NUEVA PROMOCION VINCULADA A LA SEDE DEL ADMINISTRADOR."""
    sucursal = admin.sucursal if admin.rol != UserRole.ADMIN else data.sucursal
    
    new_promo = models.Promotion(
        titulo=data.titulo,
        descripcion=data.descripcion,
        costo_puntos=data.costo_puntos,
        icono=data.icono,
        categoria=data.categoria,
        sucursal=sucursal,
        tipo_canje=data.tipo_canje or "voucher",
        valor_descuento=data.valor_descuento if (data.tipo_canje == "descuento_reserva") else None,
        direccion=data.direccion,
        latitude=data.latitude,
        longitude=data.longitude,
    )
    db.add(new_promo)
    db.commit()
    return {"status": "ok", "message": f"Promoción '{data.titulo}' creada para {sucursal or 'Global'}"}

@router.post("/promotions/{promo_id}/toggle")
def toggle_promotion(promo_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ACTIVA O DESACTIVA UNA PROMOCION."""
    promo = PromotionRepository.get_by_id(db, promo_id)
    if not promo: raise HTTPException(status_code=404, detail="Promoción no encontrada")
    
    if admin.rol != UserRole.ADMIN and promo.sucursal != admin.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta promoción")
        
    promo.activa = not promo.activa
    db.commit()
    return {"status": "ok", "activa": promo.activa}

@router.put("/promotions/{promo_id}")
def update_promotion(promo_id: int, data: schemas.PromotionCreate, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ACTUALIZA UNA PROMOCION EXISTENTE. EL ADMIN GLOBAL PUEDE REASIGNAR LA SUCURSAL."""
    promo = PromotionRepository.get_by_id(db, promo_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promoción no encontrada")

    if admin.rol != UserRole.ADMIN and promo.sucursal != admin.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta promoción")

    promo.titulo = data.titulo
    promo.descripcion = data.descripcion
    promo.costo_puntos = data.costo_puntos
    promo.icono = data.icono
    promo.categoria = data.categoria
    if admin.rol == UserRole.ADMIN:
        promo.sucursal = data.sucursal
    promo.tipo_canje = data.tipo_canje or "voucher"
    promo.valor_descuento = data.valor_descuento if (data.tipo_canje == "descuento_reserva") else None
    promo.direccion = data.direccion
    promo.latitude = data.latitude
    promo.longitude = data.longitude
    db.commit()
    return {"status": "ok", "message": f"Promoción '{data.titulo}' actualizada"}

@router.delete("/promotions/{promo_id}")
def delete_promotion(promo_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ELIMINA UNA PROMOCION PERMANENTEMENTE.
    Antes de borrar desasocia los tickets de canje (FK) poniendo promotion_id = NULL,
    ya que los tickets guardan un snapshot del beneficio y no dependen de la promoción."""
    promo = PromotionRepository.get_by_id(db, promo_id)
    if not promo: raise HTTPException(status_code=404, detail="Promoción no encontrada")
    
    if admin.rol != UserRole.ADMIN and promo.sucursal != admin.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta promoción")
    
    # DESASOCIAR TICKETS DE CANJE PARA EVITAR VIOLACION DE FK (los tickets guardan snapshot)
    RedemptionRepository.unlink_promotion(db, promo_id)
    
    db.delete(promo)
    db.commit()
    return {"status": "ok"}
