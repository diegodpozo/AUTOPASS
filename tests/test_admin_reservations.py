import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Reservation, ParkingBranch, ParkingAforo, User, Vehicle, RedemptionTicket, Settings
from models.enums import ReservationStatus, PaymentStatus
from services.reservation_service import ReservationService, verificar_disponibilidad, obtener_horas_deshabilitadas_con_reservas
from services.report_service import ReportService
from services.billing_service import BillingService
from schemas import AdminReservationCreate, ConfirmPaymentRequest
from routes.admin.reservations import (
    create_admin_reservation, update_admin_reservation, patente_lookup,
    confirm_reservation_payment, reservation_available_redemptions, admin_available_redemptions,
    reservation_redemption_info, get_new_reservations_count
)

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
    for suc in ("Sucursal Central", "Sucursal Dos"):
        db.add(Settings(clave="precio_hora", valor=1500.0, sucursal=suc))
        db.add(Settings(clave="precio_30min", valor=750.0, sucursal=suc))
        db.add(Settings(clave="precio_hora_moto", valor=800.0, sucursal=suc))
        db.add(Settings(clave="precio_30min_moto", valor=400.0, sucursal=suc))
        db.add(Settings(clave="precio_hora_camioneta", valor=2000.0, sucursal=suc))
        db.add(Settings(clave="precio_30min_camioneta", valor=1000.0, sucursal=suc))
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
    # R5: el lookup no expone PII sensible (email) al operador de caja
    assert "email" not in resultado


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


# ==========================================================================
# ORIGEN DE LA RESERVA (MANUAL = CREADA POR ADMIN/EMPLEADO)
# ==========================================================================

def test_create_admin_reservation_marca_origen_manual(db):
    staff = _staff(db)
    resultado = create_admin_reservation(_reserva_data(pagar=False), db, staff)
    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    assert res.origen == "manual"


def test_reserva_de_cliente_por_defecto_tiene_origen_cliente(db):
    res = Reservation(patente="ZZZ999", fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00",
                      tipo_estadia="hora", monto_total=1500.0, estado_pago="Pendiente",
                      estado_reserva="Pendiente", sucursal_nombre="Sucursal Central", tipo_vehiculo="Auto")
    db.add(res)
    db.commit()
    assert res.origen == "cliente"


# ==========================================================================
# EDICION DE RESERVAS MANUALES
# ==========================================================================

def test_edit_admin_reservation_actualiza_datos_y_recalcula_monto(db):
    staff = _staff(db)
    resultado = create_admin_reservation(_reserva_data(patente="ABC123", pagar=False), db, staff)

    update_admin_reservation(
        resultado["id"],
        _reserva_data(patente="abc124", fecha_inicio="2026-07-11 08:00", fecha_fin="2026-07-11 11:00"),
        db, staff
    )

    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    assert res.patente == "ABC124"
    assert res.fecha_inicio == "2026-07-11 08:00"
    assert res.fecha_fin == "2026-07-11 11:00"
    assert res.origen == "manual"
    expected = BillingService.calculate_total_amount(
        db, "hora", "2026-07-11 08:00", "2026-07-11 11:00",
        sucursal="Sucursal Central", tipo_vehiculo="Auto"
    )
    assert res.monto_total == expected


def test_edit_admin_reservation_preserva_estados(db):
    staff = _staff(db)
    resultado = create_admin_reservation(_reserva_data(pagar=True, metodo_pago="Efectivo"), db, staff)

    update_admin_reservation(resultado["id"], _reserva_data(fecha_inicio="2026-07-11 08:00", fecha_fin="2026-07-11 11:00"), db, staff)

    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    assert res.estado_pago == PaymentStatus.PAGADO
    assert res.estado_reserva == ReservationStatus.ACTIVA
    assert res.metodo_pago == "Efectivo"


def test_edit_admin_reservation_vincula_usuario_por_patente(db):
    user = _cliente_con_vehiculo(db, patente="ABC 123", tipo="Auto")
    staff = _staff(db)
    resultado = create_admin_reservation(_reserva_data(patente="XYZ 000", pagar=False), db, staff)

    update_admin_reservation(resultado["id"], _reserva_data(patente="abc123", user_id=user.id), db, staff)

    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    assert res.user_id == user.id
    assert res.patente == "ABC123"


