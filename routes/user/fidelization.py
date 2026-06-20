import datetime
import math
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import models, schemas
from core.database import get_db
from core.security import get_current_user

router = APIRouter()

@router.get("/promotions", response_model=List[schemas.PromotionResponse])
def get_promotions(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """LISTA LAS PROMOCIONES Y BENEFICIOS VIGENTES FILTRADOS POR LA SEDE DEL USUARIO."""
    from sqlalchemy import or_
    q = db.query(models.Promotion).filter(models.Promotion.activa == True)
    
    if current_user.sucursal:
        q = q.filter(or_(models.Promotion.sucursal == current_user.sucursal, models.Promotion.sucursal == None))
        
    return q.all()

@router.post("/redeem/{promo_id}")
def redeem_points(promo_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """PROCESA EL CANJE DE PUNTOS POR UN BENEFICIO DEL CATALOGO."""
    promo = db.query(models.Promotion).filter(models.Promotion.id == promo_id, models.Promotion.activa == True).first()
    if not promo: raise HTTPException(status_code=404, detail="Promoción no encontrada")
    if current_user.puntos_acumulados < promo.costo_puntos: raise HTTPException(status_code=400, detail="Puntos insuficientes")
    
    current_user.puntos_acumulados -= promo.costo_puntos
    db.add(models.PointsLog(user_id=current_user.id, cantidad=-promo.costo_puntos, motivo=f"Canje: {promo.titulo}", fecha=datetime.datetime.now().isoformat()))
    db.commit()
    return {"status": "ok", "message": f"Canje exitoso: {promo.titulo}"}

@router.get("/points-history")
def get_points_history(page: int = 1, limit: int = 10, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """RETORNA EL HISTORIAL DE MOVIMIENTOS DE PUNTOS DEL USUARIO CON PAGINACION Y TOTALES."""
    query = db.query(models.PointsLog).filter(models.PointsLog.user_id == current_user.id)
    total = query.count()
    
    earned = db.query(func.sum(models.PointsLog.cantidad)).filter(
        models.PointsLog.user_id == current_user.id,
        models.PointsLog.cantidad > 0
    ).scalar() or 0
    
    redeemed = db.query(func.sum(models.PointsLog.cantidad)).filter(
        models.PointsLog.user_id == current_user.id,
        models.PointsLog.cantidad < 0
    ).scalar() or 0

    items = query.order_by(models.PointsLog.id.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if total > 0 else 1,
        "total_earned": int(earned),
        "total_redeemed": abs(int(redeemed))
    }
