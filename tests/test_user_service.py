import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request
from models import Base, User, Vehicle, Reservation
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
    fake_request = Request({"type": "http", "method": "POST", "path": "/", "headers": [], "client": ("127.0.0.1", 12345), "server": ("test", 80), "scheme": "http", "query_string": b""})
    res_role = change_user_role(fake_request, staff.id, UserRole.STAFF, db=db, admin=local_admin)
    assert res_role["status"] == "ok"

    # 3. Local admin can delete staff in their branch
    res_del = delete_user(fake_request, staff.id, db=db, admin=local_admin)
    assert res_del["status"] == "ok"
    assert staff.is_deleted is True

    # 4. Local admin CANNOT delete Global Admin
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        delete_user(fake_request, global_admin.id, db=db, admin=local_admin)
    assert exc.value.status_code == 403

def _make_user(db):
    data = UserCreate(nombre="Juan", apellido="Perez", dni="12345678", telefono="1111111111", email="juan@test.com", password="Password123!")
    return UserService.create_user(db, data, rol=UserRole.USER)

def test_add_vehicle_success(db):
    user = _make_user(db)
    res = UserService.add_vehicle(db, user, "AB 123 CD", "Ford Ka", "Auto")
    assert res["status"] == "ok"
    vehicles = UserService.list_vehicles(db, user.id)
    assert len(vehicles) == 1
    assert vehicles[0].patente == "AB123CD"
    assert vehicles[0].marca_modelo == "Ford Ka"

def test_add_vehicle_invalid_plate(db):
    user = _make_user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        UserService.add_vehicle(db, user, "XYZ", "Ford", "Auto")
    assert exc.value.status_code == 400

def test_add_vehicle_duplicate(db):
    user = _make_user(db)
    UserService.add_vehicle(db, user, "AB 123 CD", "Ford Ka", "Auto")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        UserService.add_vehicle(db, user, "AB123CD", "Ford Ka", "Auto")
    assert exc.value.status_code == 400

def test_set_favorite_vehicle_toggle(db):
    user = _make_user(db)
    UserService.add_vehicle(db, user, "AB 123 CD", "Ford Ka", "Auto")
    UserService.add_vehicle(db, user, "AA 111 BB", "Honda Fit", "Auto")
    first = UserService.list_vehicles(db, user.id)[0].patente

    res = UserService.set_favorite_vehicle(db, user, first)
    assert res["is_favorite"] is True
    res2 = UserService.set_favorite_vehicle(db, user, first)
    assert res2["is_favorite"] is False

def test_delete_vehicle_reassigns_favorite(db):
    user = _make_user(db)
    UserService.add_vehicle(db, user, "AB 123 CD", "Ford Ka", "Auto")
    UserService.add_vehicle(db, user, "AA 111 BB", "Honda Fit", "Auto")
    UserService.set_favorite_vehicle(db, user, "AB 123 CD")

    UserService.delete_vehicle(db, user, "AB 123 CD")

    remaining = UserService.list_vehicles(db, user.id)
    assert len(remaining) == 1
    assert remaining[0].is_favorite is True

def test_delete_vehicle_blocks_active_reservation(db):
    import datetime
    user = _make_user(db)
    UserService.add_vehicle(db, user, "AB 123 CD", "Ford Ka", "Auto")
    vehicle = UserService.list_vehicles(db, user.id)[0]

    now = datetime.datetime.now()
    res = Reservation(
        user_id=user.id,
        patente=vehicle.patente,
        sucursal_nombre="AUTOPASS Morón",
        fecha_inicio=(now - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
        fecha_fin=(now + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
        estado_reserva="Pendiente",
        estado_pago="Pendiente",
        monto_total=100
    )
    db.add(res)
    db.commit()

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        UserService.delete_vehicle(db, user, "AB 123 CD")
    assert exc.value.status_code == 400

