import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, ParkingAforo, ParkingBranch, ParkingFloor, AccessLog, Reservation, Vehicle
from models.enums import AccessEventType, ReservationStatus, PaymentStatus, VehicleType
from services.access_service import AccessService
from services.reservation_service import verificar_disponibilidad
from schemas import PlateValidation

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

def test_exclusive_reservation_spots_logic(db):
    branch_name = "AUTOPASS Test"
    branch = ParkingBranch(nombre=branch_name, direccion="Av. Test 100", horario="24hs")
    aforo = ParkingAforo(
        sucursal=branch_name,
        capacidad_total=10,
        ocupacion_actual=0,
        capacidad_motos=5,
        ocupacion_motos=0,
        capacidad_camionetas=3,
        ocupacion_camionetas=0,
        capacidad_reservas=5,
        capacidad_reservas_autos=2,
        capacidad_reservas_motos=2,
        capacidad_reservas_camionetas=1,
        ocupacion_reservas=0,
        ocupacion_reservas_autos=0,
        ocupacion_reservas_motos=0,
        ocupacion_reservas_camionetas=0
    )
    db.add_all([branch, aforo])
    db.commit()

    # 1. Ingreso rotativo sin reserva debe incrementar ocupacion_actual (autos), NO ocupacion_reservas
    res_rot = AccessService.validate_plate(db, PlateValidation(plate="ROT123", gate_id="AUTOPASS Test_ENTRADA"))
    assert res_rot["status"] == "allowed"
    db.refresh(aforo)
    assert aforo.ocupacion_actual == 1
    assert aforo.ocupacion_reservas == 0
    assert aforo.ocupacion_reservas_autos == 0

    # 2. Crear vehículos y reservas vigentes y pagadas para Auto y Moto
    v_auto = Vehicle(patente="RES789", tipo=VehicleType.AUTO)
    v_moto = Vehicle(patente="MOTO99", tipo=VehicleType.MOTO)
    db.add_all([v_auto, v_moto])
    
    reserva_auto = Reservation(
        patente="RES789",
        sucursal_nombre=branch_name,
        estado_pago=PaymentStatus.PAGADO,
        estado_reserva=ReservationStatus.PENDIENTE,
        fecha_inicio="2026-09-05 00:00",
        fecha_fin="2026-09-05 23:59",
        monto_total=1500.0,
        tipo_estadia="hora"
    )
    reserva_moto = Reservation(
        patente="MOTO99",
        sucursal_nombre=branch_name,
        estado_pago=PaymentStatus.PAGADO,
        estado_reserva=ReservationStatus.PENDIENTE,
        fecha_inicio="2026-09-05 00:00",
        fecha_fin="2026-09-05 23:59",
        monto_total=800.0,
        tipo_estadia="hora"
    )
    db.add_all([reserva_auto, reserva_moto])
    db.commit()

    # 3. Verificar disponibilidad por tipo de vehículo
    disp_auto = verificar_disponibilidad(db, branch_name, "2026-09-05 10:00", "2026-09-05 14:00", tipo_vehiculo="Auto")
    assert disp_auto["disponible"] is True
    assert disp_auto["capacidad_total"] == 2
    assert disp_auto["ocupada"] == 1

    disp_moto = verificar_disponibilidad(db, branch_name, "2026-09-05 10:00", "2026-09-05 14:00", tipo_vehiculo="Moto")
    assert disp_moto["disponible"] is True
    assert disp_moto["capacidad_total"] == 2
    assert disp_moto["ocupada"] == 1

    # 4. Ingreso con reserva para Auto y Moto debe incrementar ocupacion_reservas y su tipo trimodal específico
    res_res_auto = AccessService.validate_plate(db, PlateValidation(plate="RES789", gate_id="AUTOPASS Test_ENTRADA"))
    assert res_res_auto["status"] == "allowed"
    db.refresh(aforo)
    assert aforo.ocupacion_actual == 1
    assert aforo.ocupacion_reservas == 1
    assert aforo.ocupacion_reservas_autos == 1

    res_res_moto = AccessService.validate_plate(db, PlateValidation(plate="MOTO99", gate_id="AUTOPASS Test_ENTRADA"))
    assert res_res_moto["status"] == "allowed"
    db.refresh(aforo)
    assert aforo.ocupacion_motos == 0  # Rotative moto spot untouched!
    assert aforo.ocupacion_reservas == 2
    assert aforo.ocupacion_reservas_motos == 1

    # 5. Salida del vehículo con reserva decrementa ocupacion_reservas y ocupacion_reservas_autos/motos
    res_exit_auto = AccessService.exit_plate(db, PlateValidation(plate="RES789", gate_id="AUTOPASS Test_SALIDA"))
    assert res_exit_auto["status"] == "allowed"
    db.refresh(aforo)
    assert aforo.ocupacion_reservas == 1
    assert aforo.ocupacion_reservas_autos == 0

    res_exit_moto = AccessService.exit_plate(db, PlateValidation(plate="MOTO99", gate_id="AUTOPASS Test_SALIDA"))
    assert res_exit_moto["status"] == "allowed"
    db.refresh(aforo)
    assert aforo.ocupacion_reservas == 0
    assert aforo.ocupacion_reservas_motos == 0

