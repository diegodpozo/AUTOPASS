from sqlalchemy import func, or_
from sqlalchemy.orm import Session

import models

#--- REPOSITORIO DE TICKETS DE CANJE (REDEMPTION) ---


class RedemptionRepository:
    @staticmethod
    def redemption_sucursal_clause(sucursal):
        """CLÁUSULA DE FILTRADO DE REDEMPTION TICKET POR SUCURSAL.
        Acepta el ticket global (sucursal NULL), igualdad exacta o igualdad normalizada
        (sin prefijo 'AUTOPASS ', sin espacios extra y sin diferenciar mayúsculas),
        para tolerar datos legados donde algunas sucursales se guardaron con prefijo."""
        col = models.RedemptionTicket.sucursal
        if not sucursal:
            return or_(col == None, col == '')
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
            q = q.filter(RedemptionRepository.redemption_sucursal_clause(sucursal))
        return q.order_by(models.RedemptionTicket.id.desc()).all()

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
                RedemptionRepository.redemption_sucursal_clause(sucursal)
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