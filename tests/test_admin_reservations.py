import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Reservation, ParkingBranch, ParkingAforo, User, Vehicle
from models.enums import ReservationStatus, PaymentStatus
from services.reservation_service import ReservationService, verificar_disponibilidad
from schemas import AdminReservationCreate
from routes.admin.reservations import create_admin_reservation, patente_lookup

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    branch = ParkingBranch(nombre="Sucursal Central", direccion="Av. Test 123", horario="24hs", is_24h=True)
    db.add(branch)
    db.add(ParkingAforo(sucursal="Sucursal Central", capacidad_reservas_autos=2))
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def _cliente(db):
    user = User(nombre="Cliente", apellido="Test", dni="12345678", email="cliente@test.com",
                rol="user", sucursal="Sucursal Central", saldo=5000.0, puntos_acumulados=0)
    db.add(user)
    db.commit()
    return user


def _reserva_data(patente="ABC123", **overrides):
    base = {
        "user_id": None,
        "patente": patente,
        "fecha_inicio": "2026-07-10 10:00",
        "fecha_fin": "2026-07-10 12:00",
        "tipo_estadia": "hora",
        "sucursal_nombre": "Sucursal Central",
    }
    base.update(overrides)
    return AdminReservationCreate(**base)


def test_pay_reservation_manual_marca_pagado_sin_tocar_saldo(db):
    user = _cliente(db)
    data = _reserva_data(user_id=user.id, cliente_nombre="Cliente Test")
    res = ReservationService.create_reservation(db, data)
    assert res.estado_pago == PaymentStatus.PENDIENTE
    assert res.estado_reserva == ReservationStatus.PENDIENTE

    saldo_inicial = user.saldo
    puntos_iniciales = user.puntos_acumulados

    resultado = ReservationService.pay_reservation_manual(db, res, "Efectivo")
    db.refresh(user)

    assert resultado["status"] == "ok"
    assert res.estado_pago == PaymentStatus.PAGADO
    assert res.estado_reserva == ReservationStatus.ACTIVA
    assert res.metodo_pago == "Efectivo"
    assert res.fecha_pago is not None
    assert user.saldo == saldo_inicial
    assert user.puntos_acumulados >= puntos_iniciales


def test_pay_reservation_manual_idempotente(db):
    user = _cliente(db)
    data = _reserva_data(user_id=user.id, cliente_nombre="Cliente Test")
    res = ReservationService.create_reservation(db, data)
    ReservationService.pay_reservation_manual(db, res, "Transferencia")
    second = ReservationService.pay_reservation_manual(db, res, "Tarjeta")
    assert second["status"] == "ok"
    assert res.metodo_pago == "Transferencia"


def test_create_admin_reservation_con_pago_crea_y_registra_pago(db):
    staff = User(nombre="Operador", apellido="Staff", dni="87654321", email="staff@test.com",
                 rol="staff", sucursal="Sucursal Central", saldo=0.0)
    db.add(staff)
    db.commit()

    data = _reserva_data(pagar=True, metodo_pago="Mercado Pago")
    resultado = create_admin_reservation(data, db, staff)

    assert resultado["status"] == "ok"
    assert resultado["pagado"] is True
    assert resultado["metodo_pago"] == "Mercado Pago"

    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    assert res.estado_pago == PaymentStatus.PAGADO
    assert res.estado_reserva == ReservationStatus.ACTIVA
    assert res.metodo_pago == "Mercado Pago"
    assert res.sucursal_nombre == "Sucursal Central"


def test_create_admin_reservation_sin_pago_queda_pendiente(db):
    staff = User(nombre="Operador", apellido="Staff", dni="87654321", email="staff@test.com",
                 rol="staff", sucursal="Sucursal Central", saldo=0.0)
    db.add(staff)
    db.commit()

    data = _reserva_data()
    resultado = create_admin_reservation(data, db, staff)

    assert resultado["status"] == "ok"
    assert resultado["pagado"] is False

    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    assert res.estado_pago == PaymentStatus.PENDIENTE
    assert res.estado_reserva == ReservationStatus.PENDIENTE
    assert res.metodo_pago is None


