import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from models.enums import VehicleType
from services.billing_service import BillingService

#CONFIGURACION DE BASE DE DATOS DE PRUEBA
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
    #SIMULANDO AJUSTES NECESARIOS O SOLO PROBANDO LOGICA MATEMATICA
    #EN UN ESCENARIO REAL, SEMBRAR TABLA DE AJUSTES
    monto = BillingService.calculate_total_amount(
        db, "hora", "2026-06-12T10:00:00", "2026-06-12T12:00:00", 
        tipo_vehiculo=VehicleType.AUTO
    )
    #LA FRACCION 30 MIN FALLA BACK A LA MITAD DE LA TARIFA HORA DEFAULT (1500/2=750)
    #2 HORAS = 4 BLOQUES DE 30 MIN = 3000
    assert monto == 3000.0
