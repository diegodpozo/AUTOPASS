import datetime
from decimal import Decimal
import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session
import models
from core.config import settings
from core.db_lock import bloqueo_transaccional, clave_reserva, clave_usuario
from core.logger import get_logger
from core.normalize import normalize_plate
from models.enums import PaymentStatus, ReservationStatus
from models.types import to_decimal, to_money
from services.billing_service import BillingService
from repositories.access_log_repository import AccessRepository
from repositories.mercadopago_repository import MercadoPagoPaymentRepository
from repositories.reservation_repository import ReservationRepository
from repositories.user_repository import UserRepository

logger = get_logger("MercadoPago")

MP_API_BASE = "https://api.mercadopago.com"

_APROBADO = "APROBADO"
_PENDIENTE = "PENDIENTE"
_FALLIDO = "FALLIDO"
_CANCELADO = "CANCELADO"

# STATUS DE MERCADO PAGO CONSIDERADOS COMO FALLIDOS/CANCELADOS
_ESTADOS_NO_COBRABLES = ("rejected", "cancelled", "refunded", "charged_back")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def _mp_request(method: str, path: str, payload: dict = None):
    """EJECUTA UNA LLAMADA A LA API DE MERCADO PAGO."""
    try:
        resp = requests.request(
            method,
            f"{MP_API_BASE}{path}",
            headers=_headers(),
            json=payload,
            timeout=15,
        )
    except requests.RequestException as e:
        logger.error(f"[MP] Error de red en {path}: {e}")
        raise HTTPException(status_code=502, detail="No se pudo conectar con Mercado Pago. Intentá de nuevo.")
    if resp.status_code >= 400:
        error_code = resp.json().get("message", "") if resp.headers.get("content-type", "").startswith("application/json") else ""
        logger.error(f"[MP] Error {resp.status_code} en {path}: {error_code or 'solicitud rechazada'}")
        raise HTTPException(
            status_code=502,
            detail="Mercado Pago rechazó la operación. Verificá que las credenciales de prueba estén configuradas en el .env.",
        )
    return resp.json()


def _generar_external_reference(pago: "models.MercadoPagoPayment") -> str:
    import uuid
    return f"AP-{pago.tipo.upper()}-{pago.id}-{uuid.uuid4().hex[:8]}"


def _get_payment_from_mp(payment_id, external_reference=None):
    """CONSULTA EL PAGO EN MERCADO PAGO POR id O POR external_reference."""
    if payment_id:
        try:
            return _mp_request("GET", f"/v1/payments/{payment_id}")
        except HTTPException:
            return None
    if external_reference:
        try:
            data = _mp_request("GET", f"/v1/payments/search", {"external_reference": external_reference})
            results = data.get("results") or []
            return results[0] if results else None
        except HTTPException:
            return None
    return None


def _monto_reserva_con_descuento(db: Session, user: "models.User", res: "models.Reservation", redemption_ticket_id):
    """CALCULA EL MONTO A COBRAR POR UNA RESERVA APLICANDO DESCUENTO POR CANJE SI CORRESPONDE.
    Devuelve (monto_a_cobrar, ticket_redencion)."""
    if not redemption_ticket_id:
        return res.monto_total, None
    from services.reservation_service import ReservationService
    ticket = ReservationService.validate_redemption_ticket(db, user.id, redemption_ticket_id, res.sucursal_nombre)
    porc = ticket.valor_descuento or 0
    descuento_factor = Decimal(100 - porc) / Decimal(100)
    return to_money(res.monto_total * descuento_factor), ticket



