import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, ParkingAforo, ParkingBranch, Reservation, Vehicle
from models.enums import ReservationStatus, PaymentStatus, VehicleType
from services.reservation_service import (
    verificar_disponibilidad,
    _calcular_ocupacion_maxima_simultanea,
    obtener_fechas_deshabilitadas,
    obtener_horas_deshabilitadas
)

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

def test_sweep_line_algorithm(db):
    """PRUEBA EL ALGORITMO SWEEP-LINE DE CÁLCULO DE OCUPACIÓN MÁXIMA SIMULTÁNEA."""
    res1 = Reservation(patente="AAA111", fecha_inicio="2026-09-10 14:00", fecha_fin="2026-09-10 15:00")
    res2 = Reservation(patente="BBB222", fecha_inicio="2026-09-10 14:30", fecha_fin="2026-09-10 15:30")
    res3 = Reservation(patente="CCC333", fecha_inicio="2026-09-10 16:00", fecha_fin="2026-09-10 17:00")

    # Entre 14:00 y 14:30 hay 1 (res1)
    # Entre 14:30 y 15:00 hay 2 (res1 + res2) -> Ocupación máxima es 2
    # Entre 15:00 y 15:30 hay 1 (res2)
    # Entre 16:00 y 17:00 hay 1 (res3)

    max_oc = _calcular_ocupacion_maxima_simultanea([res1, res2, res3], "2026-09-10 00:00", "2026-09-10 23:59")
    assert max_oc == 2

    # Si evaluamos solo de 16:00 a 17:00, el pico es 1
    max_oc_tarde = _calcular_ocupacion_maxima_simultanea([res1, res2, res3], "2026-09-10 16:00", "2026-09-10 17:00")
    assert max_oc_tarde == 1


def test_capacity_blocking_rules(db):
    """VERIFICA QUE UNA RESERVA POR HORA QUE LLENA LA CAPACIDAD BLOQUEE LA RESERVA DE DÍA ENTERO PERO NO OTRA HORA LIBRE."""
    branch_name = "AUTOPASS Morón"
    branch = ParkingBranch(nombre=branch_name, direccion="Av. Morón 123", horario="24hs")
    aforo = ParkingAforo(
        sucursal=branch_name,
        capacidad_total=5,
        capacidad_reservas=2,
        capacidad_reservas_autos=2  # Capacidad máxima de 2 autos
    )
    db.add_all([branch, aforo])

    v1 = Vehicle(patente="AUTO1", tipo=VehicleType.AUTO)
    v2 = Vehicle(patente="AUTO2", tipo=VehicleType.AUTO)
    db.add_all([v1, v2])

    # 2 reservas activas el 10 de Septiembre de 14:00 a 15:00 (Llenan la capacidad de 2 autos en esa hora)
    r1 = Reservation(
        patente="AUTO1", sucursal_nombre=branch_name,
        estado_pago=PaymentStatus.PAGADO, estado_reserva=ReservationStatus.ACTIVA,
        fecha_inicio="2026-09-10 14:00", fecha_fin="2026-09-10 15:00",
        tipo_estadia="hora", monto_total=1500.0
    )
    r2 = Reservation(
        patente="AUTO2", sucursal_nombre=branch_name,
        estado_pago=PaymentStatus.PAGADO, estado_reserva=ReservationStatus.ACTIVA,
        fecha_inicio="2026-09-10 14:00", fecha_fin="2026-09-10 15:00",
        tipo_estadia="hora", monto_total=1500.0
    )
    db.add_all([r1, r2])
    db.commit()

    # 1. Intentar reservar el día completo (00:00 a 23:59) -> Debe FALLAR porque a las 14:00-15:00 se superaría la capacidad (2+1=3 > 2)
    disp_dia = verificar_disponibilidad(db, branch_name, "2026-09-10 00:00", "2026-09-10 23:59", tipo_vehiculo="Auto")
    assert disp_dia["disponible"] is False
    assert disp_dia["ocupada"] == 2

    # 2. Intentar reservar la hora 14:00 a 15:00 -> Debe FALLAR (ocupada = 2)
    disp_hora_llena = verificar_disponibilidad(db, branch_name, "2026-09-10 14:00", "2026-09-10 15:00", tipo_vehiculo="Auto")
    assert disp_hora_llena["disponible"] is False

    # 3. Intentar reservar en otra hora del mismo día (10:00 a 11:00) -> Debe SER EXITOSO (ocupada = 0)
    disp_hora_libre = verificar_disponibilidad(db, branch_name, "2026-09-10 10:00", "2026-09-10 11:00", tipo_vehiculo="Auto")
    assert disp_hora_libre["disponible"] is True
    assert disp_hora_libre["ocupada"] == 0
    assert disp_hora_libre["restan"] == 2