def test_edit_reserva_de_cliente_rechazada(db):
    staff = _staff(db)
    res = Reservation(patente="ZZZ999", fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00",
                      tipo_estadia="hora", monto_total=1500.0, estado_pago="Pendiente",
                      estado_reserva="Pendiente", sucursal_nombre="Sucursal Central", tipo_vehiculo="Auto")
    db.add(res)
    db.commit()

    with pytest.raises(HTTPException) as exc:
        update_admin_reservation(res.id, _reserva_data(), db, staff)
    assert exc.value.status_code == 400


def test_edit_completada_rechazada(db):
    staff = _staff(db)
    resultado = create_admin_reservation(_reserva_data(pagar=False), db, staff)
    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    res.estado_reserva = ReservationStatus.COMPLETADA
    db.commit()

    with pytest.raises(HTTPException) as exc:
        update_admin_reservation(resultado["id"], _reserva_data(), db, staff)
    assert exc.value.status_code == 400


def test_edit_staff_no_puede_editar_otra_sucursal(db):
    db.add(ParkingBranch(nombre="Sucursal Dos", direccion="Av. Test 456", horario="24hs", is_24h=True))
    db.add(ParkingAforo(sucursal="Sucursal Dos", capacidad_reservas_autos=2))
    db.commit()

    admin = User(nombre="Admin", apellido="Global", dni="11111111", email="admin@test.com",
                 rol="admin", sucursal=None, saldo=0.0)
    db.add(admin)
    db.commit()

    resultado = create_admin_reservation(_reserva_data(sucursal_nombre="Sucursal Dos"), db, admin)
    staff = _staff(db)  # Sucursal Central

    with pytest.raises(HTTPException) as exc:
        update_admin_reservation(resultado["id"], _reserva_data(), db, staff)
    assert exc.value.status_code == 403


