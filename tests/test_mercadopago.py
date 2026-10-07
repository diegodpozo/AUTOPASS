import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Vehicle, Reservation, AccessLog, MercadoPagoPayment, Settings
from models.enums import ReservationStatus, PaymentStatus
from services import mercadopago_service as mp_service
from fastapi import HTTPException

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def _crear_usuario(db, saldo=5000.0):
    user = User(email=f"user{uuid.uuid4().hex[:10]}@test.com", nombre="Test", apellido="User",
                password_hash="x", rol="user", saldo=saldo, puntos_acumulados=0)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class CheckoutSchema:
    """Stub de schemas.MercadoPagoCheckout para aislar el servicio."""
    def __init__(self, tipo="reserva", reserva_id=None, access_log_id=None, redemption_ticket_id=None):
        self.tipo = tipo
        self.reserva_id = reserva_id
        self.access_log_id = access_log_id
        self.redemption_ticket_id = redemption_ticket_id


def test_create_payment_require_https_base_url(db, monkeypatch):
    """MP exige https:// en los back_urls: BASE_URL http debe fallar con aviso claro."""
    monkeypatch.setattr(mp_service.settings, "MP_ACCESS_TOKEN", "TEST-TOKEN")
    monkeypatch.setattr(mp_service.settings, "BASE_URL", "http://localhost:8000")
    user = _crear_usuario(db)
    res = Reservation(user_id=user.id, patente="ABC123", fecha_inicio="2026-09-02T10:00:00",
                      fecha_fin="2026-09-02T12:00:00", monto_total=3000.0,
                      estado_pago=PaymentStatus.PENDIENTE, estado_reserva=ReservationStatus.PENDIENTE,
                      tipo_estadia="hora", sucursal_nombre="AUTOPASS Central")
    db.add(res)
    db.commit()
    db.refresh(res)
    data = CheckoutSchema(tipo="reserva", reserva_id=res.id)
    with pytest.raises(HTTPException) as exc:
        mp_service.create_payment(db, user, data)
    assert exc.value.status_code == 400
    assert "https" in exc.value.detail


def test_create_payment_require_credentials(db, monkeypatch):
    """Sin credenciales configuradas, se rechaza con 503."""
    monkeypatch.setattr(mp_service.settings, "MP_ACCESS_TOKEN", "")
    user = _crear_usuario(db)
    data = CheckoutSchema(tipo="reserva", reserva_id=1)
    with pytest.raises(HTTPException) as exc:
        mp_service.create_payment(db, user, data)
    assert exc.value.status_code == 503


def test_create_payment_estadia_creates_intent(db, monkeypatch):
    """Con credenciales y BASE_URL https, el checkout de estadía crea la intención y devuelve init_point."""
    monkeypatch.setattr(mp_service.settings, "MP_ACCESS_TOKEN", "TEST-TOKEN")
    monkeypatch.setattr(mp_service.settings, "BASE_URL", "https://localhost:8000")
    user = _crear_usuario(db)

    db.add(Vehicle(user_id=user.id, patente="ABC123", marca_modelo="Test Auto", tipo="Auto"))
    db.commit()

    db.add(Settings(clave="precio_hora", valor=1500.0, sucursal=None))
    db.add(Settings(clave="precio_30min", valor=750.0, sucursal=None))
    db.commit()

    log = AccessLog(patente_detectada="ABC123", tipo_evento="ENTRADA",
                    tipo_vehiculo="Auto", fecha_hora="2026-09-01T10:00:00", pago_confirmado=False)
    db.add(log)
    db.commit()
    db.refresh(log)

    def fake_mp_request(method, path, payload=None):
        assert path == "/checkout/preferences"
        return {"id": "PREF-1", "init_point": "https://sandbox.mercadopago.com.ar/checkout/v1/redirect?pref_id=PREF-1"}

    monkeypatch.setattr(mp_service, "_mp_request", fake_mp_request)

    data = CheckoutSchema(tipo="estadia", access_log_id=log.id)
    result = mp_service.create_payment(db, user, data)
    assert result["init_point"]
    assert result["monto"] > 0
    assert result["external_reference"].startswith("AP-ESTADIA-")

    pago = db.query(MercadoPagoPayment).filter(
        MercadoPagoPayment.external_reference == result["external_reference"]
    ).first()
    assert pago is not None
    assert pago.estado == "PENDIENTE"
    assert pago.tipo == "estadia"
    assert pago.payment_id is None


