import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
from models import Base
from models.enums import VehicleType
from services.billing_service import BillingService
from core.cache import ttl_cache

#CONFIGURACION DE BASE DE DATOS DE PRUEBA
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    ttl_cache.invalidate()
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)
    ttl_cache.invalidate()

def test_calculate_total_amount_hora(db):
    db.add(models.Settings(clave="precio_hora", valor=1500.0, sucursal=None))
    db.add(models.Settings(clave="precio_30min", valor=750.0, sucursal=None))
    db.commit()
    monto = BillingService.calculate_total_amount(
        db, "hora", "2026-06-12T10:00:00", "2026-06-12T12:00:00", 
        tipo_vehiculo=VehicleType.AUTO
    )
    #2 HORAS = 4 BLOQUES DE 30 MIN = 3000
    assert monto == 3000.0

def test_calculate_total_amount_sin_tarifario_devuelve_none(db):
    monto = BillingService.calculate_total_amount(
        db, "hora", "2026-06-12T10:00:00", "2026-06-12T12:00:00",
        tipo_vehiculo=VehicleType.AUTO
    )
    assert monto is None

def test_get_rate_estricta_por_sucursal(db):
    db.add(models.ParkingBranch(nombre="Centro", direccion="d", horario="24hs"))
    db.add(models.Settings(clave="precio_hora", valor=1800.0, sucursal=None))
    db.add(models.Settings(clave="precio_hora", valor=2200.0, sucursal="Centro"))
    db.commit()
    assert BillingService.get_rate(db, "hora", sucursal="Centro", tipo_vehiculo=VehicleType.AUTO) == 2200.0
    assert BillingService.get_rate(db, "hora", sucursal="Otra", tipo_vehiculo=VehicleType.AUTO) is None