def create_payment(db: Session, user: "models.User", data) -> dict:
    """CREA UNA PREFERENCIA DE CHECKOUT PRO Y REGISTRA LA INTENCION DE PAGO."""
    if not settings.MP_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Mercado Pago no está configurado todavía. Configurá MP_ACCESS_TOKEN en el .env.",
        )

    title, desc, monto, tipo, reserva, access_log = None, None, None, data.tipo, None, None
    redemption_ticket_id = None

    if tipo == "reserva":
        if not data.reserva_id:
            raise HTTPException(status_code=400, detail="Falta reserva_id")
        res = ReservationRepository.get_by_user_and_id(db, user.id, data.reserva_id)
        if not res:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        if res.estado_reserva in [ReservationStatus.CANCELADA, ReservationStatus.COMPLETADA]:
            raise HTTPException(status_code=400, detail=f"No se puede abonar una reserva en estado '{res.estado_reserva}'")
        if res.estado_pago == PaymentStatus.PAGADO:
            raise HTTPException(status_code=400, detail="La reserva ya ha sido abonada")
        monto, _ = _monto_reserva_con_descuento(db, user, res, data.redemption_ticket_id)
        redemption_ticket_id = data.redemption_ticket_id
        title = f"Reserva AutoPass # {res.id}"
        desc = f"Estacionamiento {res.sucursal_nombre} - Patente {res.patente} ({res.tipo_estadia})"
        reserva = res
    elif tipo == "estadia":
        if not data.access_log_id:
            raise HTTPException(status_code=400, detail="Falta access_log_id")
        log = AccessRepository.get_by_id(db, data.access_log_id)
        if not log:
            raise HTTPException(status_code=404, detail="Estadía no encontrada")
        user_plates = [normalize_plate(v.patente) for v in user.vehicles]
        if normalize_plate(log.patente_detectada) not in user_plates:
            raise HTTPException(status_code=403, detail="La estadía no pertenece a un vehículo del usuario")
        if log.pago_confirmado:
            raise HTTPException(status_code=400, detail="La estadía ya ha sido abonada")
        deuda = BillingService.calculate_debt(
            log.fecha_hora, db, sucursal=log.sucursal, tipo_vehiculo=log.tipo_vehiculo or "Auto"
        )
        if deuda is None:
            raise HTTPException(status_code=409, detail="La sucursal no tiene tarifario configurado. No se puede cobrar la estadía.")
        monto = to_money(deuda)
        title = f"Estadía AutoPass - Patente {log.patente_detectada}"
        desc = f"Sucursal {log.sucursal or '-'} - Ingreso {log.fecha_hora}"
        access_log = log
    else:
        raise HTTPException(status_code=400, detail="Tipo de pago inválido")

    if monto <= 0:
        raise HTTPException(status_code=400, detail="El monto a cobrar debe ser mayor a cero")

    # REGISTRAR INTENCION DE PAGO
    pago = models.MercadoPagoPayment(
        user_id=user.id,
        tipo=tipo,
        reserva_id=reserva.id if reserva else None,
        access_log_id=access_log.id if access_log else None,
        redemption_ticket_id=redemption_ticket_id,
        patente=(reserva.patente if reserva else access_log.patente_detectada if access_log else None),
        monto=monto,
        estado=_PENDIENTE,
        fecha_creacion=datetime.datetime.now().isoformat(),
    )
    db.add(pago)
    db.flush()
    pago.external_reference = _generar_external_reference(pago)
    db.commit()
    db.refresh(pago)

    base = settings.BASE_URL.rstrip("/")
    if not base.startswith("https://"):
        raise HTTPException(
            status_code=400,
            detail="Mercado Pago exige que BASE_URL use https:// para los back_urls. "
                   "Configurá BASE_URL=https://... en el .env (p.ej. un túnel cloudflared: https://xxx.trycloudflare.com).",
        )
    now = datetime.datetime.now(datetime.timezone.utc)
    exp_from = now.isoformat(timespec="milliseconds")
    exp_to = (now + datetime.timedelta(minutes=settings.MP_PREFERENCE_EXPIRE_MINUTES)).isoformat(timespec="milliseconds")

    preference_payload = {
        "items": [{
            "id": str(pago.id),
            "title": title,
            "description": desc,
            "quantity": 1,
            "unit_price": float(monto),
            "currency_id": "ARS",
        }],
        "payer": {"email": user.email, "name": user.nombre or "", "surname": user.apellido or ""},
        "external_reference": pago.external_reference,
        "back_urls": {
            "success": f"{base}/v1/user/mercadopago/success",
            "pending": f"{base}/v1/user/mercadopago/pending",
            "failure": f"{base}/v1/user/mercadopago/failure",
        },
        "auto_return": "approved",
        "statement_descriptor": "AUTOPASS",
        "expires": True,
        "expiration_date_from": exp_from,
        "expiration_date_to": exp_to,
    }
    if settings.MP_WEBHOOK_URL:
        preference_payload["notification_url"] = settings.MP_WEBHOOK_URL

    try:
        pref = _mp_request("POST", "/checkout/preferences", preference_payload)
    except Exception:
        logger.exception("[MP] Error creando preferencia de pago")
        pago.estado = _FALLIDO
        db.commit()
        raise

    pago.preference_id = pref.get("id")
    db.commit()

    return {
        "init_point": pref.get("init_point") or pref.get("sandbox_init_point"),
        "external_reference": pago.external_reference,
        "monto": monto,
        "preference_id": pago.preference_id,
    }


