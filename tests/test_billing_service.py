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
    #2 HORAS = 4 BLOQUES -> 2 HORAS + 1 FRACCION = 2*1500 + 750
    assert monto == 3750.0


@pytest.mark.parametrize("horas,esperado", [
    (0.5, 750.0),    # 1 BLOQUE -> FRACCION
    (0.75, 1500.0),  # 2 BLOQUES -> HORA (REEMPLAZA LA FRACCION)
    (1.0, 1500.0),   # 2 BLOQUES -> HORA
    (1.25, 2250.0),  # 3 BLOQUES -> HORA + FRACCION
    (1.5, 2250.0),   # 3 BLOQUES -> HORA + FRACCION
    (2.0, 3750.0),   # 4 BLOQUES -> 2 HORAS + FRACCION
    (2.5, 4500.0),   # 5 BLOQUES -> 2 HORAS + 2 FRACCIONES
])
def test_calculate_hourly_amount_escalonado(db, horas, esperado):
    db.add(models.Settings(clave="precio_hora", valor=1500.0, sucursal=None))
    db.add(models.Settings(clave="precio_30min", valor=750.0, sucursal=None))
    db.commit()
    assert BillingService.calculate_hourly_amount(db, horas) == esperado


def test_hourly_amount_from_rates_fallbacks(db):
    # SOLO HORA -> FRACCION = HORA / 2
    assert BillingService.hourly_amount_from_rates(0.5, 1000.0, None) == 500.0
    assert BillingService.hourly_amount_from_rates(1.25, 1000.0, None) == 1500.0
    # SOLO FRACCION -> HORA = FRACCION * 2
    assert BillingService.hourly_amount_from_rates(1.25, None, 400.0) == 1200.0
    # SIN TARIFAS -> NONE
    assert BillingService.hourly_amount_from_rates(1.0, None, None) is None


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
