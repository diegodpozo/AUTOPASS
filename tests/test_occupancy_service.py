import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, ParkingBranch, ParkingAforo, ParkingFloor, AccessLog, Reservation, Settings
from models.enums import ReservationStatus, PaymentStatus
from services.occupancy_service import OccupancyService
from services.time_service import TimeService

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.add(Settings(clave="precio_hora", valor=1500.0, sucursal="Centro"))
    db.add(Settings(clave="precio_30min", valor=750.0, sucursal="Centro"))
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def _reserva(db, sucursal="Sede", tipo="Auto", estado_pago=PaymentStatus.PAGADO,
             estado_reserva=ReservationStatus.PENDIENTE, ini="2000-01-01 00:00:00", fin="2100-01-01 00:00:00"):
    r = Reservation(sucursal_nombre=sucursal, tipo_vehiculo=tipo, patente="P1",
                    estado_pago=estado_pago.value, estado_reserva=estado_reserva.value,
                    fecha_inicio=ini, fecha_fin=fin, monto_total=100.0)
    db.add(r)
    db.commit()
    return r


def _log(db, i, patente, tipo, sucursal, fecha, reserva_id=None, pago=False):
    db.add(AccessLog(id=i, patente_detectada=patente, tipo_evento=tipo, sucursal=sucursal,
                     fecha_hora=fecha, reserva_id=reserva_id, pago_confirmado=pago))
    db.commit()


def test_default_capacities(db):
    caps = OccupancyService.default_capacities()
    assert caps["capacidad_total"] == 20
    assert caps["capacidad_motos"] == 10
    assert caps["capacidad_camionetas"] == 5
    assert caps["disponibilidad"] == 20


def test_capacities_from_aforo(db):
    a = ParkingAforo(sucursal="Sede", capacidad_total=50, ocupacion_actual=3,
                     capacidad_motos=12, capacidad_camionetas=4, ocupacion_camionetas=1)
    db.add(a)
    db.commit()

    caps = OccupancyService.capacities_from_aforo(a)
    assert caps["capacidad_total"] == 50
    assert caps["ocupacion_actual"] == 3
    assert caps["disponibilidad"] == 47
    assert caps["capacidad_camionetas"] == 4
    assert caps["ocupacion_camionetas"] == 1
    assert caps["disponibilidad_camionetas"] == 3
    # Aforo sin valores de reservas usa los defaults del modelo
    assert caps["capacidad_reservas_autos"] == 5
    assert caps["capacidad_reservas_motos"] == 3
    assert caps["capacidad_reservas_camionetas"] == 2
    assert caps["capacidad_reservas"] == 10
    assert caps["disponibilidad_reservas"] == 10


def test_calculate_branch_capacities_suma_pb_y_pisos(db):
    branch = ParkingBranch(nombre="TestBranch", direccion="Dir", horario="24hs")
    db.add(branch)
    db.commit()

    db.add(ParkingAforo(sucursal="TestBranch", capacidad_total=20, capacidad_motos=10))
    db.add(ParkingFloor(branch_id=branch.id, nombre="Piso 1", capacidad_total=10, capacidad_motos=5))
    db.commit()

    caps = OccupancyService.calculate_branch_capacities(db, branch)
    assert caps["capacidad_total"] == 30
    assert caps["capacidad_motos"] == 15
    assert caps["capacidad_camionetas"] == 10
    assert caps["disponibilidad"] == 30
    # PB default 5 + piso default 5 en reservas de autos
    assert caps["capacidad_reservas_autos"] == 10


def test_ocupacion_reservas_vigentes_cuenta_por_tipo(db):
    _reserva(db, tipo="Auto")
    _reserva(db, tipo="Moto")
    _reserva(db, tipo="Camioneta")
    # EXCLUIDA: NO PAGADA
    _reserva(db, tipo="Moto", estado_pago=PaymentStatus.PENDIENTE)

    conteo = OccupancyService.ocupacion_reservas_vigentes(db, "Sede")
    assert conteo == {"autos": 1, "motos": 1, "camionetas": 1}


def test_calculate_branch_capacities_incluye_reservas_vigentes(db):
    branch = ParkingBranch(nombre="Sede", direccion="Dir", horario="24hs")
    db.add(branch)
    db.commit()
    db.add(ParkingAforo(sucursal="Sede", capacidad_total=20, capacidad_motos=10))
    _reserva(db, sucursal="Sede", tipo="Moto")
    db.commit()

    caps = OccupancyService.calculate_branch_capacities(db, branch)
    assert caps["ocupacion_reservas_motos"] == 1
    assert caps["disponibilidad_reservas_motos"] == max(0, 3 - 1)


def test_current_occupancy_excluye_salidas(db):
    _log(db, 1, "AAA111", "ENTRADA", "Centro", "2025-01-05 10:00:00")
    _log(db, 2, "BBB222", "ENTRADA", "Centro", "2025-01-05 10:00:00")
    _log(db, 3, "AAA111", "SALIDA", "Centro", "2025-01-05 11:00:00")

    res = OccupancyService.current_occupancy(db, "Centro")
    patentes = [r["patente"] for r in res]
    assert patentes == ["BBB222"]
    assert res[0]["es_reserva"] is False


def test_current_occupancy_cortesia_dentro_de_10min(db):
    _log(db, 1, "CCC333", "ENTRADA", "Centro", TimeService.now_str())

    res = OccupancyService.current_occupancy(db, "Centro")
    assert res[0]["patente"] == "CCC333"
    assert res[0]["en_cortesia"] is True
    assert res[0]["deuda"] == 0.0


def test_current_occupancy_fuera_de_cortesia_acumula_deuda(db):
    _log(db, 1, "EEE555", "ENTRADA", "Centro", "2025-01-05 10:00:00")

    res = OccupancyService.current_occupancy(db, "Centro")
    assert res[0]["en_cortesia"] is False
    assert res[0]["deuda"] > 0.0


def test_current_occupancy_reserva_pagada_vigente(db):
    r = _reserva(db, sucursal="Centro", tipo="Auto")
    _log(db, 1, "DDD444", "ENTRADA", "Centro", "2025-01-05 10:00:00", reserva_id=r.id)

    res = OccupancyService.current_occupancy(db, "Centro")
    assert res[0]["patente"] == "DDD444"
    assert res[0]["es_reserva"] is True
    assert res[0]["ya_pago"] is True
    assert res[0]["deuda"] == 0.0
    assert res[0]["reserva"]["id"] == r.id