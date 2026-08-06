import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, ParkingBranch, ParkingAforo
from models.enums import VehicleType, AccessEventType, PaymentStatus
from services.access_service import AccessService
from schemas import PlateValidation

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Seed default branch and aforo
    branch = ParkingBranch(id=1, nombre="Centro", direccion="Av. Principal 123", activa=True)
    aforo = ParkingAforo(id=1, sucursal="Centro", capacidad_total=50, ocupacion_actual=0)
    db.add(branch)
    db.add(aforo)
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_validate_plate_new_entry(db):
    data = PlateValidation(plate="AA123BB", gate_id="Centro_ENTRADA")
    result = AccessService.validate_plate(db, data)
    assert result["status"] == "allowed"
    assert "Acceso permitido" in result["message"]

    # Check that occupancy increased
    aforo = db.query(ParkingAforo).filter_by(sucursal="Centro").first()
    assert aforo.ocupacion_actual == 1

def test_validate_plate_duplicate_entry(db):
    data = PlateValidation(plate="AA123BB", gate_id="Centro_ENTRADA")
    # First entry
    res1 = AccessService.validate_plate(db, data)
    assert res1["status"] == "allowed"

    # Second entry while inside
    res2 = AccessService.validate_plate(db, data)
    assert res2["status"] == "denied"
    assert "ya figura dentro" in res2["message"]

def test_exit_plate_courtesy_time(db):
    data_in = PlateValidation(plate="CC789DD", gate_id="Centro_ENTRADA")
    res_in = AccessService.validate_plate(db, data_in)
    assert res_in["status"] == "allowed"

    # Exit immediately (well within 10-minute courtesy period)
    data_out = PlateValidation(plate="CC789DD", gate_id="Centro_SALIDA")
    res_out = AccessService.exit_plate(db, data_out)
    assert res_out["status"] == "allowed"
    assert "Salida autorizada" in res_out["message"]

    # Check that occupancy decreased back to 0
    aforo = db.query(ParkingAforo).filter_by(sucursal="Centro").first()
    assert aforo.ocupacion_actual == 0
