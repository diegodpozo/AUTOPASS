"""FASE 3 - INVALIDACION DEL CACHE DE DISPONIBILIDAD (R1 del informe de concurrencia).

El cache de disponibilidad (`services/availability.py`) guarda cada calculo de
fechas/horas deshabilitadas durante 30 segundos (`_CACHE_AVAILABILITY_TTL_SECONDS`).
Eso hace que el selector de horarios siga ofreciendo un rango que acaba de ocuparse:
el usuario cierra una reserva y, si vuelve a mirar la grilla dentro de la ventana del
TTL, el horario que ya no existe sigue apareciendo como libre.

Estos tests son la prueba del arreglo de la Fase 3: tras un cambio de ocupacion el
cache de esa sede tiene que quedar vacio, de modo que la siguiente consulta recalcule
contra la base y el rango ocupado ya no se ofrezca.

ANTES de la implementacion (cache sin invalidar) estos tests FALLAN de forma
determinista: la segunda consulta devuelve el resultado viejo cacheado.
DESPUES de la implementacion (invalidacion por sucursal post-commit) PASAN.

Por que SQLite en memoria alcanza aca: a diferencia de los tests de R1/R3 (que
necesitan dos transacciones reales en paralelo), este bug es de ESTADO EN MEMORIA del
proceso -- el cache no depende de la base -- asi que una sola sesion secuencial lo
reproduce sin problemas.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base
from models import ParkingAforo, ParkingBranch, Reservation, Vehicle
from models.enums import PaymentStatus, ReservationStatus, VehicleType
from services import availability
from services.availability import (
    obtener_fechas_deshabilitadas,
    obtener_horas_deshabilitadas,
    invalidar_cache_disponibilidad,
)


SUCURSAL = "AUTOPASS Moron Cache"
FECHA = "2026-09-25"
INICIO = f"{FECHA} 10:00"
FIN = f"{FECHA} 11:00"


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    # EL CACHE ES GLOBAL AL PROCESO: SE LIMPIA ANTES DE CADA TEST PARA AISLARLOS.
    availability._CACHE_AVAILABILITY.clear()
    try:
        yield session
    finally:
        session.close()
        availability._CACHE_AVAILABILITY.clear()
        Base.metadata.drop_all(bind=engine)


def _seed(db, capacidad=1):
    db.add(ParkingBranch(nombre=SUCURSAL, direccion="Av. Moron 123", horario="24hs"))
    db.add(ParkingAforo(sucursal=SUCURSAL, capacidad_reservas_autos=capacidad))
    db.add(Vehicle(patente="CACHE1", tipo=VehicleType.AUTO))
    db.commit()


def _crear_reserva_activa(db):
    """Inserta la reserva que ocupa la plaza (simula lo que persiste create_user_reservation)."""
    db.add(Reservation(
        patente="CACHE1", sucursal_nombre=SUCURSAL,
        estado_pago=PaymentStatus.PAGADO, estado_reserva=ReservationStatus.ACTIVA,
        fecha_inicio=INICIO, fecha_fin=FIN, tipo_estadia="hora",
        monto_total=1500.0, tipo_vehiculo="Auto",
    ))
    db.commit()


def test_horas_deshabilitadas_reflejan_ocupacion_tras_invalidar(db):
    """CON CAPACIDAD 1: LA PRIMERA CONSULTA VE EL DIA LIBRE; DESPUES DE OCUPARLA E
    INVALIDAR, LA MISMA CONSULTA TIENE QUE VER LA HORA 10:00 COMO DESHABILITADA."""
    _seed(db, capacidad=1)

    antes = obtener_horas_deshabilitadas(db, SUCURSAL, FECHA, tipo_vehiculo="Auto")
    assert "10:00" not in antes  # el cache guarda el dia libre

    _crear_reserva_activa(db)
    # SIN INVALIDAR, el TTL de 30s devuelve el calculo viejo -> el bug (RED).
    invalidar_cache_disponibilidad(SUCURSAL)

    despues = obtener_horas_deshabilitadas(db, SUCURSAL, FECHA, tipo_vehiculo="Auto")
    assert "10:00" in despues


def test_cache_sin_invalidar_devuelve_el_valor_viejo(db):
    """DOCUMENTA EL BUG: SIN INVALIDAR, EL CACHE SIRVE EL RESULTADO ANTERIOR DENTRO DEL TTL.
    ES EL COMPORTAMIENTO ESPERADO DEL CACHE (no un fallo): sirve para fijar que la
    invalidacion es lo que cambia el resultado, y no otra casualidad del test."""
    _seed(db, capacidad=1)

    antes = obtener_horas_deshabilitadas(db, SUCURSAL, FECHA, tipo_vehiculo="Auto")
    assert "10:00" not in antes

    _crear_reserva_activa(db)
    sin_invalidar = obtener_horas_deshabilitadas(db, SUCURSAL, FECHA, tipo_vehiculo="Auto")
    assert "10:00" not in sin_invalidar  # valor viejo servido desde el cache


def test_fechas_deshabilitadas_reflejan_ocupacion_tras_invalidar(db):
    """MISMO CONTRATO PARA EL SELECTOR DE FECHAS (CACHE SEPARADO, MISMO TTL)."""
    _seed(db, capacidad=1)

    antes = obtener_fechas_deshabilitadas(
        db, SUCURSAL, tipo_vehiculo="Auto", tipo_estadia="dia",
        fecha_desde_str=FECHA, dias_evaluar=1,
    )
    assert FECHA not in antes

    _crear_reserva_activa(db)
    invalidar_cache_disponibilidad(SUCURSAL)

    despues = obtener_fechas_deshabilitadas(
        db, SUCURSAL, tipo_vehiculo="Auto", tipo_estadia="dia",
        fecha_desde_str=FECHA, dias_evaluar=1,
    )
    assert FECHA in despues


def test_invalidar_por_sucursal_no_toca_otras_sedes(db):
    """LA INVALIDACION ES POR SUCURSAL: LOS CALCULOS CACHEADOS DE OTRA SEDE SOBREVIVEN."""
    _seed(db, capacidad=1)
    otra = "AUTOPASS Castelar Cache"
    db.add(ParkingBranch(nombre=otra, direccion="Av. Castelar 456", horario="24hs"))
    db.add(ParkingAforo(sucursal=otra, capacidad_reservas_autos=2))
    db.commit()

    obtener_horas_deshabilitadas(db, SUCURSAL, FECHA, tipo_vehiculo="Auto")
    obtener_horas_deshabilitadas(db, otra, FECHA, tipo_vehiculo="Auto")
    claves_antes = set(availability._CACHE_AVAILABILITY)

    invalidar_cache_disponibilidad(SUCURSAL)

    claves_despues = set(availability._CACHE_AVAILABILITY)
    assert not any(k[1] == SUCURSAL for k in claves_despues)
    assert any(k[1] == otra for k in claves_despues)
    assert claves_despues < claves_antes


def test_invalidar_sin_sucursal_vacia_todo_el_cache(db):
    """CON `sucursal=None` SE VACIA EL CACHE COMPLETO (PARA CALLERS QUE NO CONOCEN LA SEDE)."""
    _seed(db, capacidad=1)
    obtener_horas_deshabilitadas(db, SUCURSAL, FECHA, tipo_vehiculo="Auto")
    assert availability._CACHE_AVAILABILITY

    invalidar_cache_disponibilidad()

    assert availability._CACHE_AVAILABILITY == {}