def test_edit_excluye_propia_reserva_de_disponibilidad(db):
    staff = _staff(db)
    _reserva_data_10_12 = lambda: _reserva_data(fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00")
    r1 = create_admin_reservation(_reserva_data_10_12(), db, staff)["id"]
    r2 = create_admin_reservation(_reserva_data_10_12(), db, staff)["id"]

    # CAPACIDAD 2: AMBAS RESERVAS LLENAN EL SLOT. EDITAR UNA SIN EXCLUIR FALLARIA,
    # PERO EXCLUYENDO LA PROPIA DEBE PERMITIRSE.
    resultado = update_admin_reservation(r2, _reserva_data_10_12(), db, staff)
    assert resultado["status"] == "ok"
    assert r1 != r2


def test_edit_admin_reservation_valida_rango_invertido(db):
    staff = _staff(db)
    resultado = create_admin_reservation(_reserva_data(pagar=False), db, staff)

    with pytest.raises(HTTPException) as exc:
        update_admin_reservation(resultado["id"], _reserva_data(fecha_inicio="2026-07-11 12:00", fecha_fin="2026-07-11 10:00"), db, staff)
    assert exc.value.status_code == 400


def test_edit_sin_user_id_conserva_vinculo_si_la_patente_sigue_siendo_del_usuario(db):
    user = _cliente_con_vehiculo(db, patente="ABC 123", tipo="Auto")
    staff = _staff(db)
    resultado = create_admin_reservation(_reserva_data(patente="ABC123", user_id=user.id, pagar=False), db, staff)

    # EDIT SIN USER_ID: LA PATENTE SIGUE SIENDO DEL USUARIO VINCULADO => CONSERVA EL VINCULO
    update_admin_reservation(resultado["id"], _reserva_data(patente="ABC123", user_id=None), db, staff)

    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    assert res.user_id == user.id
    assert res.patente == "ABC123"


def test_edit_sin_user_id_desvincula_si_la_patente_ya_no_es_del_usuario(db):
    user = _cliente_con_vehiculo(db, patente="ABC 123", tipo="Auto")
    staff = _staff(db)
    resultado = create_admin_reservation(_reserva_data(patente="ABC123", user_id=user.id, pagar=False), db, staff)

    # CAMBIA LA PATENTE A UNA QUE NO LE PERTENECE AL USUARIO => SE DESVINCULA
    update_admin_reservation(resultado["id"], _reserva_data(patente="ZZZ999", user_id=None), db, staff)

    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    assert res.user_id is None
    assert res.patente == "ZZZ999"


def test_create_admin_reservation_almacena_patente_canonica_sin_espacios(db):
    staff = _staff(db)
    resultado = create_admin_reservation(_reserva_data(patente="as122tr", pagar=False), db, staff)

    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    assert res.patente == "AS122TR"


def test_disabled_hours_excluye_propia_reserva_al_editar(db):
    staff = _staff(db)
    r = create_admin_reservation(_reserva_data(fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00", pagar=False), db, staff)

    sin_exclusion = obtener_horas_deshabilitadas_con_reservas(
        db, "Sucursal Central", "2026-07-10", "Auto", exclude_id=None
    )
    assert {"inicio": "10:00", "fin": "12:00"} in sin_exclusion["reserved_ranges"]

    con_exclusion = obtener_horas_deshabilitadas_con_reservas(
        db, "Sucursal Central", "2026-07-10", "Auto", exclude_id=r["id"]
    )
    assert con_exclusion["reserved_ranges"] == []


def _monto(db, inicio, fin, tipo="hora"):
    return BillingService.calculate_total_amount(
        db, tipo, inicio, fin, sucursal="Sucursal Central", tipo_vehiculo="Auto"
    )


def test_edit_cobra_diferencia_cuando_aumenta_el_monto(db):
    staff = _staff(db)
    r = create_admin_reservation(
        _reserva_data(fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00", pagar=True, metodo_pago="Efectivo"),
        db, staff
    )
    monto_2h = _monto(db, "2026-07-10 10:00", "2026-07-10 12:00")

    res = update_admin_reservation(
        r["id"],
        _reserva_data(fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 14:00", cobrar_diferencia_metodo="Tarjeta"),
        db, staff
    )
    monto_4h = _monto(db, "2026-07-10 10:00", "2026-07-10 14:00")

    assert res["accion"] == "cobro"
    assert res["diferencia"] == round(monto_4h - monto_2h, 2)
    assert res["monto"] == round(monto_4h, 2)
    assert res["metodo_pago"] == "Tarjeta"

    row = db.query(Reservation).filter(Reservation.id == r["id"]).one()
    assert row.estado_pago == PaymentStatus.PAGADO
    assert row.metodo_pago == "Tarjeta"
    assert row.monto_total == round(monto_4h, 2)
    assert row.monto_reembolsado == 0.0


def test_edit_reembolsa_diferencia_al_saldo_cuando_disminuye(db):
    user = _cliente_con_vehiculo(db, patente="ABC 123", tipo="Auto")
    staff = _staff(db)
    saldo_inicial = user.saldo
    r = create_admin_reservation(
        _reserva_data(patente="ABC123", user_id=user.id, fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00", pagar=True, metodo_pago="Efectivo"),
        db, staff
    )
    monto_2h = _monto(db, "2026-07-10 10:00", "2026-07-10 12:00")

    res = update_admin_reservation(
        r["id"],
        _reserva_data(patente="ABC123", user_id=user.id, fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 11:00", reembolsar_diferencia_metodo="Saldo"),
        db, staff
    )
    monto_1h = _monto(db, "2026-07-10 10:00", "2026-07-10 11:00")
    esperado = round(monto_2h - monto_1h, 2)

    assert res["accion"] == "reembolso"
    assert res["diferencia"] == -esperado
    assert res["reembolsado_total"] == esperado

    row = db.query(Reservation).filter(Reservation.id == r["id"]).one()
    assert row.estado_pago == PaymentStatus.PAGADO
    assert row.monto_total == round(monto_2h, 2)
    assert row.monto_reembolsado == esperado
    # EL REEMBOLSO SE ACREDITA AL SALDO DEL USUARIO
    assert row.user.saldo == round(saldo_inicial + esperado, 2)


def test_edit_reembolso_en_efectivo_no_acredita_saldo(db):
    user = _cliente_con_vehiculo(db, patente="ABC 123", tipo="Auto")
    staff = _staff(db)
    saldo_inicial = user.saldo
    monto_2h = _monto(db, "2026-07-10 10:00", "2026-07-10 12:00")
    monto_1h = _monto(db, "2026-07-10 10:00", "2026-07-10 11:00")
    esperado = round(monto_2h - monto_1h, 2)

    r = create_admin_reservation(
        _reserva_data(patente="ABC123", user_id=user.id, fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00", pagar=True, metodo_pago="Efectivo"),
        db, staff
    )

    res = update_admin_reservation(
        r["id"],
        _reserva_data(patente="ABC123", user_id=user.id, fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 11:00", reembolsar_diferencia_metodo="Efectivo"),
        db, staff
    )

    assert res["accion"] == "reembolso"
    assert res["metodo_pago"] == "Efectivo"
    row = db.query(Reservation).filter(Reservation.id == r["id"]).one()
    assert row.estado_pago == PaymentStatus.PAGADO
    assert row.monto_total == round(monto_2h, 2)
    assert row.monto_reembolsado == esperado
    # LA DEVOLUCIÓN EN EFECTIVO NO ACREDITA AL SALDO VIRTUAL
    assert row.user.saldo == saldo_inicial

    # EN EL REPORTE LA RESERVA QUEDA IMPUTADA A EFECTIVO (PAGO EN CAJA) EN NETO
    user.rol = "admin"
    user.sucursal = None
    db.commit()
    resumen = ReportService.get_financial_summary(db, user, period="total")
    assert resumen["desglose"]["reservas"]["monto"] == round(monto_2h - esperado, 2)
    assert resumen["total_reembolsado"] == esperado
    reserva_efectivo = next(m for m in resumen["desglose_metodos"] if m["metodo"] == "CAJA")
    assert reserva_efectivo["monto"] == round(monto_2h - esperado, 2)

    historial = ReportService.get_payment_history(db, user, period="total")
    reembolso = [e for e in historial if e["id"] == f"REF{r['id']}" and e["tipo"] == "Reembolso"]
    assert reembolso
    assert reembolso[0]["costo_estadia"] == -esperado
    assert reembolso[0]["metodo"] == "Efectivo"


def test_edit_sin_diferencia_no_toca_finanzas(db):
    staff = _staff(db)
    r = create_admin_reservation(
        _reserva_data(fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00", pagar=True, metodo_pago="Efectivo"),
        db, staff
    )
    monto_2h = _monto(db, "2026-07-10 10:00", "2026-07-10 12:00")

    res = update_admin_reservation(
        r["id"],
        _reserva_data(fecha_inicio="2026-07-11 10:00", fecha_fin="2026-07-11 12:00"),
        db, staff
    )

    assert res["accion"] == "sin_cambio"
    row = db.query(Reservation).filter(Reservation.id == r["id"]).one()
    assert row.monto_total == round(monto_2h, 2)
    assert row.monto_reembolsado == 0.0
    assert res["diferencia"] == 0.0


def test_edit_pagada_con_multiples_ajustes_mantiene_neto_correcto(db):
    staff = _staff(db)
    r = create_admin_reservation(
        _reserva_data(fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00", pagar=True, metodo_pago="Efectivo"),
        db, staff
    )
    monto_2h = _monto(db, "2026-07-10 10:00", "2026-07-10 12:00")

    # SUBE 2h -> 4h (cobra diferencia)
    update_admin_reservation(
        r["id"],
        _reserva_data(fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 14:00", cobrar_diferencia_metodo="Tarjeta"),
        db, staff
    )
    monto_4h = _monto(db, "2026-07-10 10:00", "2026-07-10 14:00")

    # BAJA 4h -> 3h (reembolsa diferencia)
    res = update_admin_reservation(
        r["id"],
        _reserva_data(fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 13:00", reembolsar_diferencia_metodo="Saldo"),
        db, staff
    )
    monto_3h = _monto(db, "2026-07-10 10:00", "2026-07-10 13:00")

    assert res["accion"] == "reembolso"
    row = db.query(Reservation).filter(Reservation.id == r["id"]).one()
    # NETO = monto_total - reembolsado = valor final
    assert round((row.monto_total or 0) - (row.monto_reembolsado or 0), 2) == round(monto_3h, 2)


def test_reporte_cuenta_reembolso_parcial_de_reserva_pagada(db):
    admin = _cliente(db)
    admin.rol = "admin"
    db.commit()
    staff = _staff(db)
    r = create_admin_reservation(
        _reserva_data(fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00", pagar=True, metodo_pago="Efectivo"),
        db, staff
    )
    monto_2h = _monto(db, "2026-07-10 10:00", "2026-07-10 12:00")
    monto_1h = _monto(db, "2026-07-10 10:00", "2026-07-10 11:00")
    esperado = round(monto_2h - monto_1h, 2)

    update_admin_reservation(
        r["id"],
        _reserva_data(fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 11:00", reembolsar_diferencia_metodo="Saldo"),
        db, staff
    )

    resumen = ReportService.get_financial_summary(db, admin, period="total")
    assert resumen["desglose"]["reservas"]["monto"] == round(monto_2h - esperado, 2)
    assert resumen["total_reembolsado"] == esperado
    # EN EL DESGLOSE POR METODO LA RESERVA CON REEMBOLSO PARCIAL QUEDA EN NETO
    reserva_metodo = next(m for m in resumen["desglose_metodos"] if m["metodo"] == "DIGITAL")
    assert reserva_metodo["monto"] == round(monto_2h - esperado, 2)

    historial = ReportService.get_payment_history(db, admin, period="total")
    reembolso = [e for e in historial if e["id"] == f"REF{r['id']}" and e["tipo"] == "Reembolso"]
    assert reembolso
    assert reembolso[0]["costo_estadia"] == -esperado


# ==========================================================================
# DESCUENTOS DE CANJE EN PAGO CAJA (MANUAL / ADMIN)
# ==========================================================================

def _descuento_ticket(db, user, sucursal="Sucursal Central", porc=10):
    ticket = RedemptionTicket(
        user_id=user.id,
        codigo=f"T{user.id}S{porc}C{sucursal[:3].upper()}",
        titulo="Descuento en Estacionamiento",
        descripcion="10%",
        tipo_canje="descuento_reserva",
        valor_descuento=porc,
        icono="fas fa-percent",
        sucursal=sucursal,
        estado="VIGENTE",
        qr_data="AUTOPASS_REDEMPTION|ID:TEST",
    )
    db.add(ticket)
    db.commit()
    return ticket


def test_pay_reservation_manual_aplica_descuento_de_canje(db):
    user = _cliente(db)
    ticket = _descuento_ticket(db, user, porc=10)
    monto = _monto(db, "2026-07-10 10:00", "2026-07-10 12:00")
    data = _reserva_data(user_id=user.id, cliente_nombre="Cliente Test",
                         fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00")
    res = ReservationService.create_reservation(db, data)
    puntos_iniciales = user.puntos_acumulados

    resultado = ReservationService.pay_reservation_manual(db, res, "Efectivo", ticket.id)
    db.refresh(user); db.refresh(ticket); db.refresh(res)

    descuento_esperado = round(monto * 0.10, 2)
    assert resultado["status"] == "ok"
    assert resultado["descuento"] == descuento_esperado
    assert res.estado_pago == PaymentStatus.PAGADO
    assert res.monto_total == round(monto - descuento_esperado, 2)
    assert ticket.estado == "USADO"
    assert ticket.reserva_id == res.id
    assert user.puntos_acumulados == puntos_iniciales + BillingService.calculate_points(monto - descuento_esperado)


def test_pay_reservation_manual_idempotente_con_descuento(db):
    user = _cliente(db)
    ticket = _descuento_ticket(db, user, porc=10)
    res = ReservationService.create_reservation(db, _reserva_data(user_id=user.id, cliente_nombre="Cliente Test"))
    ReservationService.pay_reservation_manual(db, res, "Efectivo", ticket.id)
    # SEGUNDO LLAMADO: IDEMPOTENTE, NO CONSUME OTRO TICKET NI TOCA MONTO
    second = ReservationService.pay_reservation_manual(db, res, "Tarjeta")
    assert second["status"] == "ok"
    assert second["descuento"] == 0.0
    assert res.metodo_pago == "Efectivo"


def test_pay_reservation_manual_rechaza_ticket_de_otra_sucursal(db):
    user = _cliente(db)
    res = ReservationService.create_reservation(db, _reserva_data(user_id=user.id, cliente_nombre="Cliente Test"))
    ticket_otra = _descuento_ticket(db, user, sucursal="Sucursal Dos", porc=10)
    with pytest.raises(HTTPException) as exc:
        ReservationService.pay_reservation_manual(db, res, "Efectivo", ticket_otra.id)
    assert exc.value.status_code == 400
    assert res.estado_pago == PaymentStatus.PENDIENTE


def test_pay_reservation_manual_sin_usuario_en_reserva_y_con_ticket_rechaza(db):
    res = ReservationService.create_reservation(db, _reserva_data(pagar=False))
    ticket = RedemptionTicket(user_id=999, codigo="X", titulo="T", tipo_canje="descuento_reserva",
                              valor_descuento=10, sucursal="Sucursal Central", estado="VIGENTE",
                              qr_data="AUTOPASS_REDEMPTION|ID:X")
    db.add(ticket); db.commit()
    with pytest.raises(HTTPException) as exc:
        ReservationService.pay_reservation_manual(db, res, "Caja", ticket.id)
    assert exc.value.status_code == 400
    assert res.estado_pago == PaymentStatus.PENDIENTE


def test_create_admin_reservation_con_descuento_crea_y_paga(db):
    user = _cliente_con_vehiculo(db, patente="ABC 123", tipo="Auto")
    staff = _staff(db)
    ticket = _descuento_ticket(db, user, porc=10)
    monto = _monto(db, "2026-07-10 10:00", "2026-07-10 12:00")

    data = _reserva_data(user_id=user.id, cliente_nombre="Cliente Test",
                         fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00",
                         pagar=True, metodo_pago="Efectivo", redemption_ticket_id=ticket.id)
    resultado = create_admin_reservation(data, db, staff)

    assert resultado["status"] == "ok"
    assert resultado["pagado"] is True
    assert resultado["descuento"] == round(monto * 0.10, 2)

    res = db.query(Reservation).filter(Reservation.id == resultado["id"]).one()
    db.refresh(ticket)
    assert res.estado_pago == PaymentStatus.PAGADO
    assert res.monto_total == round(monto - round(monto * 0.10, 2), 2)
    assert ticket.estado == "USADO"
    assert ticket.reserva_id == res.id


def test_confirm_reservation_payment_aplica_descuento(db):
    user = _cliente_con_vehiculo(db, patente="ABC 123", tipo="Auto")
    staff = _staff(db)
    ticket = _descuento_ticket(db, user, porc=10)
    data = _reserva_data(user_id=user.id, cliente_nombre="Cliente Test",
                         fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00", pagar=False)
    r = create_admin_reservation(data, db, staff)
    res = db.query(Reservation).filter(Reservation.id == r["id"]).one()
    monto = _monto(db, "2026-07-10 10:00", "2026-07-10 12:00")
    out = confirm_reservation_payment(r["id"], ConfirmPaymentRequest(metodo_pago="Caja", redemption_ticket_id=ticket.id), db, staff)
    db.refresh(res); db.refresh(ticket)
    descuento = round(monto * 0.10, 2)
    assert out["descuento"] == descuento
    assert res.monto_total == round(monto - descuento, 2)
    assert res.estado_pago == PaymentStatus.PAGADO
    assert ticket.estado == "USADO"


def test_confirm_reservation_payment_con_ticket_invalido_rechaza(db):
    user = _cliente_con_vehiculo(db, patente="ABC 123", tipo="Auto")
    staff = _staff(db)
    ticket_otra = _descuento_ticket(db, user, sucursal="Sucursal Dos", porc=10)
    r = create_admin_reservation(_reserva_data(user_id=user.id, cliente_nombre="Cliente Test"), db, staff)
    with pytest.raises(HTTPException) as exc:
        confirm_reservation_payment(r["id"], ConfirmPaymentRequest(metodo_pago="Caja", redemption_ticket_id=ticket_otra.id), db, staff)
    assert exc.value.status_code == 400
    res = db.query(Reservation).filter(Reservation.id == r["id"]).one()
    assert res.estado_pago == PaymentStatus.PENDIENTE


def test_reservation_available_redemptions_lista_descuentos(db):
    user = _cliente_con_vehiculo(db, patente="ABC 123", tipo="Auto")
    staff = _staff(db)
    ticket = _descuento_ticket(db, user, porc=10)
    data = _reserva_data(user_id=user.id, cliente_nombre="Cliente Test",
                         fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00", pagar=False)
    r = create_admin_reservation(data, db, staff)
    monto = _monto(db, "2026-07-10 10:00", "2026-07-10 12:00")
    out = reservation_available_redemptions(r["id"], db, staff)
    assert len(out) == 1
    assert out[0]["id"] == ticket.id
    assert out[0]["valor_descuento"] == 10
    assert out[0]["descuento_peso"] == round(monto * 0.10, 2)
    assert out[0]["monto_final"] == round(monto * 0.90, 2)


def test_reservation_available_redemptions_vacio_sin_usuario(db):
    staff = _staff(db)
    r = create_admin_reservation(_reserva_data(pagar=False), db, staff)
    out = reservation_available_redemptions(r["id"], db, staff)
    assert out == []


def test_admin_available_redemptions_por_usuario(db):
    user = _cliente(db)
    staff = _staff(db)
    _descuento_ticket(db, user, porc=10)
    out = admin_available_redemptions(user.id, "Sucursal Central", db, staff)
    assert len(out) == 1
    assert out[0]["valor_descuento"] == 10
    # SIN USUARIO VINCULADO => VACÍA
    assert admin_available_redemptions(None, "Sucursal Central", db, staff) == []


def test_admin_available_redemptions_sin_tickets_vacia(db):
    user = _cliente(db)
    staff = _staff(db)
    out = admin_available_redemptions(user.id, "Sucursal Central", db, staff)
    assert out == []


def test_admin_available_redemptions_user_id_inexistente_404(db):
    _cliente(db)
    staff = _staff(db)
    with pytest.raises(HTTPException) as exc:
        admin_available_redemptions(999999, "Sucursal Central", db, staff)
    assert exc.value.status_code == 404


def test_redemption_info_edicion_reserva_pagada_con_descuento(db):
    user = _cliente_con_vehiculo(db, patente="ABC 123", tipo="Auto")
    staff = _staff(db)
    ticket = _descuento_ticket(db, user, porc=10)
    data = _reserva_data(user_id=user.id, cliente_nombre="Cliente Test",
                         fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00", pagar=False)
    r = create_admin_reservation(data, db, staff)
    confirm_reservation_payment(r["id"], ConfirmPaymentRequest(metodo_pago="Caja", redemption_ticket_id=ticket.id), db, staff)

    out = reservation_redemption_info(r["id"], db, staff)
    assert out["aplica"] is True
    assert out["fuente"] == "aplicado"
    assert out["valor_descuento"] == 10
    assert out["ticket_id"] == ticket.id


def test_redemption_info_edicion_reserva_con_descuento_vigente(db):
    user = _cliente_con_vehiculo(db, patente="ABC 123", tipo="Auto")
    staff = _staff(db)
    _descuento_ticket(db, user, porc=20)
    r = create_admin_reservation(_reserva_data(user_id=user.id, cliente_nombre="Cliente Test"), db, staff)

    out = reservation_redemption_info(r["id"], db, staff)
    assert out["aplica"] is True
    assert out["fuente"] == "vigente"
    assert out["valor_descuento"] == 20


def test_redemption_info_edicion_reserva_sin_descuento(db):
    staff = _staff(db)
    r = create_admin_reservation(_reserva_data(pagar=False), db, staff)
    out = reservation_redemption_info(r["id"], db, staff)
    assert out["aplica"] is False
    assert out["fuente"] is None


def test_editar_reserva_pagada_con_descuento_mantiene_descuento_al_recalcular(db):
    user = _cliente_con_vehiculo(db, patente="ABC 123", tipo="Auto")
    staff = _staff(db)
    ticket = _descuento_ticket(db, user, porc=10)
    data = _reserva_data(user_id=user.id, cliente_nombre="Cliente Test", patente="ABC123",
                         fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 12:00", pagar=False)
    r = create_admin_reservation(data, db, staff)
    confirm_reservation_payment(r["id"], ConfirmPaymentRequest(metodo_pago="Efectivo", redemption_ticket_id=ticket.id), db, staff)

    monto_2h = _monto(db, "2026-07-10 10:00", "2026-07-10 12:00")
    monto_4h = _monto(db, "2026-07-10 10:00", "2026-07-10 14:00")
    desc_2h = round(monto_2h * 0.10, 2)
    desc_4h = round(monto_4h * 0.10, 2)

    res = update_admin_reservation(
        r["id"],
        _reserva_data(user_id=user.id, cliente_nombre="Cliente Test", patente="ABC123",
                      fecha_inicio="2026-07-10 10:00", fecha_fin="2026-07-10 14:00", cobrar_diferencia_metodo="Tarjeta"),
        db, staff
    )

    # EL MONTO RECALCULADO SE MANTIENE CON EL MISMO DESCUENTO (BASE DESCONTADA)
    assert res["accion"] == "cobro"
    assert res["monto"] == round(monto_4h - desc_4h, 2)
    assert res["diferencia"] == round((monto_4h - desc_4h) - (monto_2h - desc_2h), 2)

    row = db.query(Reservation).filter(Reservation.id == r["id"]).one()
    assert row.estado_pago == PaymentStatus.PAGADO
    assert row.monto_total == round(monto_4h - desc_4h, 2)
    db.refresh(ticket)
    assert ticket.estado == "USADO"
    assert ticket.reserva_id == row.id


def test_get_new_reservations_count_sin_reservas(db):
    admin_user = User(nombre="Admin", apellido="Global", dni="99999999", email="admin@test.com",
                      rol="admin", sucursal="Todas")
    res = get_new_reservations_count(since_id=None, db=db, staff=admin_user)
    assert res["count"] == 0
    assert res["latest_id"] == 0


def test_get_new_reservations_count_incrementa_con_nuevas_reservas(db):
    admin_user = User(nombre="Admin", apellido="Global", dni="99999999", email="admin@test.com",
                      rol="admin", sucursal="Todas")
    
    # Crear primera reserva
    data1 = _reserva_data(patente="AAA111")
    r1 = ReservationService.create_reservation(db, data1)
    
    # Inicialmente sin since_id
    res0 = get_new_reservations_count(since_id=None, db=db, staff=admin_user)
    assert res0["latest_id"] == r1.id
    assert res0["count"] == 0

    # Si ya se vio r1.id
    res_seen = get_new_reservations_count(since_id=r1.id, db=db, staff=admin_user)
    assert res_seen["count"] == 0

    # Crear 2 reservas más
    data2 = _reserva_data(patente="BBB222")
    r2 = ReservationService.create_reservation(db, data2)
    data3 = _reserva_data(patente="CCC333")
    r3 = ReservationService.create_reservation(db, data3)

    res_new = get_new_reservations_count(since_id=r1.id, db=db, staff=admin_user)
    assert res_new["count"] == 2
    assert res_new["latest_id"] == r3.id

    # Al ver la última
    res_cleared = get_new_reservations_count(since_id=r3.id, db=db, staff=admin_user)
    assert res_cleared["count"] == 0


def test_get_new_reservations_count_aislamiento_sucursales(db):
    local_user = User(nombre="Local", apellido="Admin", dni="88888888", email="local@test.com",
                      rol="local_admin", sucursal="Sucursal Central")
    admin_global = User(nombre="Admin", apellido="Global", dni="99999999", email="admin@test.com",
                        rol="admin", sucursal="Todas")

    branch2 = ParkingBranch(nombre="Sucursal Norte", direccion="Calle Norte 456", horario="24hs", is_24h=True)
    db.add(branch2)
    db.add(Settings(clave="precio_hora", valor=1500.0, sucursal="Sucursal Norte"))
    db.add(Settings(clave="precio_30min", valor=750.0, sucursal="Sucursal Norte"))
    db.commit()

    # Reserva en Sucursal Central
    r1 = ReservationService.create_reservation(db, _reserva_data(patente="AAA111", sucursal_nombre="Sucursal Central"))
    # Reserva en Sucursal Norte
    r2 = ReservationService.create_reservation(db, _reserva_data(patente="BBB222", sucursal_nombre="Sucursal Norte"))

    # Local admin de Sucursal Central sólo debe ver la reserva de su sucursal
    res_local = get_new_reservations_count(since_id=0, db=db, staff=local_user)
    assert res_local["count"] == 1
    assert res_local["latest_id"] == r1.id

    # Admin global ve ambas reservas
    res_global = get_new_reservations_count(since_id=0, db=db, staff=admin_global)
    assert res_global["count"] == 2
    assert res_global["latest_id"] == r2.id