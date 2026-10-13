from sqlalchemy import func, or_
from sqlalchemy.orm import Session

import models
from repositories.branch_repository import BranchRepository

#--- REPOSITORIO DE TICKETS DE CANJE (REDEMPTION) ---


class RedemptionRepository:
    @staticmethod
    def redemption_sucursal_clause(db: Session, sucursal):
        """CLÁUSULA DE FILTRADO DE REDEMPTION TICKET POR SUCURSAL.

        Camino principal por `sucursal_id` (migración por id): se resuelve el id
        de la sede y se empareja el ticket de esa sede o los globales (id NULL).
        Fallback legacy por nombre cuando la sede no existe (datos de prueba con
        nombres sin rama real) para preservar el comportamiento histórico.
        """
        id_col = models.RedemptionTicket.sucursal_id
        col = models.RedemptionTicket.sucursal
        if not sucursal:
            return or_(col == None, col == '')
        branch_id = BranchRepository.get_id_by_name(db, sucursal)
        if branch_id:
            # GLOBAL = nombre NULL (no id NULL: un ticket con nombre cuya sede no
            # existe mantiene id NULL sin ser global).
            return or_(col == None, id_col == branch_id)
        norm_col = func.trim(func.replace(func.lower(col), 'autopass ', ''))
        norm_param = func.trim(func.replace(func.lower(func.trim(sucursal)), 'autopass ', ''))
        return or_(col == sucursal, col == None, norm_col == norm_param)

    @staticmethod
    def list_discounts_by_user(db: Session, user_id: int, sucursal: str = None) -> list:
        """DESCUENTOS DE RESERVA (%) VIGENTES DE UN USUARIO, OPCIONALMENTE FILTRADOS POR SUCURSAL."""
        q = db.query(models.RedemptionTicket).filter(
            models.RedemptionTicket.user_id == user_id,
            models.RedemptionTicket.tipo_canje == "descuento_reserva",
            models.RedemptionTicket.estado == "VIGENTE"
        )
        if sucursal:
            q = q.filter(RedemptionRepository.redemption_sucursal_clause(db, sucursal))
        return q.order_by(models.RedemptionTicket.id.desc()).all()

    @staticmethod
    def get_by_user(db: Session, user_id: int) -> list:
        """TICKETS DE CANJE DE UN USUARIO, MAS RECIENTES PRIMERO."""
        return (
            db.query(models.RedemptionTicket)
            .filter(models.RedemptionTicket.user_id == user_id)
            .order_by(models.RedemptionTicket.id.desc())
            .all()
        )

    @staticmethod
    def get_by_id_and_user(db: Session, ticket_id: int, user_id: int) -> models.RedemptionTicket:
        """TICKET DE CANJE POR IDENTIFICADOR UNICO PERTENECIENTE A UN USUARIO."""
        return db.query(models.RedemptionTicket).filter(
            models.RedemptionTicket.id == ticket_id,
            models.RedemptionTicket.user_id == user_id
        ).first()

    @staticmethod
    def get_valid_discount(db: Session, redemption_ticket_id: int, user_id: int, sucursal: str = None) -> models.RedemptionTicket:
        """TICKET DE DESCUENTO VIGENTE Y VALIDO PARA EL USUARIO Y SUCURSAL."""
        if not redemption_ticket_id:
            return None
        return (
            db.query(models.RedemptionTicket)
            .filter(
                models.RedemptionTicket.id == redemption_ticket_id,
                models.RedemptionTicket.user_id == user_id,
                models.RedemptionTicket.tipo_canje == "descuento_reserva",
                models.RedemptionTicket.estado == "VIGENTE",
                RedemptionRepository.redemption_sucursal_clause(db, sucursal)
            )
            .first()
        )

    @staticmethod
    def get_used_discount_for_reserva(db: Session, reserva_id: int) -> models.RedemptionTicket:
        """TICKET DE DESCUENTO APLICADO (USADO) A UNA RESERVA."""
        return (
            db.query(models.RedemptionTicket)
            .filter(
                models.RedemptionTicket.reserva_id == reserva_id,
                models.RedemptionTicket.tipo_canje == "descuento_reserva",
                models.RedemptionTicket.estado == "USADO"
            )
            .first()
        )

    @staticmethod
    def unlink_promotion(db: Session, promo_id: int) -> int:
        """DESASOCIA LOS TICKETS DE CANJE DE UNA PROMOCION (promotion_id = NULL) ANTES DE BORRARLA."""
        updated = (
            db.query(models.RedemptionTicket)
            .filter(models.RedemptionTicket.promotion_id == promo_id)
            .update({models.RedemptionTicket.promotion_id: None})
        )
        db.commit()
        return updated