def test_disabled_dates_calculation(db):
    """VERIFICA LA GENERACIÓN DE DÍAS Y HORAS DESHABILITADAS."""
    branch_name = "AUTOPASS Morón"
    branch = ParkingBranch(nombre=branch_name, direccion="Av. Morón 123", horario="24hs")
    aforo = ParkingAforo(sucursal=branch_name, capacidad_reservas_autos=1) # Capacidad de 1 auto
    db.add_all([branch, aforo])

    # Crear una reserva de 1 hora que llena la capacidad (1/1) el 2026-09-15 a las 10:00
    v = Vehicle(patente="FULL1", tipo=VehicleType.AUTO)
    r = Reservation(
        patente="FULL1", sucursal_nombre=branch_name,
        estado_pago=PaymentStatus.PAGADO, estado_reserva=ReservationStatus.ACTIVA,
        fecha_inicio="2026-09-15 10:00", fecha_fin="2026-09-15 11:00",
        tipo_estadia="hora", monto_total=1500.0
    )
    db.add_all([v, r])
    db.commit()

    # 1. Para estadía por DÍA, el 2026-09-15 debe estar deshabilitado (ya que en 10:00-11:00 no cabe 1 más)
    disabled_days = obtener_fechas_deshabilitadas(
        db, sucursal_nombre=branch_name, tipo_vehiculo="Auto",
        tipo_estadia="dia", fecha_desde_str="2026-09-15", dias_evaluar=2
    )
    assert "2026-09-15" in disabled_days
    assert "2026-09-16" not in disabled_days

    # 2. Para horas deshabilitadas el 2026-09-15, la hora 10:00 debe figurar como deshabilitada
    disabled_hours = obtener_horas_deshabilitadas(
        db, sucursal_nombre=branch_name, fecha_str="2026-09-15", tipo_vehiculo="Auto"
    )
    assert "10:00" in disabled_hours
    assert "11:00" not in disabled_hours


def test_capacidad_reservas_cero_no_muestra_disponibilidad(db):
    """REGRESION: SI LA SEDE NO TIENE PLAZAS ASIGNADAS PARA RESERVAS (capacidad 0 EXPLICITA),
    NO DEBE MOSTRARSE NINGUN HORARIO COMO DISPONIBLE. ANTES EL FALLBACK A 5 HACIA QUE EL
    PICKER MOSTRARA TODO LIBRE PERO LA RESERVA SE RECHAZARA AL CREARSE."""
    branch_name = "AUTOPASS Ituzaingó"
    branch = ParkingBranch(nombre=branch_name, direccion="Av. Ituzaingó 456", horario="24hs")
    # capacidad_reservas_autos = 0 EXPLICITO: NO HAY PLAZAS PARA RESERVAS DE AUTOS
    aforo = ParkingAforo(sucursal=branch_name, capacidad_total=0, capacidad_reservas_autos=0)
    db.add_all([branch, aforo])
    db.commit()

    # 1. verificar_disponibilidad debe rechazar (NO usar el fallback de 5)
    disp = verificar_disponibilidad(db, branch_name, "2026-09-20 10:00", "2026-09-20 11:00", tipo_vehiculo="Auto")
    assert disp["disponible"] is False
    assert disp["capacidad_total"] == 0
    assert "no cuenta con plazas" in disp["mensaje"]

    # 2. Las horas deshabilitadas deben cubrir TODO el día (no devolver [] y fingir que hay lugar)
    disabled_hours = obtener_horas_deshabilitadas(
        db, sucursal_nombre=branch_name, fecha_str="2026-09-20", tipo_vehiculo="Auto"
    )
    assert "10:00" in disabled_hours
    assert len(disabled_hours) >= 24

    # 3. Las fechas deshabilitadas deben incluir los días evaluados
    disabled_days = obtener_fechas_deshabilitadas(
        db, sucursal_nombre=branch_name, tipo_vehiculo="Auto",
        tipo_estadia="hora", fecha_desde_str="2026-09-20", dias_evaluar=3
    )
    assert "2026-09-20" in disabled_days
    assert "2026-09-22" in disabled_days

    # 4. SI SE CONFIGURA CAPACIDAD POSTERIORMENTE, LA DISPONIBILIDAD VUELVE A FUNCIONAR
    aforo.capacidad_reservas_autos = 2
    db.commit()
    disp2 = verificar_disponibilidad(db, branch_name, "2026-09-20 10:00", "2026-09-20 11:00", tipo_vehiculo="Auto")
    assert disp2["disponible"] is True
    assert disp2["restan"] == 2
