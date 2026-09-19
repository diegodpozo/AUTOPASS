from sqlalchemy.orm import Session

import models

#--- REPOSITORIO DE PAGOS MERCADO PAGO (INTENCIONES Y CONFIRMACIONES) ---


class MercadoPagoPaymentRepository:
    @staticmethod
    def get_by_external_reference(db: Session, external_reference: str) -> models.MercadoPagoPayment:
        """OBTIENE UN PAGO POR SU REFERENCIA EXTERNA (UNICA)."""
        return db.query(models.MercadoPagoPayment).filter(
            models.MercadoPagoPayment.external_reference == external_reference
        ).first()

    @staticmethod
    def get_by_id(db: Session, payment_id: int) -> models.MercadoPagoPayment:
        """OBTIENE UN PAGO POR SU IDENTIFICADOR UNICO."""
        return db.query(models.MercadoPagoPayment).filter(
            models.MercadoPagoPayment.id == payment_id
        ).first()