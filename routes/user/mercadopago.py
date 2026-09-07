from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import models, schemas
from core.database import get_db
from core.security import get_current_user
from core.logger import get_logger
import services.mercadopago_service as mp_service

logger = get_logger("MercadoPagoRoutes")

router = APIRouter()


@router.post("/mercadopago/checkout", response_model=schemas.MercadoPagoCheckoutResponse)
def create_mp_checkout(data: schemas.MercadoPagoCheckout, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """CREA UNA PREFERENCIA DE CHECKOUT PRO PARA PAGAR UNA RESERVA O ESTADIA."""
    if current_user.is_blocked:
        raise HTTPException(status_code=403, detail="Su cuenta se encuentra bloqueada.")
    return mp_service.create_payment(db, current_user, data)


def _procesar_retorno(external_reference: str, payment_id: str):
    """Procesa el retorno del checkout y redirige al portal con el resultado."""
    from core.database import SessionLocal

    tipo = "reserva"
    mp_status = "failed"
    db = SessionLocal()
    try:
        pago = db.query(models.MercadoPagoPayment).filter(
            models.MercadoPagoPayment.external_reference == external_reference
        ).first()
        if pago:
            tipo = pago.tipo or "reserva"
        try:
            resultado = mp_service.confirm_payment(db, external_reference, payment_id=payment_id)
            mp_status = "approved" if resultado["aplicado"] else "pending"
        except HTTPException as e:
            mp_status = "failed"
            logger.warning(f"[MP] Retorno sin aplicar: {e.detail}")
    except Exception as e:
        mp_status = "failed"
        logger.error(f"[MP] Error procesando retorno: {e}")
    finally:
        db.close()

    return RedirectResponse(url=f"/perfil?mp_status={mp_status}&mp_tipo={tipo}")


@router.get("/mercadopago/success")
def mp_success(external_reference: str = None, payment_id: str = None, collection_id: str = None):
    """RETORNO DE MERCADO PAGO - PAGO EXITOSO."""
    return _procesar_retorno(external_reference, payment_id or collection_id)


@router.get("/mercadopago/pending")
def mp_pending(external_reference: str = None, payment_id: str = None, collection_id: str = None):
    """RETORNO DE MERCADO PAGO - PAGO PENDIENTE."""
    return _procesar_retorno(external_reference, payment_id or collection_id)


@router.get("/mercadopago/failure")
def mp_failure(external_reference: str = None, payment_id: str = None, collection_id: str = None):
    """RETORNO DE MERCADO PAGO - PAGO DECLINADO/CANCELADO."""
    return _procesar_retorno(external_reference, payment_id or collection_id)


@router.post("/mercadopago/webhook")
async def mp_webhook(request: Request, db: Session = Depends(get_db)):
    """WEBHOOK DE NOTIFICACIONES DE MERCADO PAGO (para producción / túnel / acceso remoto)."""
    try:
        body = await request.json()
    except Exception:
        return {"status": "ok"}

    data = body.get("data") or {}
    payment_id = data.get("id") or body.get("data_id")
    if not payment_id:
        return {"status": "ok"}

    logger.info(f"[MP] Webhook recibido: type={body.get('type')} payment_id={payment_id}")
    try:
        # BUSCAR external_reference VIA API DE MP PARA LOCALIZAR LA INTENCION
        pago_mp = mp_service._mp_request("GET", f"/v1/payments/{payment_id}")
        external_reference = pago_mp.get("external_reference")
        if not external_reference:
            logger.warning(f"[MP] Webhook sin external_reference para payment {payment_id}")
            return {"status": "ok"}
        mp_service.confirm_payment(db, external_reference, payment_id=payment_id)
    except HTTPException as e:
        logger.warning(f"[MP] Webhook no aplicado: {e.detail}")
    except Exception as e:
        logger.error(f"[MP] Error en webhook: {e}")

    return {"status": "ok"}