def test_confirm_reserva_approved_no_saldo_deduction(db, monkeypatch):
    """La confirmación de una reserva paga NO descuenta saldo y acredita puntos."""
    monkeypatch.setattr(mp_service.settings, "MP_ACCESS_TOKEN", "TEST-TOKEN")

    user = _crear_usuario(db, saldo=5000.0)

    res = Reservation(user_id=user.id, patente="ABC123", fecha_inicio="2026-09-02T10:00:00",
                      fecha_fin="2026-09-02T12:00:00", monto_total=3000.0,
                      estado_pago=PaymentStatus.PENDIENTE, estado_reserva=ReservationStatus.PENDIENTE,
                      tipo_estadia="hora", sucursal_nombre="AUTOPASS Central")
    db.add(res)
    db.commit()
    db.refresh(res)

    pago = MercadoPagoPayment(user_id=user.id, tipo="reserva", reserva_id=res.id,
                              patente="ABC123", monto=3000.0, external_reference="AP-RES-999",
                              preference_id="PREF-1", estado="PENDIENTE")
    db.add(pago)
    db.commit()

    # SIMULAR ESTADO APROBADO EN MP
    def fake_get_payment(payment_id, external_reference=None):
        return {"id": "PAY-123", "status": "approved", "transaction_amount": 3000.0}

    monkeypatch.setattr(mp_service, "_get_payment_from_mp", fake_get_payment)

    result = mp_service.confirm_payment(db, "AP-RES-999", payment_id="PAY-123")
    assert result["status"] == "ok"
    assert result["aplicado"] is True

    db.refresh(res)
    db.refresh(user)
    assert res.estado_pago == PaymentStatus.PAGADO
    assert user.saldo == 5000.0  # NO SE DESCONTÓ SALDO
    assert user.puntos_acumulados == 30  # 10 pts / $1000

    pago_actualizado = db.query(MercadoPagoPayment).filter(
        MercadoPagoPayment.external_reference == "AP-RES-999"
    ).first()
    assert pago_actualizado.aplicado is True
    assert pago_actualizado.payment_id == "PAY-123"


def test_confirm_payment_idempotent(db, monkeypatch):
    """Una vez aplicado, una segunda confirmación no duplica puntos ni re-aplica."""
    monkeypatch.setattr(mp_service.settings, "MP_ACCESS_TOKEN", "TEST-TOKEN")

    user = _crear_usuario(db)
    res = Reservation(user_id=user.id, patente="ABC123", fecha_inicio="2026-09-02T10:00:00",
                      fecha_fin="2026-09-02T12:00:00", monto_total=1000.0,
                      estado_pago=PaymentStatus.PENDIENTE, estado_reserva=ReservationStatus.PENDIENTE,
                      tipo_estadia="hora", sucursal_nombre="AUTOPASS Central")
    db.add(res)
    db.commit()
    db.refresh(res)

    pago = MercadoPagoPayment(user_id=user.id, tipo="reserva", reserva_id=res.id,
                              patente="ABC123", monto=1000.0, external_reference="AP-RES-888",
                              preference_id="PREF-2", estado="PENDIENTE")
    db.add(pago)
    db.commit()

    def fake_get_payment(payment_id, external_reference=None):
        return {"id": "PAY-2", "status": "approved", "transaction_amount": 1000.0}

    monkeypatch.setattr(mp_service, "_get_payment_from_mp", fake_get_payment)

    mp_service.confirm_payment(db, "AP-RES-888", payment_id="PAY-2")
    segundo = mp_service.confirm_payment(db, "AP-RES-888", payment_id="PAY-2")
    assert segundo["aplicado"] is True  # ya aplicado: no se vuelve a aplicar (pago.aplicado)

    db.refresh(user)
    assert user.puntos_acumulados == 10


def test_confirm_estadia_approved(db, monkeypatch):
    """La confirmación de una estadía la marca pagada con método MERCADOPAGO."""
    monkeypatch.setattr(mp_service.settings, "MP_ACCESS_TOKEN", "TEST-TOKEN")

    user = _crear_usuario(db)
    log = AccessLog(patente_detectada="XYZ987", tipo_evento="ENTRADA", tipo_vehiculo="Auto",
                    fecha_hora="2026-09-01T10:00:00", pago_confirmado=False, sucursal="AUTOPASS Central")
    db.add(log)
    db.commit()
    db.refresh(log)

    pago = MercadoPagoPayment(user_id=user.id, tipo="estadia", access_log_id=log.id,
                              patente="XYZ987", monto=1500.0, external_reference="AP-EST-777",
                              preference_id="PREF-3", estado="PENDIENTE")
    db.add(pago)
    db.commit()

    def fake_get_payment(payment_id, external_reference=None):
        return {"id": "PAY-3", "status": "approved", "transaction_amount": 1500.0}

    monkeypatch.setattr(mp_service, "_get_payment_from_mp", fake_get_payment)

    result = mp_service.confirm_payment(db, "AP-EST-777", payment_id="PAY-3")
    assert result["aplicado"] is True

    db.refresh(log)
    assert log.pago_confirmado is True
    assert log.metodo_pago == "MERCADOPAGO"
    assert log.costo_estadia == 1500.0


def test_confirm_payment_rejected_not_applied(db, monkeypatch):
    """Un pago rechazado por MP no aplica la acreditación."""
    monkeypatch.setattr(mp_service.settings, "MP_ACCESS_TOKEN", "TEST-TOKEN")

    user = _crear_usuario(db)
    pago = MercadoPagoPayment(user_id=user.id, tipo="estadia", monto=1500.0,
                              external_reference="AP-EST-666", preference_id="PREF-4", estado="PENDIENTE")
    db.add(pago)
    db.commit()

    def fake_get_payment(payment_id, external_reference=None):
        return {"id": "PAY-4", "status": "rejected", "transaction_amount": 1500.0}

    monkeypatch.setattr(mp_service, "_get_payment_from_mp", fake_get_payment)

    result = mp_service.confirm_payment(db, "AP-EST-666", payment_id="PAY-4")
    assert result["aplicado"] is False

    db.refresh(pago)
    assert pago.estado == "FALLIDO"