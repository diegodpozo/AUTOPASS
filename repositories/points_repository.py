from sqlalchemy import func
from sqlalchemy.orm import Session

import models

#--- REPOSITORIO DE HISTORIAL DE PUNTOS ---


class PointsRepository:
    @staticmethod
    def get_history(db: Session, user_id: int, page: int = 1, limit: int = 10) -> dict:
        """HISTORIAL PAGINADO DE MOVIMIENTOS DE PUNTOS CON TOTALES GANADOS/REEMBOLSADOS."""
        query = db.query(models.PointsLog).filter(models.PointsLog.user_id == user_id)
        total = query.count()
        earned = db.query(func.sum(models.PointsLog.cantidad)).filter(
            models.PointsLog.user_id == user_id, models.PointsLog.cantidad > 0
        ).scalar() or 0
        redeemed = db.query(func.sum(models.PointsLog.cantidad)).filter(
            models.PointsLog.user_id == user_id, models.PointsLog.cantidad < 0
        ).scalar() or 0
        items = query.order_by(models.PointsLog.id.desc()).offset((page - 1) * limit).limit(limit).all()
        return {"total": total, "earned": earned, "redeemed": redeemed, "items": items}