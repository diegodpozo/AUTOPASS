from sqlalchemy import or_
from sqlalchemy.orm import Session

import models

#--- REPOSITORIO DE PROMOCIONES (BENEFICIOS DE FIDELIZACION) ---


class PromotionRepository:
    @staticmethod
    def get_all(db: Session, sucursal: str = None) -> list:
        """OBTIENE TODAS LAS PROMOCIONES, OPCIONALMENTE FILTRADAS POR SUCURSAL EXACTA."""
        q = db.query(models.Promotion)
        if sucursal is not None:
            q = q.filter(models.Promotion.sucursal == sucursal)
        return q.all()

    @staticmethod
    def get_active(db: Session, sucursal: str = None) -> list:
        """PROMOCIONES ACTIVAS; SI SE PASA UNA SUCURSAL INCLUYE TAMBIEN LAS GLOBALES."""
        q = db.query(models.Promotion).filter(models.Promotion.activa == True)
        if sucursal:
            q = q.filter(or_(models.Promotion.sucursal == sucursal, models.Promotion.sucursal == None))
        return q.all()

    @staticmethod
    def get_by_id(db: Session, promo_id: int) -> models.Promotion:
        """OBTIENE UNA PROMOCION POR SU IDENTIFICADOR UNICO."""
        return db.query(models.Promotion).filter(models.Promotion.id == promo_id).first()

    @staticmethod
    def get_active_by_id(db: Session, promo_id: int) -> models.Promotion:
        """OBTIENE UNA PROMOCION ACTIVA POR SU IDENTIFICADOR UNICO."""
        return db.query(models.Promotion).filter(
            models.Promotion.id == promo_id,
            models.Promotion.activa == True
        ).first()