def confirm_payment(db: Session, external_reference: str, payment_id=None) -> dict:
    """VERIFICA EL PAGO EN MERCADO PAGO Y APLICA LA ACREDITACION SI FUE APROBADO.
    Es idempotente: un pago ya aplicado no se vuelve a aplicar."""
    pago = MercadoPagoPaymentRepository.get_by_external_reference(db, external_reference)
    if not pago:
        raise HTTPException(status_code=404, detail="Referencia de pago no encontrada")

    if pago.aplicado:
        return {"status": "ok", "message": "Pago ya confirmado", "aplicado": True}

    mp_payment = _get_payment_from_mp(payment_id, external_reference)
    payment_id = str(payment_id or (mp_payment or {}).get("id") or pago.payment_id or "")
    if payment_id:
        pago.payment_id = payment_id

    if mp_payment:
        mp_status = mp_payment.get("status")
        pago.mp_status = mp_status
        amount = mp_payment.get("transaction_amount")
        if mp_status == "approved":
            if amount is not None and abs(to_decimal(amount) - pago.monto) > Decimal("1.00"):
                logger.error(f"[MP] Monto no coincide: esperado {pago.monto}, recibido {amount}. No se aplica.")
                pago.estado = _FALLIDO
                db.commit()
                raise HTTPException(status_code=409, detail="El monto confirmado por Mercado Pago no coincide con la operación")
            return _aplicar_pago(db, pago, payment_id)
        if mp_status in _ESTADOS_NO_COBRABLES:
            pago.estado = _FALLIDO if mp_status in ("rejected", "refunded", "charged_back") else _CANCELADO
            db.commit()
            return {"status": "pending", "message": f"El pago no fue aprobado (estado: {mp_status})", "aplicado": False}
        # pending / in_process / otros: seguir esperando
        pago.estado = _PENDIENTE
        db.commit()
        return {"status": "pending", "message": "El pago se encuentra pendiente de acreditación", "aplicado": False}

    # Sin respuesta de MP: no aplicar. Marcar pendiente y avisar.
    db.commit()
    return {"status": "pending", "message": "No se pudo verificar el pago en Mercado Pago. Volvé a intentar.", "aplicado": False}


def _aplicar_pago(db: Session, pago: "models.MercadoPagoPayment", payment_id: str) -> dict:
    """APLICA LA ACREDITACION REAL DEL PAGO (RESERVA O ESTADIA) SIN TOCAR EL SALDO DEL USUARIO."""
    # SECCION CRITICA (FASE 2): aqui llegan los webhooks de Mercado Pago, que pueden
    # repetirse. El lock de cuenta (+ reserva, si la hay) serializa los duplicados, y
    # RE-LEEMOS el registro de pago bajo el lock: si otro webhook lo aplico mientras
    # esperabamos el turno, salimos sin acreditar (idempotencia bajo lock, R4).
    # OJO: la llamada HTTP a la API de MP NO entra aqui a proposito (puede tardar
    # hasta 15s); vive en confirm_payment, FUERA del lock.
    with bloqueo_transaccional(db, clave_reserva(pago.reserva_id), clave_usuario(pago.user_id)):
        # RE-VALIDACION BAJO LOCK (regla critica del informe): releemos solo la
        # columna de estado --sin refrescar el objeto entero-- para conservar los
        # cambios sin flush que hizo confirm_payment antes de llamarnos
        # (payment_id / mp_status / mp_payment_status).
        estado_reg = db.query(models.MercadoPagoPayment.estado).filter(models.MercadoPagoPayment.id == pago.id).scalar()
        if estado_reg == _APROBADO:
            return {"status": "ok", "message": "Pago ya confirmado", "aplicado": True}

        user = UserRepository.get_by_id(db, pago.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if pago.tipo == "reserva":
            res = ReservationRepository.get_by_id(db, pago.reserva_id)
            if not res:
                raise HTTPException(status_code=404, detail="Reserva no encontrada")
            from services.reservation_service import ReservationService
            resultado = ReservationService.pay_reservation_mp(db, user, res, pago.monto, pago.redemption_ticket_id)
        elif pago.tipo == "estadia":
            log = AccessRepository.get_by_id(db, pago.access_log_id)
            if not log:
                raise HTTPException(status_code=404, detail="Estadía no encontrada")
            from services.billing_service import BillingService
            resultado = BillingService.apply_stay_mp_payment(db, user, log, pago.monto)
        else:
            raise HTTPException(status_code=400, detail="Tipo de pago inválido")

        pago.estado = _APROBADO
        pago.mp_status = "approved"
        # CLAVE DE IDEMPOTENCIA: si no hay id de MP se guarda NULL (varios NULL no
        # colisionan en el indice unico); nunca '' porque dos '' chocarian.
        pago.payment_id = str(payment_id) if payment_id else None
        pago.fecha_confirmacion = datetime.datetime.now().isoformat()
        # El commit cierra la seccion critica: a partir de ahi el lock queda libre.
        db.commit()

    return {"status": "ok", "message": "Pago acreditado con éxito", "aplicado": True, **resultado}