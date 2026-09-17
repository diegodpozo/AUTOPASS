import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, ParkingBranch, ParkingAforo, ParkingFloor
from services.branch_service import BranchService

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

def test_get_branch_capacity_summary(db):
    branch = ParkingBranch(nombre="TestBranch", direccion="Dir", horario="24hs")
    db.add(branch)
    db.commit()
    
    aforo_pb = ParkingAforo(sucursal="TestBranch", capacidad_total=20, capacidad_motos=10)
    db.add(aforo_pb)
    
    floor = ParkingFloor(branch_id=branch.id, nombre="Piso 1", capacidad_total=10, capacidad_motos=5)
    db.add(floor)
    db.commit()
    
    summary = BranchService.get_branch_capacity_summary(db, branch)
    
    # 20 (PB) + 10 (PISO) = 30
    assert summary["capacidad_autos_total"] == 30
    # 10 (PB) + 5 (PISO) = 15
    assert summary["capacidad_motos_total"] == 15
    # 5 (PB) + 5 (PISO) = 10
    assert summary["capacidad_camionetas_total"] == 10

def test_rename_branch_propagates(db):
    branch = ParkingBranch(nombre="Vieja", direccion="Dir", horario="24hs")
    db.add(branch)
    db.add(ParkingAforo(sucursal="Vieja", capacidad_total=20, capacidad_motos=10))
    db.commit()

    BranchService.rename_branch(db, branch, "Nueva Sede")

    assert branch.nombre == "Nueva Sede"
    aforo = db.query(ParkingAforo).filter(ParkingAforo.sucursal == "Nueva Sede").first()
    assert aforo is not None
    assert aforo.capacidad_total == 20

def test_rename_branch_same_name_is_noop(db):
    branch = ParkingBranch(nombre="Igual", direccion="Dir", horario="24hs")
    db.add(branch)
    db.commit()

    BranchService.rename_branch(db, branch, "Igual")

    assert branch.nombre == "Igual"

def test_has_physical_occupancy(db):
    branch = ParkingBranch(nombre="Ocupada", direccion="Dir", horario="24hs")
    db.add(branch)
    db.add(ParkingAforo(sucursal="Ocupada", capacidad_total=20, capacidad_motos=10, ocupacion_actual=3))
    db.commit()

    assert BranchService.has_physical_occupancy(db, branch) is True

    db.query(ParkingAforo).filter(ParkingAforo.sucursal == "Ocupada").delete()
    db.commit()
    assert BranchService.has_physical_occupancy(db, branch) is False
