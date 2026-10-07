import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Reservation, ParkingBranch, Settings
from models.enums import ReservationStatus, PaymentStatus, VehicleType
from services.reservation_service import ReservationService
from schemas import AdminReservationCreate

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

def test_create_reservation_success(db):
    #CONFIGURAR SUCURSAL
    branch = ParkingBranch(nombre="TestBranch", direccion="Calle Falsa 123", horario="24hs")
    db.add(branch)
    db.add(Settings(clave="precio_hora", valor=1500.0, sucursal="TestBranch"))
    db.add(Settings(clave="precio_30min", valor=750.0, sucursal="TestBranch"))
    db.commit()
    
    data = AdminReservationCreate(
        user_id=None,
        patente="ABC1234",
        fecha_inicio="2026-06-20T10:00:00",
        fecha_fin="2026-06-20T12:00:00",
        tipo_estadia="hora",
        sucursal_nombre="TestBranch",
        cliente_nombre="Juan Test"
    )
    res = ReservationService.create_reservation(db, data)
    assert res.estado_reserva == ReservationStatus.PENDIENTE
    assert res.estado_pago == PaymentStatus.PENDIENTE

def test_branch_info_str_resolution(db):
    from services.branch_service import BranchService
    branch = ParkingBranch(nombre="AUTOPASS Castelar", direccion="Montes de Oca 1220, Castelar", horario="24hs", is_24h=True)
    db.add(branch)
    db.commit()

    info = BranchService.get_branch_info_str(db, "AUTOPASS Castelar")
    assert "Montes de Oca 1220" in info
    assert "Abierto 24hs" in info

    # Búsqueda insensible/parcial
    info_partial = BranchService.get_branch_info_str(db, "Castelar")
    assert "Montes de Oca 1220" in info_partial

