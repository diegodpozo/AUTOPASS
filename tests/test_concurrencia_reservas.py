"""FASE 0 (R1/R2) - CARRERAS DE AFORO Y DE PATENTE BAJO EL LOCK TRANSACCIONAL.

R1 (aforo): dos requests simultaneos sobre la ULTIMA plaza de una sede pasan los dos
    el chequeo de disponibilidad y ambos insertan: la sede queda sobrevendida.
R2 (patente): dos requests simultaneos con la MISMA patente y rango solapado pasan los
    dos `get_overlap_by_patente` y ambos insertan: dos reservas vigentes para el mismo
    auto en la misma sede.

Estas carreras son check-then-act: la decision (`verificar_disponibilidad` /
`get_overlap_by_patente`) y la escritura (`db.add` + `db.commit`) no son atomicas, asi
que sin serializacion los dos hilos deciden con el mismo estado viejo.

POR QUE ESTOS TESTS CORREN EN POSTGRES Y NO EN SQLITE: el fix de la Fase 2 es
`pg_advisory_xact_lock`, y en SQLite `bloqueo_transaccional` es un no-op documentado
(no hay advisory locks). Un test sobre SQLite no puede demostrar que el lock serializa
--probaria solo el guard secuencial--, asi que la prueba real de R1/R2 necesita un
Postgres. Estos tests usan un SCHEMA PROPIO Y EFIMERO (search_path) en la base de
`DATABASE_URL` (Neon) para no tocar ninguna tabla real: se crea al empezar el modulo y
se borra al terminar.

Se saltan solos (`pytest.skip`) si no hay `DATABASE_URL` de Postgres o si la base no
responde, para no romper la suite offline.

GRUPO "postgres": todo el modulo esta marcado con `pytestmark = pytest.mark.postgres`.
Ese grupo se DESELECCIONA por defecto desde `pytest.ini` (`addopts = -m "not postgres"`)
para que la suite normal sea rapida y sin red. Para correr SOLO estos:
    venv\\Scripts\\python.exe -m pytest -m postgres

Estructura de cada carrera:
  1. `test_r1_*_sin_lock_demuestra_la_carrera`: llama al cuerpo SIN `bloqueo_transaccional`
     (replica el codigo de decision + insercion). Los dos hilos insertan -> evidencia de
     la carrera (equivalente al RED historico). Es el CONTROL: prueba que el escenario
     realmente se solapa y que, de no haber lock, el bug ocurre.
  2. `test_r1_*_con_lock_serializa`: llama a `ReservationService.create_user_reservation`
     (que SI toma el lock). Exactamente uno de los dos gana; el otro recibe el rechazo
     del guard. Es el GREEN de la Fase 2.
"""
import datetime
import threading
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.config import settings
from core.database import Base
from models import ParkingAforo, ParkingBranch, Reservation, Settings, User, Vehicle
from models.enums import PaymentStatus, ReservationStatus, VehicleType
from schemas import UserReservationCreate
from services import availability
from services.reservation_service import ReservationService

# TODO el modulo pertenece al grupo "postgres" (ver pytest.ini).
pytestmark = pytest.mark.postgres

POSTGRES_URL = None
if settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgresql"):
    POSTGRES_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    if "postgresql+psycopg://" not in POSTGRES_URL:
        POSTGRES_URL = None

pg_only = pytest.mark.skipif(
    POSTGRES_URL is None,
    reason="R1/R2 requieren Postgres (el lock es no-op en SQLite). Sin DATABASE_URL de Postgres.",
)


def _probe(url):
    """True si la base de Postgres responde (evita fallar la suite sin red)."""
    try:
        eng = create_engine(url, connect_args={"connect_timeout": 8})
        with eng.connect() as c:
            c.execute(text("select 1"))
        eng.dispose()
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def pg_engines():
    if POSTGRES_URL is None:
        pytest.skip("Sin DATABASE_URL de Postgres")
    if not _probe(POSTGRES_URL):
        pytest.skip("Postgres no responde (¿sin red?)")

    schema = f"rk_test_{uuid.uuid4().hex[:12]}"
    admin = create_engine(POSTGRES_URL, connect_args={"connect_timeout": 10})
    with admin.begin() as c:
        c.execute(text(f'CREATE SCHEMA "{schema}"'))

    # search_path por conexion: TODO lo que haga este engine vive en el schema efimero.
    eng = create_engine(
        POSTGRES_URL,
        connect_args={"connect_timeout": 10, "options": f"-csearch_path={schema}"},
    )
    Base.metadata.create_all(bind=eng)
    try:
        yield eng
    finally:
        eng.dispose()
        with admin.begin() as c:
            c.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin.dispose()


