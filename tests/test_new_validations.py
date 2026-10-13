import datetime
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Vehicle, Reservation, AccessLog, ParkingBranch, ParkingFloor, ParkingAforo
from models.enums import UserRole, VehicleType, ReservationStatus, PaymentStatus
from services.user_service import UserService
from services.reservation_service import ReservationService
from schemas import UserAdminUpdate

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

def test_delete_vehicle_with_active_reservation_fails(db):
    from routes.user.vehicles import delete_user_vehicle
    user = User(nombre="Juan", email="juan@test.com", password_hash="pwd", rol="user")
    db.add(user)
    db.commit()

    vehicle = Vehicle(user_id=user.id, patente="AA 123 BB", tipo="Auto")
    db.add(vehicle)
    db.commit()

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    future_str = (datetime.datetime.now() + datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
    res = Reservation(user_id=user.id, patente="AA 123 BB", fecha_inicio=now_str, fecha_fin=future_str, estado_reserva="Activa", estado_pago="Pagado")
    db.add(res)
    db.commit()

    with pytest.raises(HTTPException) as exc:
        delete_user_vehicle("AA 123 BB", db, user)
    assert exc.value.status_code == 400
    assert "reservas activas" in exc.value.detail

def test_delete_vehicle_parked_inside_fails(db):
    from routes.user.vehicles import delete_user_vehicle
    user = User(nombre="Juan", email="juan@test.com", password_hash="pwd", rol="user")
    db.add(user)
    db.commit()

    vehicle = Vehicle(user_id=user.id, patente="AA 999 BB", tipo="Auto")
    db.add(vehicle)
    db.commit()

    log = AccessLog(patente_detectada="AA999BB", normalized_patente="AA999BB", tipo_evento="ENTRADA", fecha_hora="2026-08-15 10:00")
    db.add(log)
    db.commit()

    with pytest.raises(HTTPException) as exc:
        delete_user_vehicle("AA 999 BB", db, user)
    assert exc.value.status_code == 400
    assert "ingresado" in exc.value.detail

def test_add_vehicle_camioneta_and_blocked_check(db):
    from routes.user.vehicles import add_user_vehicle
    from schemas import VehicleCreate
    user = User(nombre="Pedro", email="pedro@test.com", password_hash="pwd", rol="user", is_blocked=True)
    db.add(user)
    db.commit()

    with pytest.raises(HTTPException) as exc:
        add_user_vehicle(VehicleCreate(patente="AB 123 CD", marca_modelo="Toyota Hilux", tipo="Camioneta"), db, user)
    assert exc.value.status_code == 403

    user.is_blocked = False
    db.commit()

    res = add_user_vehicle(VehicleCreate(patente="AB 123 CD", marca_modelo="Toyota Hilux", tipo="Camioneta"), db, user)
    assert res["status"] == "ok"
    veh = db.query(Vehicle).filter(Vehicle.patente == "AB123CD").first()
    assert veh is not None
    assert veh.tipo == "Camioneta"

def test_update_user_duplicate_email_fails(db):
    u1 = User(nombre="U1", email="u1@test.com", dni="11111111", password_hash="pwd")
    u2 = User(nombre="U2", email="u2@test.com", dni="22222222", password_hash="pwd")
    db.add_all([u1, u2])
    db.commit()

    with pytest.raises(HTTPException) as exc:
        UserService.update_user(db, u2.id, UserAdminUpdate(email="u1@test.com"))
    assert exc.value.status_code == 400
    assert "correo ya está registrado" in exc.value.detail

def test_delete_floor_with_occupancy_fails(db):
    from routes.admin.branches import delete_floor
    admin = User(nombre="Admin", email="admin@test.com", rol="admin")
    floor = ParkingFloor(nombre="Piso 1", capacidad_total=10, ocupacion_actual=1)
    db.add_all([admin, floor])
    db.commit()

    with pytest.raises(HTTPException) as exc:
        delete_floor(floor.id, db, admin)
    assert exc.value.status_code == 400
    assert "vehículos actualmente estacionados" in exc.value.detail


def test_is_valid_plate_formatos_latam_reconocidos():
    from core.normalize import is_valid_plate
    for p in ["ABC123", "AB123CD", "123ABC", "A123BCD", "ABC1234", "ABC1D23", "ABCD123", "1234ABC"]:
        assert is_valid_plate(p), f"deberia ser valida: {p}"
    for p in ["AC404", "AC404S", "MOTO12", "ZZ000", "AA123", "12345", "", "AB 1", "A123"]:
        assert not is_valid_plate(p), f"deberia ser invalida: {p}"


def test_add_vehicle_rechaza_formato_invalido(db):
    from routes.user.vehicles import add_user_vehicle
    from schemas import VehicleCreate
    user = User(nombre="Ana", email="ana@test.com", password_hash="pwd", rol="user")
    db.add(user)
    db.commit()
    with pytest.raises(HTTPException) as exc:
        add_user_vehicle(VehicleCreate(patente="AC404", marca_modelo="Fiat", tipo="Auto"), db, user)
    assert exc.value.status_code == 400
    assert "Formato de patente inválido" in exc.value.detail
    assert db.query(Vehicle).count() == 0


def test_validate_plate_rechaza_formato_y_no_registra(db):
    from services.access_service import AccessService
    from schemas import PlateValidation
    db.add(ParkingBranch(nombre="Centro", direccion="Av X", activa=True))
    db.add(ParkingAforo(sucursal="Centro", capacidad_total=10, ocupacion_actual=0,
                        capacidad_motos=5, ocupacion_motos=0))
    db.commit()
    res = AccessService.validate_plate(db, PlateValidation(plate="AC404", gate_id="Centro_ENTRADA"))
    assert res["status"] == "denied"
    assert "Formato de patente inválido" in res["message"]
    assert db.query(AccessLog).count() == 0


def test_manual_entry_rechaza_formato_invalido(db):
    from services.access_service import AccessService
    with pytest.raises(HTTPException) as exc:
        AccessService.manual_entry(db, "MOTO12", "Centro")
    assert exc.value.status_code == 400
    assert "Formato de patente inválido" in exc.value.detail


def test_process_payment_rechaza_formato_invalido(db):
    from services.billing_service import BillingService
    res = BillingService.process_payment(db, "AC404")
    assert res["status"] == "error"
    assert "Formato de patente inválido" in res["message"]
