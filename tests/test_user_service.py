import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User
from models.enums import UserRole
from services.user_service import UserService
from schemas import UserCreate, UserAdminUpdate

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

def test_create_user_success(db):
    data = UserCreate(nombre="Juan", apellido="Perez", dni="12345678", telefono="1111111111", email="juan@test.com", password="Password123!")
    user = UserService.create_user(db, data, rol=UserRole.USER)
    assert user.email == "juan@test.com"
    assert user.rol == UserRole.USER

def test_update_user_success(db):
    data = UserCreate(nombre="Juan", apellido="Perez", dni="12345678", telefono="1111111111", email="juan@test.com", password="Password123!")
    user = UserService.create_user(db, data, rol=UserRole.USER)
    
    update_data = UserAdminUpdate(nombre="JuanNuevo")
    updated = UserService.update_user(db, user.id, update_data)
    assert updated.nombre == "Juannuevo"
