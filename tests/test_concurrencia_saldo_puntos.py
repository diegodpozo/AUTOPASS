"""FASE 0 (RED) - CARRERAS DE SALDO Y PUNTOS (R3 del informe de concurrencia).

Demuestra que la carrera existe y es REPRODUCIBLE: cada test arma dos hilos con
una barrera de sincronizacion que los obliga a LEER el estado (saldo o puntos)
antes de que ninguno escriba. Esa es exactamente la ventana del bug
lectura-modificacion-escritura (`user.saldo -= monto` en Python):

    hilo A: lee saldo=100 ................................ escribe saldo=40
    hilo B: lee saldo=100 ...... (misma ventana) .......... escribe saldo=40

Resultado: se cobro una sola vez por dos pagos (dinero regalado) o se perdio
una acreditacion de puntos.

Antes de la Fase 1 estos tests FALLAN (evidencia de la carrera).
Despues de la Fase 1 PASAN: el descuento ya es un `UPDATE ... WHERE saldo >= :monto
RETURNING saldo` atomico, y la acreditacion es `SET saldo = saldo + :monto`, asi que
dos transacciones simultaneas no pueden pisarse.

Por que SQLite sobre ARCHIVO y no `sqlite://`: el resto de la suite usa SQLite en
memoria con `StaticPool`, que reutiliza UNA sola conexion para todos los hilos y por
lo tanto no permite intercalar dos transacciones. Con archivo + una sesion por hilo
cada hilo tiene su propia conexion real. Se activa WAL para que un escritor y varios
lectores convivan sin "database is locked".
"""
import datetime
import threading
import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import models
from core.database import Base
from repositories.promotion_repository import PromotionRepository
from repositories.reservation_repository import ReservationRepository
from repositories.user_repository import UserRepository
from routes.user.fidelization import redeem_points
from services.email_service import EmailService
from services.payments import ReservationPaymentsMixin


@pytest.fixture
def sesion_factory(tmp_path):
    """SQLite sobre archivo: una conexion real por hilo (no StaticPool)."""
    ruta = tmp_path / "concurrencia_saldo_puntos.db"
    motor = create_engine(
        f"sqlite:///{ruta}",
        connect_args={"check_same_thread": False, "timeout": 15},
    )

    @event.listens_for(motor, "connect")
    def _configurar_sqlite(conexion_cruda, _registro):
        cursor = conexion_cruda.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=15000")
        cursor.close()

    Base.metadata.create_all(bind=motor)
    yield sessionmaker(autocommit=False, autoflush=False, bind=motor)
    motor.dispose()


@pytest.fixture(autouse=True)
def _sin_correo_real(monkeypatch):
    """Los pagos mandan mail: en el test se reemplaza por un no-op."""
    monkeypatch.setattr(
        EmailService, "send_reservation_confirmation", lambda *a, **k: None
    )


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _usuario(S, saldo=0.0, puntos=0):
    """Crea un usuario y devuelve su id."""
    db = S()
    u = models.User(
        nombre="Carrera", apellido="Concurrente",
        dni=str(uuid.uuid4().int)[:8],
        email=f"carrera-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="x", rol="user",
        saldo=saldo, puntos_acumulados=puntos,
    )
    db.add(u)
    db.commit()
    uid = u.id
    db.close()
    return uid