@pytest.fixture
def pg_db(pg_engines):
    S = sessionmaker(autocommit=False, autoflush=False, bind=pg_engines)
    session = S()
    # Aislamiento: cada test arranca con las tablas del schema limpias.
    with pg_engines.begin() as c:
        c.execute(text(
            "TRUNCATE reservations, vehicles, users, settings, parking_aforo, parking_branches "
            "RESTART IDENTITY CASCADE"
        ))
    availability._CACHE_AVAILABILITY.clear()
    try:
        yield session
    finally:
        session.close()
        availability._CACHE_AVAILABILITY.clear()


SUCURSAL = "Sede Concurrencia PG"
# LA VALIDACION DE ANTICIPACION USA RELOJ REAL: rango futuro calculado al vuelo.
_FUTURO = (datetime.datetime.now() + datetime.timedelta(days=5)).replace(
    minute=0, second=0, microsecond=0
)


def _seed(pg_db, capacidad=1, patente="PGS123", user_email="pg@test.com"):
    branch = ParkingBranch(nombre=SUCURSAL, direccion="Av. PG 100", horario="24hs", is_24h=True)
    pg_db.add(branch)
    pg_db.commit()
    pg_db.add(ParkingAforo(sucursal=SUCURSAL, capacidad_reservas_autos=capacidad))
    for clave, valor in (("precio_hora", 1500.0), ("precio_30min", 750.0)):
        pg_db.add(Settings(clave=clave, valor=valor, sucursal=SUCURSAL))
    user = User(nombre="Con", apellido="Carrera", dni="30999888", email=user_email,
                rol="user", sucursal=SUCURSAL, saldo=100000.0, puntos_acumulados=0)
    pg_db.add(user)
    pg_db.commit()
    pg_db.add(Vehicle(patente=patente, tipo=VehicleType.AUTO, user_id=user.id))
    pg_db.commit()
    return user


def _rango(offset_min=0, dur_min=60):
    base = _FUTURO + datetime.timedelta(minutes=offset_min)
    return (
        base.strftime("%Y-%m-%d %H:%M"),
        (base + datetime.timedelta(minutes=dur_min)).strftime("%Y-%m-%d %H:%M"),
    )


def _data(patente, inicio, fin):
    return UserReservationCreate(
        patente=patente, sucursal_nombre=SUCURSAL,
        fecha_inicio=inicio, fecha_fin=fin, tipo_estadia="hora",
    )


