import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from models.enums import VehicleType, AccessEventType
from services.access_service import AccessService
from schemas import PlateValidation
from core.database import get_db

# Setup test database
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

def test_validate_plate_success(db):
    # Setup: Create necessary entities (Vehicle, ParkingAforo)
    # This is a simplified test; in a full suite, you'd mock or seed proper data
    data = PlateValidation(plate="ABC1234", gate_id="TEST_ENTRADA")
    
    # Run test
    result = AccessService.validate_plate(db, data)
    
    # Assert
    assert result["status"] == "allowed"
    assert "Acceso permitido" in result["message"]