def _reserva(S, user_id, monto):
    """Crea una reserva pendiente de pago y devuelve su id."""
    db = S()
    r = models.Reservation(
        user_id=user_id,
        patente="AB123CD",
        fecha_inicio=datetime.datetime.now().isoformat(),
        fecha_fin=(datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat(),
        monto_total=monto,
        monto_reembolsado=0.0,
        estado_pago="Pendiente",
        estado_reserva="Pendiente",
        tipo_estadia="hora",
        sucursal_nombre="Centro",
        sucursal_info="Centro, Calle 123",
    )
    db.add(r)
    db.commit()
    rid = r.id
    db.close()
    return rid


def _promo(S, costo_puntos=50):
    """Crea una promocion activa (voucher) y devuelve su id."""
    db = S()
    p = models.Promotion(
        titulo="Voucher Lavado", descripcion="Beneficio de prueba",
        costo_puntos=costo_puntos, sucursal="Centro", activa=True,
        tipo_canje="voucher", direccion="Calle 123",
        latitude=1.0, longitude=1.0,
    )
    db.add(p)
    db.commit()
    pid = p.id
    db.close()
    return pid


def _barrera_en(monkeypatch, clase, metodo, barrera):
    """Envuelve `clase.metodo` para que cada hilo espere en la barrera DESPUES de leer.

    Es el truco que hace determinista la carrera: cuando ambos hilos pasan la
    barrera, los dos ya leyeron el saldo/puntos viejos y todavia ninguno escribio.
    """
    original = getattr(clase, metodo)

    def envuelto(*args, **kwargs):
        resultado = original(*args, **kwargs)
        barrera.wait()
        return resultado

    monkeypatch.setattr(clase, metodo, staticmethod(envuelto))


def _correr_en_paralelo(fn, cantidad=2, timeout=30):
    """Corre `fn(i)` en `cantidad` hilos y devuelve ('ok'/`error`, valor) por hilo."""
    resultados = [None] * cantidad

    def correr(i):
        try:
            resultados[i] = ("ok", fn(i))
        except Exception as exc:  # el test clasifica el error, no lo propaga
            resultados[i] = ("error", exc)

    hilos = [threading.Thread(target=correr, args=(i,)) for i in range(cantidad)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout)
    return resultados


# ---------------------------------------------------------------------------
# R3 - saldo
# ---------------------------------------------------------------------------

def test_dos_pagos_simultaneos_no_regalan_saldo(sesion_factory, monkeypatch):
    """Saldo 100 y dos reservas de 60: SOLO UNA puede pagarse con saldo."""
    S = sesion_factory
    uid = _usuario(S, saldo=100.0)
    reservas = [_reserva(S, uid, monto=60.0), _reserva(S, uid, monto=60.0)]

    _barrera_en(monkeypatch, ReservationRepository, "get_by_user_and_id",
                threading.Barrier(2, timeout=10))

    def pagar(i):
        db = S()
        try:
            user = UserRepository.get_by_id(db, uid)
            return ReservationPaymentsMixin.pay_reservation(db, user, reservas[i])
        finally:
            db.close()

    resultados = _correr_en_paralelo(pagar)
    exitos = [r for r in resultados if r[0] == "ok"]
    fallos = [r for r in resultados if r[0] == "error"]

    assert len(exitos) == 1, (
        "los DOS pagos pasaron: con saldo 100 no se pueden pagar dos reservas de "
        f"60 (dinero regalado). Resultados: {resultados}"
    )
    assert len(fallos) == 1
    assert getattr(fallos[0][1], "status_code", None) == 400
    assert "Saldo insuficiente" in str(getattr(fallos[0][1], "detail", ""))

    db = S()
    assert UserRepository.get_by_id(db, uid).saldo == pytest.approx(40.0)
    db.close()


def test_dos_pagos_simultaneos_no_pierden_puntos(sesion_factory, monkeypatch):
    """Dos acreditaciones de 10 puntos: tienen que quedar 20 (el lost update da 10)."""
    S = sesion_factory
    uid = _usuario(S, saldo=5000.0)
    reservas = [_reserva(S, uid, monto=1000.0), _reserva(S, uid, monto=1000.0)]

    _barrera_en(monkeypatch, ReservationRepository, "get_by_user_and_id",
                threading.Barrier(2, timeout=10))

    def pagar(i):
        db = S()
        try:
            user = UserRepository.get_by_id(db, uid)
            return ReservationPaymentsMixin.pay_reservation(db, user, reservas[i])
        finally:
            db.close()

    resultados = _correr_en_paralelo(pagar)
    assert all(r[0] == "ok" for r in resultados), resultados

    db = S()
    usuario = UserRepository.get_by_id(db, uid)
    assert usuario.puntos_acumulados == 20, (
        "se perdio una acreditacion de puntos: cada pago de $1000 da 10 puntos, "
        f"tendrian que quedar 20 y quedaron {usuario.puntos_acumulados}"
    )
    assert usuario.saldo == pytest.approx(3000.0), (
        "se perdio un descuento de saldo: 5000 - 2x1000 = 3000 y quedo "
        f"{usuario.saldo}"
    )
    db.close()


# ---------------------------------------------------------------------------
# R3 - puntos (canje)
# ---------------------------------------------------------------------------

def test_dos_canjes_simultaneos_no_regalan_puntos(sesion_factory, monkeypatch):
    """80 puntos y dos canjes de 50: solo UNO puede concretarse."""
    S = sesion_factory
    uid = _usuario(S, puntos=80)
    promo_id = _promo(S, costo_puntos=50)

    _barrera_en(monkeypatch, PromotionRepository, "get_active_by_id",
                threading.Barrier(2, timeout=10))

    def canjear(i):
        db = S()
        try:
            user = UserRepository.get_by_id(db, uid)
            return redeem_points(promo_id, db=db, current_user=user)
        finally:
            db.close()

    resultados = _correr_en_paralelo(canjear)
    exitos = [r for r in resultados if r[0] == "ok"]
    fallos = [r for r in resultados if r[0] == "error"]

    assert len(exitos) == 1, (
        "los DOS canjes pasaron: con 80 puntos solo se puede canjear UN beneficio "
        f"de 50 (se regalaron puntos). Resultados: {resultados}"
    )
    assert len(fallos) == 1
    assert getattr(fallos[0][1], "status_code", None) == 400
    assert "Puntos insuficientes" in str(getattr(fallos[0][1], "detail", ""))

    db = S()
    assert UserRepository.get_by_id(db, uid).puntos_acumulados == 30
    assert db.query(models.RedemptionTicket).count() == 1, "se emitieron dos tickets"
    db.close()
