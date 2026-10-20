"""FASE 4 - CONSTRAINT DE NO-SOLAPE DE PATENTE POR SEDE (solo Postgres).

Criterio de salida del informe: un `INSERT` manual que solape una patente vigente
falla con `IntegrityError` aunque se esquive el servicio (o sea: sin pasar por
`ReservationService`, sin pasar por el lock).

El constraint vive en la migracion Alebmic `b1c2d3e4f5a6` (solo Postgres): SQLite no
tiene `EXCLUDE`, y declararlo en el modelo romperia `create_all` en SQLite (que es la
base de toda la suite). Por eso este modulo corre en el grupo `postgres`.

El test aplica el MISMO DDL que la migracion (importa `DDL_CONSTRAINT`), asi que si
alguien cambia la migracion, el test verifica lo nuevo — no una copia.

Las semantica que se verifica es la del repositorio (`get_overlap_by_patente`):
misma patente normalizada (mayusculas sin espacios) + misma sede + rango solapado
`inicio < hasta AND fin > desde` (o sea `[)`), solo entre reservas vigentes.
"""
import datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from core.database import Base
from models import ParkingAforo, ParkingBranch, Reservation, Settings, User, Vehicle
from models.enums import PaymentStatus, ReservationStatus, VehicleType
from tests.postgres_helpers import (
    borrar_schema_efimero,
    cargar_migracion,
    crear_schema_efimero,
    pg_only,
    solo_si_postgres_esta_vivo,
)

# TODO el modulo pertenece al grupo "postgres" (ver pytest.ini).
pytestmark = pytest.mark.postgres

# Fuente unica del DDL: se importa de la migracion.
_migracion = cargar_migracion("b1c2d3e4f5a6")
NOMBRE_CONSTRAINT = _migracion.CONSTRAINT
DDL_CONSTRAINT = _migracion.DDL_CONSTRAINT

SUCURSAL = "Sede Constraint PG"
_FUTURO = (datetime.datetime.now() + datetime.timedelta(days=30)).replace(
    minute=0, second=0, microsecond=0
)


@pytest.fixture(scope="module")
def pg_con_constraint():
    """Schema efimero con el esquema del modelo + el constraint de la Fase 4 aplicado."""
    solo_si_postgres_esta_vivo()
    eng, admin, schema = crear_schema_efimero("rk_f4")
    Base.metadata.create_all(bind=eng)
    with eng.begin() as c:
        c.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        c.execute(text(DDL_CONSTRAINT))
    try:
        yield eng
    finally:
        eng.dispose()
        borrar_schema_efimero(admin, schema)


@pytest.fixture
def db(pg_con_constraint):
    S = sessionmaker(autocommit=False, autoflush=False, bind=pg_con_constraint)
    session = S()
    with pg_con_constraint.begin() as c:
        c.execute(text(
            "TRUNCATE reservations, vehicles, users, settings, parking_aforo, parking_branches "
            "RESTART IDENTITY CASCADE"
        ))
    try:
        yield session
    finally:
        session.close()


def _seed(db, capacidad=5):
    db.add(ParkingBranch(nombre=SUCURSAL, direccion="Av. F4 100", horario="24hs", is_24h=True))
    db.commit()
    db.add(ParkingAforo(sucursal=SUCURSAL, capacidad_reservas_autos=capacidad))
    for clave, valor in (("precio_hora", 1500.0), ("precio_30min", 750.0)):
        db.add(Settings(clave=clave, valor=valor, sucursal=SUCURSAL))
    user = User(nombre="Con", apellido="Straint", dni="30888777", email="f4@test.com",
                rol="user", sucursal=SUCURSAL, saldo=100000.0, puntos_acumulados=0)
    db.add(user)
    db.commit()
    db.add(Vehicle(patente="F4X123", tipo=VehicleType.AUTO, user_id=user.id))
    db.commit()
    return user


def _franja(offset_horas=0, dur_horas=2):
    """Rango [inicio, fin) en el formato que guarda el modelo (str 'YYYY-MM-DD HH:MM')."""
    ini = _FUTURO + datetime.timedelta(hours=offset_horas)
    fin = ini + datetime.timedelta(hours=dur_horas)
    return ini.strftime("%Y-%m-%d %H:%M"), fin.strftime("%Y-%m-%d %H:%M")


def _reserva(user_id, patente, ini, fin, estado_reserva=ReservationStatus.PENDIENTE,
             estado_pago=PaymentStatus.PENDIENTE, sucursal=SUCURSAL):
    return Reservation(user_id=user_id, patente=patente, fecha_inicio=ini, fecha_fin=fin,
                       monto_total=1500.0, estado_pago=estado_pago,
                       estado_reserva=estado_reserva, tipo_estadia="hora",
                       sucursal_nombre=sucursal, tipo_vehiculo="Auto")


# ---------------------------------------------------------------------------
# Criterio de salida: el INSERT solapado falla con IntegrityError
# ---------------------------------------------------------------------------

