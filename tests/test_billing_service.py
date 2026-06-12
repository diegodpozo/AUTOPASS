import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from models.enums import VehicleType
from services.billing_service import BillingService

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

def test_calculate_total_amount_hora(db):
    # Mocking necessary settings or just testing math logic
    # In a real scenario, seed Settings table
    monto = BillingService.calculate_total_amount(
        db, "hora", "2026-06-12T10:00:00", "2026-06-12T12:00:00", 
        tipo_vehiculo=VehicleType.AUTO
    )
    # Default base rate is 1000, 2 hours = 2000
    assert monto == 2000.0
