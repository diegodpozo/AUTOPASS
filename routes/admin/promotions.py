from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from core.database import get_db
from core.security import get_local_manager

router = APIRouter()

@router.get("/promotions", response_model=List[schemas.PromotionResponse])
def list_promotions_admin(db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """LISTA TODAS LAS PROMOCIONES. LOS LOCALES SOLO VEN LAS DE SU SEDE."""
    q = db.query(models.Promotion)
    if admin.rol != "admin":
        q = q.filter(models.Promotion.sucursal == admin.sucursal)
    
    promos = q.all()
    for p in promos:
        if p.activa is None:
            p.activa = True
            
    return promos

@router.post("/promotions")
def create_promotion(data: schemas.PromotionCreate, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """CREA UNA NUEVA PROMOCION VINCULADA A LA SEDE DEL ADMINISTRADOR."""
    sucursal = admin.sucursal if admin.rol != "admin" else data.sucursal
    
    new_promo = models.Promotion(
        titulo=data.titulo,
        descripcion=data.descripcion,
        costo_puntos=data.costo_puntos,
        icono=data.icono,
        categoria=data.categoria,
        sucursal=sucursal
    )
    db.add(new_promo)
    db.commit()
    return {"status": "ok", "message": f"Promoción '{data.titulo}' creada para {sucursal or 'Global'}"}

@router.post("/promotions/{promo_id}/toggle")
def toggle_promotion(promo_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ACTIVA O DESACTIVA UNA PROMOCION."""
    promo = db.query(models.Promotion).filter(models.Promotion.id == promo_id).first()
    if not promo: raise HTTPException(status_code=404, detail="Promoción no encontrada")
    
    if admin.rol != "admin" and promo.sucursal != admin.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta promoción")
        
    promo.activa = not promo.activa
    db.commit()
    return {"status": "ok", "activa": promo.activa}

@router.delete("/promotions/{promo_id}")
def delete_promotion(promo_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ELIMINA UNA PROMOCION PERMANENTEMENTE."""
    promo = db.query(models.Promotion).filter(models.Promotion.id == promo_id).first()
    if not promo: raise HTTPException(status_code=404, detail="Promoción no encontrada")
    
    if admin.rol != "admin" and promo.sucursal != admin.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre esta promoción")
        
    db.delete(promo)
    db.commit()
    return {"status": "ok"}