@pg_only
def test_insert_manual_solapado_falla(db):
    """Aunque se esquive el servicio, el motor rechaza el solape de patente."""
    user = _seed(db)
    ini, fin = _franja(0, 2)
    db.add(_reserva(user.id, "F4X123", ini, fin))
    db.commit()

    # INSERT "a mano", sin servicios ni locks: mismo auto, misma sede, rango solapado.
    solapada = _franja(1, 2)  # arranca dentro del rango anterior
    db.add(_reserva(user.id, "F4X123", solapada[0], solapada[1]))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    total = db.query(Reservation).filter(Reservation.sucursal_nombre == SUCURSAL).count()
    assert total == 1, "el motor debe impedir la segunda reserva solapada"


@pg_only
def test_normaliza_espacios_y_mayusculas(db):
    """'f4 x123' y 'F4X123' son la MISMA patente (igual que el repositorio)."""
    user = _seed(db)
    ini, fin = _franja(0, 2)
    db.add(_reserva(user.id, "F4X123", ini, fin))
    db.commit()

    variante = _franja(1, 2)
    db.add(_reserva(user.id, "f4 x123", variante[0], variante[1]))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


@pg_only
def test_rango_contiguo_no_choca(db):
    """Semantica [): una reserva que empieza justo cuando termina la otra es valida."""
    user = _seed(db)
    ini, fin = _franja(0, 2)
    db.add(_reserva(user.id, "F4X123", ini, fin))
    db.commit()

    contigua = _franja(2, 2)  # arranca exactamente al terminar la anterior
    db.add(_reserva(user.id, "F4X123", contigua[0], contigua[1]))
    db.commit()  # no debe lanzar
    assert db.query(Reservation).filter(Reservation.patente == "F4X123").count() == 2


@pg_only
def test_otra_sede_no_choca(db):
    """El solape es POR SEDE: la misma patente en otra sede es valida."""
    user = _seed(db)
    db.add(ParkingBranch(nombre="Otra Sede F4", direccion="Calle 2", horario="24hs", is_24h=True))
    db.commit()

    ini, fin = _franja(0, 2)
    db.add(_reserva(user.id, "F4X123", ini, fin, sucursal=SUCURSAL))
    db.add(_reserva(user.id, "F4X123", ini, fin, sucursal="Otra Sede F4"))
    db.commit()  # no debe lanzar
    assert db.query(Reservation).filter(Reservation.patente == "F4X123").count() == 2


@pg_only
@pytest.mark.parametrize("estado_reserva,estado_pago", [
    (ReservationStatus.CANCELADA, PaymentStatus.PAGADO),
    (ReservationStatus.COMPLETADA, PaymentStatus.PAGADO),
    (ReservationStatus.PENDIENTE, PaymentStatus.CANCELADO),
    (ReservationStatus.PENDIENTE, PaymentStatus.FALLIDO),
    (ReservationStatus.PENDIENTE, PaymentStatus.REEMBOLSADO),
])
def test_estados_no_vigentes_no_bloquean(db, estado_reserva, estado_pago):
    """Canceladas/completadas/fallidas NO cuentan: el predicado parcial las ignora."""
    user = _seed(db)
    ini, fin = _franja(0, 2)
    db.add(_reserva(user.id, "F4X123", ini, fin,
                    estado_reserva=estado_reserva, estado_pago=estado_pago))
    db.commit()

    # Otra vigente en el mismo rango: debe poder entrar.
    db.add(_reserva(user.id, "F4X123", ini, fin))
    db.commit()  # no debe lanzar
    assert db.query(Reservation).filter(Reservation.patente == "F4X123").count() == 2


@pg_only
def test_sin_fecha_de_mp_no_choca(db):
    """Preferencias de MP sin fechas cargadas no bloquean (fechas NULL)."""
    user = _seed(db)
    db.add(_reserva(user.id, "F4X123", None, None))
    db.commit()
    ini, fin = _franja(0, 2)
    db.add(_reserva(user.id, "F4X123", ini, fin))
    db.commit()  # no debe lanzar
    assert db.query(Reservation).filter(Reservation.patente == "F4X123").count() == 2


@pg_only
def test_el_constraint_existe_con_el_nombre_esperado(db):
    """El constraint quedo declarado en el catalogo de Postgres.

    Se acota a la tabla del schema actual (`to_regclass` respeta el `search_path`):
    contar por nombre sin filtrar sumaria tambien el constraint de `public` en Neon,
    que es el mismo nombre, y el test fallaria por una razon que no le importa.
    """
    with db.get_bind().connect() as c:
        n = c.execute(text(
            "SELECT COUNT(*) FROM pg_constraint "
            "WHERE conname = :n AND contype = 'x' AND conrelid = to_regclass('reservations')"
        ), {"n": NOMBRE_CONSTRAINT}).scalar()
    assert n == 1, f"falta el constraint {NOMBRE_CONSTRAINT} en el schema del test"