def _correr_dos(cuerpo, sesion_factory):
    """Corre `cuerpo(sesion)` en dos hilos con una barrera comun de arranque.

    Devuelve la lista de resultados: ("ok", valor) o ("err", excepcion)."""
    barrera = threading.Barrier(2)
    resultados = []
    lock_res = threading.Lock()

    def worker():
        sesion = sesion_factory()
        barrera.wait()
        try:
            valor = cuerpo(sesion)
            with lock_res:
                resultados.append(("ok", valor))
        except Exception as exc:  # HTTPException esperada en el perdedor
            with lock_res:
                resultados.append(("err", exc))
        finally:
            sesion.close()

    hilos = [threading.Thread(target=worker) for _ in range(2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=60)
    return resultados


# ---------------------------------------------------------------------------
# R1 - capacidad de la sede
# ---------------------------------------------------------------------------

def _cuerpo_sin_lock_r1(sesion, user_id, data):
    """Replica el chequeo + la insercion de create_user_reservation SIN el lock."""
    from services.reservation_service import verificar_disponibilidad
    disp = verificar_disponibilidad(sesion, data.sucursal_nombre, data.fecha_inicio, data.fecha_fin, tipo_vehiculo="Auto")
    if not disp["disponible"]:
        raise AssertionError("no disponible")
    sesion.add(Reservation(
        user_id=user_id, patente=data.patente, sucursal_nombre=data.sucursal_nombre,
        fecha_inicio=data.fecha_inicio, fecha_fin=data.fecha_fin, tipo_estadia="hora",
        monto_total=1500.0, estado_pago=PaymentStatus.PENDIENTE,
        estado_reserva=ReservationStatus.PENDIENTE, tipo_vehiculo="Auto",
    ))
    sesion.commit()
    return True


@pg_only
def test_r1_sin_lock_demuestra_la_carrera(pg_db, pg_engines):
    """CONTROL: sin lock, dos hilos sobrevendidos insertan AMBOS la ultima plaza."""
    user = _seed(pg_db, capacidad=1)
    inicio, fin = _rango()
    data = _data("PGS123", inicio, fin)
    S = sessionmaker(autocommit=False, autoflush=False, bind=pg_engines)

    resultados = _correr_dos(lambda s: _cuerpo_sin_lock_r1(s, user.id, data), S)

    ok = [r for r in resultados if r[0] == "ok"]
    total = pg_db.query(Reservation).filter(Reservation.sucursal_nombre == SUCURSAL).count()
    assert len(ok) == 2, f"se esperaba la carrera (2 exitos), hubo {len(resultados)} resultados: {resultados}"
    assert total == 2, "sin lock, la sede quedo sobrevendida (2 reservas con capacidad 1)"


@pg_only
def test_r1_con_lock_serializa(pg_db, pg_engines):
    """GREEN: con el lock de la Fase 2, solo UNO gana la ultima plaza."""
    user = _seed(pg_db, capacidad=1)
    inicio, fin = _rango()
    data = _data("PGS123", inicio, fin)
    S = sessionmaker(autocommit=False, autoflush=False, bind=pg_engines)

    def cuerpo(sesion):
        # Cada hilo carga SU copia del usuario: nada de objetos ORM cruzando sesiones.
        usuario = sesion.query(User).filter(User.id == user.id).one()
        # create_user_reservation toma clave_aforo + clave_patente + clave_usuario.
        return ReservationService.create_user_reservation(sesion, usuario, data)

    resultados = _correr_dos(cuerpo, S)

    ok = [r for r in resultados if r[0] == "ok"]
    err = [r for r in resultados if r[0] == "err"]
    total = pg_db.query(Reservation).filter(Reservation.sucursal_nombre == SUCURSAL).count()
    assert len(ok) == 1, f"exactamente uno debe ganar; resultados: {resultados}"
    assert len(err) == 1, f"el perdedor debe ser rechazado; resultados: {resultados}"
    assert total == 1, "con el lock no puede sobrevenderse la sede"


# ---------------------------------------------------------------------------
# R2 - misma patente, rango solapado
# ---------------------------------------------------------------------------

def _cuerpo_sin_lock_r2(sesion, user_id, data):
    """Replica chequeo de solape de patente + insercion SIN el lock."""
    from repositories.reservation_repository import ReservationRepository
    from core.normalize import normalize_plate
    p = normalize_plate(data.patente)
    if ReservationRepository.get_overlap_by_patente(
        sesion, p, data.sucursal_nombre, data.fecha_inicio, data.fecha_fin
    ):
        raise AssertionError("solape detectado")
    sesion.add(Reservation(
        user_id=user_id, patente=p, sucursal_nombre=data.sucursal_nombre,
        fecha_inicio=data.fecha_inicio, fecha_fin=data.fecha_fin, tipo_estadia="hora",
        monto_total=1500.0, estado_pago=PaymentStatus.PENDIENTE,
        estado_reserva=ReservationStatus.PENDIENTE, tipo_vehiculo="Auto",
    ))
    sesion.commit()
    return True


@pg_only
def test_r2_sin_lock_demuestra_la_carrera(pg_db, pg_engines):
    """CONTROL: sin lock, dos hilos con la misma patente y rango insertan AMBOS."""
    user = _seed(pg_db, capacidad=5)
    inicio, fin = _rango()
    data = _data("PGS123", inicio, fin)
    S = sessionmaker(autocommit=False, autoflush=False, bind=pg_engines)

    resultados = _correr_dos(lambda s: _cuerpo_sin_lock_r2(s, user.id, data), S)

    ok = [r for r in resultados if r[0] == "ok"]
    total = pg_db.query(Reservation).filter(Reservation.patente == "PGS123").count()
    assert len(ok) == 2, f"se esperaba la carrera (2 exitos): {resultados}"
    assert total == 2, "sin lock quedaron 2 reservas solapadas de la misma patente"


@pg_only
def test_r2_con_lock_serializa(pg_db, pg_engines):
    """GREEN: con el lock, el segundo ve el solape que el primero ya confirmo."""
    user = _seed(pg_db, capacidad=5)
    inicio, fin = _rango()
    data = _data("PGS123", inicio, fin)
    S = sessionmaker(autocommit=False, autoflush=False, bind=pg_engines)

    def cuerpo(sesion):
        usuario = sesion.query(User).filter(User.id == user.id).one()
        return ReservationService.create_user_reservation(sesion, usuario, data)

    resultados = _correr_dos(cuerpo, S)

    ok = [r for r in resultados if r[0] == "ok"]
    err = [r for r in resultados if r[0] == "err"]
    total = pg_db.query(Reservation).filter(Reservation.patente == "PGS123").count()
    assert len(ok) == 1, f"exactamente uno debe ganar; resultados: {resultados}"
    assert len(err) == 1, f"el solapado debe rechazarse; resultados: {resultados}"
    assert total == 1, "con el lock no puede haber dos reservas solapadas de la misma patente"
