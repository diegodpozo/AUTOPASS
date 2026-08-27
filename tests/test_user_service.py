import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User
from models.enums import UserRole
from services.user_service import UserService
from schemas import UserCreate, UserAdminUpdate

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

def test_local_admin_permissions_on_branch_users(db):
    from routes.admin.users import delete_user, update_user_admin, change_user_role
    from schemas import UserAdminUpdate

    local_admin = User(nombre="AdminLocal", apellido="Moron", dni="11111111", email="admmoron@test.com", password_hash="hash", rol=UserRole.LOCAL_ADMIN, sucursal="AUTOPASS Morón")
    staff = User(nombre="Pedro", apellido="Staff", dni="22222222", email="staff@test.com", password_hash="hash", rol=UserRole.STAFF, sucursal="Morón")
    client = User(nombre="Maria", apellido="Cliente", dni="33333333", email="maria@test.com", password_hash="hash", rol=UserRole.USER, sucursal=None)
    global_admin = User(nombre="SuperAdmin", apellido="Global", dni="44444444", email="admin@test.com", password_hash="hash", rol=UserRole.ADMIN, sucursal=None)
    
    db.add_all([local_admin, staff, client, global_admin])
    db.commit()

    # 1. Local admin can edit staff in their branch (with normalized sucursal)
    up = UserAdminUpdate(nombre="PedroEditado")
    res_up = update_user_admin(staff.id, up, db=db, admin=local_admin)
    assert res_up["status"] == "ok"

    # 2. Local admin can change role of staff in their branch
    res_role = change_user_role(staff.id, UserRole.STAFF, db=db, admin=local_admin)
    assert res_role["status"] == "ok"

    # 3. Local admin can delete staff in their branch
    res_del = delete_user(staff.id, db=db, admin=local_admin)
    assert res_del["status"] == "ok"
    assert staff.is_deleted is True

    # 4. Local admin CANNOT delete Global Admin
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        delete_user(global_admin.id, db=db, admin=local_admin)
    assert exc.value.status_code == 403

