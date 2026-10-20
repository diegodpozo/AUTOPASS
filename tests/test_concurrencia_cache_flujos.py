"""FASE 3 - INVALIDACION DEL CACHE DESDE LOS FLUJOS REALES DE RESERVA.

El test de `tests/test_concurrencia_cache_disponibilidad.py` prueba el helper
(`invalidar_cache_disponibilidad`). Estos tests prueban lo otro: que los flujos que
cambian la ocupacion de una sede REALMENTE lo llamen despues del commit. Sin esto, el
helper podria estar perfecto y el cache seguir sirviendo datos viejos.

Se cubren los tres flujos que pide la Fase 3 del informe:
  - crear reserva de usuario   (create_user_reservation)
  - modificar reserva          (modify_user_reservation)
  - cancelar reserva           (cancel_reservation)

La verificacion es directa sobre `_CACHE_AVAILABILITY`: se puebla el cache de la sede
con una consulta real y se comprueba que despues de la operacion no queden entradas de
esa sede (para crear/modificar se puebla a mano para no depender de la disponibilidad
del rango elegido).
"""
import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.database import Base
from models import ParkingAforo, ParkingBranch, Settings, User, Vehicle
from models.enums import ReservationStatus, VehicleType
from schemas import UserReservationCreate
from services import availability
from services.availability import obtener_horas_deshabilitadas
from services.reservation_service import ReservationService


SUCURSAL = "Sucursal Cache Flujo"
# LA VALIDACION DE ANTICIPACION USA RELOJ REAL (datetime.datetime.now, no TimeService),
# ASI QUE LOS RANGOS SE ARMARON SOBRE UNA FECHA FUTURA CALCULADA AL VUELO.
_BASE = (datetime.datetime.now() + datetime.timedelta(days=10)).replace(
    hour=0, minute=0, second=0, microsecond=0
)
FECHA = _BASE.strftime("%Y-%m-%d")


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()

    session.add(ParkingBranch(nombre=SUCURSAL, direccion="Av. Flujo 123", horario="24hs", is_24h=True))
    session.add(ParkingAforo(sucursal=SUCURSAL, capacidad_reservas_autos=3))
    for clave, valor in (("precio_hora", 1500.0), ("precio_30min", 750.0)):
        session.add(Settings(clave=clave, valor=valor, sucursal=SUCURSAL))
    session.commit()

    availability._CACHE_AVAILABILITY.clear()
    try:
        yield session
    finally:
        session.close()
        availability._CACHE_AVAILABILITY.clear()
        Base.metadata.drop_all(bind=engine)


def _cliente(db, saldo=100000.0):
    user = User(nombre="Ana", apellido="Flujo", dni="30111222", email="ana@test.com",
                rol="user", sucursal=SUCURSAL, saldo=saldo, puntos_acumulados=0)
    db.add(user)
    db.commit()
    return user


def _vehiculo(db, user, patente="FLU123"):
    db.add(Vehicle(patente=patente, tipo=VehicleType.AUTO, user_id=user.id))
    db.commit()


def _poblar_cache(db, sucursal=SUCURSAL):
    """Llena el cache de la sede con una consulta real, para poder observar la invalidacion."""
    obtener_horas_deshabilitadas(db, sucursal, FECHA, tipo_vehiculo="Auto")
    assert any(k[1] == sucursal for k in availability._CACHE_AVAILABILITY)


def _entradas_de(sucursal):
    return [k for k in availability._CACHE_AVAILABILITY if len(k) > 1 and k[1] == sucursal]


def test_create_user_reservation_invalida_cache(db):
    user = _cliente(db)
    _vehiculo(db, user)
    _poblar_cache(db)

    data = UserReservationCreate(
        patente="FLU123", sucursal_nombre=SUCURSAL,
        fecha_inicio=f"{FECHA} 10:00", fecha_fin=f"{FECHA} 11:00",
        tipo_estadia="hora",
    )
    ReservationService.create_user_reservation(db, user, data)

    assert _entradas_de(SUCURSAL) == []


def test_modify_user_reservation_invalida_cache(db):
    user = _cliente(db)
    _vehiculo(db, user)
    reserva = models.Reservation(
        user_id=user.id, patente="FLU123", sucursal_nombre=SUCURSAL,
        fecha_inicio=f"{FECHA} 08:00", fecha_fin=f"{FECHA} 09:00",
        tipo_estadia="hora", monto_total=1500.0,
        estado_reserva=ReservationStatus.PENDIENTE, tipo_vehiculo="Auto",
    )
    db.add(reserva)
    db.commit()

    _poblar_cache(db)

    from schemas import ReservationUpdate
    ReservationService.modify_user_reservation(
        db, user, reserva.id,
        ReservationUpdate(fecha_inicio=f"{FECHA} 09:00", fecha_fin=f"{FECHA} 10:00",
                          tipo_estadia="hora", sucursal_nombre=SUCURSAL),
    )

    assert _entradas_de(SUCURSAL) == []


def test_cancel_reservation_invalida_cache(db):
    user = _cliente(db)
    _vehiculo(db, user)
    reserva = models.Reservation(
        user_id=user.id, patente="FLU123", sucursal_nombre=SUCURSAL,
        fecha_inicio=f"{FECHA} 10:00", fecha_fin=f"{FECHA} 11:00",
        tipo_estadia="hora", monto_total=1500.0,
        estado_reserva=ReservationStatus.PENDIENTE, tipo_vehiculo="Auto",
    )
    db.add(reserva)
    db.commit()

    _poblar_cache(db)

    ReservationService.cancel_reservation(db, user, reserva.id)

    assert _entradas_de(SUCURSAL) == []