def test_create_admin_reservation_staff_no_cambia_sucursal(db):
    staff = User(nombre="Operador", apellido="Staff", dni="87654321", email="staff@test.com",
                 rol="staff", sucursal="Sucursal Central", saldo=0.0)
    db.add(staff)
    db.commit()

    data = _reserva_data(sucursal_nombre="Sucursal Otra", pagar=True, metodo_pago="Efectivo")
    resultado = create_admin_reservation(data, db, staff)

    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    assert res.sucursal_nombre == "Sucursal Central"


def test_create_admin_reservation_admin_si_cambia_sucursal(db):
    db.add(ParkingBranch(nombre="Sucursal Dos", direccion="Av. Test 456", horario="24hs", is_24h=True))
    db.add(ParkingAforo(sucursal="Sucursal Dos", capacidad_reservas_autos=2))
    db.commit()

    admin = User(nombre="Admin", apellido="Global", dni="11111111", email="admin@test.com",
                 rol="admin", sucursal=None, saldo=0.0)
    db.add(admin)
    db.commit()

    data = _reserva_data(sucursal_nombre="Sucursal Dos", pagar=True, metodo_pago="Efectivo")
    resultado = create_admin_reservation(data, db, admin)

    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    assert res.sucursal_nombre == "Sucursal Dos"


def test_create_admin_reservation_persiste_tipo_vehiculo(db):
    staff = User(nombre="Operador", apellido="Staff", dni="87654321", email="staff@test.com",
                 rol="staff", sucursal="Sucursal Central", saldo=0.0)
    db.add(staff)
    db.commit()

    data = _reserva_data(tipo_vehiculo="Camioneta", pagar=True, metodo_pago="Efectivo")
    resultado = create_admin_reservation(data, db, staff)

    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    assert res.tipo_vehiculo == "Camioneta"


def test_disponibilidad_considera_tipo_vehiculo_de_reserva_manual(db):
    data = _reserva_data(tipo_vehiculo="Moto")
    res = ReservationService.create_reservation(db, data)
    assert res.tipo_vehiculo == "Moto"

    disp_moto = verificar_disponibilidad(db, "Sucursal Central", "2026-07-10 10:00", "2026-07-10 12:00", tipo_vehiculo="Moto")
    disp_auto = verificar_disponibilidad(db, "Sucursal Central", "2026-07-10 10:00", "2026-07-10 12:00", tipo_vehiculo="Auto")

    assert disp_moto["disponible"] is True
    assert disp_moto["ocupada"] == 1
    assert disp_auto["ocupada"] == 0


def _cliente_con_vehiculo(db, patente="ABC 123", tipo="Moto"):
    user = User(nombre="Cliente", apellido="Test", dni="12345678", email="cliente@test.com",
                rol="user", sucursal="Sucursal Central", saldo=5000.0, puntos_acumulados=0)
    db.add(user)
    db.commit()
    db.add(Vehicle(user_id=user.id, patente=patente, tipo=tipo))
    db.commit()
    return user


def _staff(db):
    staff = User(nombre="Operador", apellido="Staff", dni="87654321", email="staff@test.com",
                 rol="staff", sucursal="Sucursal Central", saldo=0.0)
    db.add(staff)
    db.commit()
    return staff


def test_patente_lookup_encuentra_dueno_registrado(db):
    user = _cliente_con_vehiculo(db, patente="ABC 123", tipo="Moto")
    staff = _staff(db)

    resultado = patente_lookup("abc123", db, staff)

    assert resultado["encontrado"] is True
    assert resultado["user_id"] == user.id
    assert resultado["nombre"] == "Cliente"
    assert resultado["apellido"] == "Test"
    assert resultado["tipo_vehiculo"] == "Moto"


def test_patente_lookup_no_encontrada(db):
    staff = _staff(db)
    resultado = patente_lookup("ZZZ999", db, staff)
    assert resultado["encontrado"] is False


def test_patente_lookup_ignora_patentes_cortas(db):
    staff = _staff(db)
    resultado = patente_lookup("ab", db, staff)
    assert resultado["encontrado"] is False


def test_create_admin_reservation_vincula_usuario_por_patente(db):
    user = _cliente_con_vehiculo(db, patente="ABC 123", tipo="Auto")
    staff = _staff(db)

    data = _reserva_data(patente="abc123", user_id=user.id, pagar=True, metodo_pago="Efectivo", tipo_vehiculo="Auto")
    resultado = create_admin_reservation(data, db, staff)

    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    assert res.user_id == user.id
    assert res.estado_pago == PaymentStatus.PAGADO
    db.refresh(user)
    assert user.puntos_acumulados > 0