from sqlalchemy import or_, false
from sqlalchemy.orm import Session

import models
from repositories.branch_repository import BranchRepository

#--- REPOSITORIO DE PROMOCIONES (BENEFICIOS DE FIDELIZACION) ---


class PromotionRepository:
    @staticmethod
    def _sucursal_predicate(db: Session, sucursal: str, include_global: bool = False, organization_id=None):
        """PREDICADO SQL DE PROMOCION POR `sucursal_id`. Con include_global agrega las globales.

        Si la sucursal no existe, no matchea promos de sede (no se hereda nada)."""
        if not sucursal:
            return None
        branch_id = BranchRepository.get_id_by_name(db, sucursal, organization_id)
        branch_cond = false() if branch_id is None else models.Promotion.sucursal_id == branch_id
        if include_global:
            return or_(branch_cond, models.Promotion.sucursal_id.is_(None))
        return branch_cond

    @staticmethod
    def get_all(db: Session, sucursal: str = None, organization_id=None) -> list:
        """PROMOCIONES FILTRADAS POR SEDE EXACTA Y/O ORGANIZACION (MULTIEMPRESA)."""
        q = db.query(models.Promotion)
        if sucursal is not None:
            q = q.filter(PromotionRepository._sucursal_predicate(db, sucursal, organization_id=organization_id))
        if organization_id is not None:
            q = q.filter(models.Promotion.organization_id == organization_id)
        return q.all()

    @staticmethod
    def get_active(db: Session, sucursal: str = None, organization_id=None) -> list:
        """PROMOCIONES ACTIVAS; SI SE PASA UNA SUCURSAL INCLUYE TAMBIEN LAS GLOBALES."""
        q = db.query(models.Promotion).filter(models.Promotion.activa == True)
        if sucursal:
            q = q.filter(PromotionRepository._sucursal_predicate(db, sucursal, include_global=True, organization_id=organization_id))
        if organization_id is not None:
            q = q.filter(models.Promotion.organization_id == organization_id)
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