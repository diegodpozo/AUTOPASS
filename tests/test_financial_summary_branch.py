import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, ParkingBranch, AccessLog, Settings, User
from models.enums import AccessEventType
from services.report_service import ReportService

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.add(ParkingBranch(nombre="Centro", direccion="d", horario="24hs", is_24h=True))
    db.add(ParkingBranch(nombre="Sede", direccion="d", horario="24hs", is_24h=True))
    db.add(ParkingBranch(nombre="Cerrada", direccion="d", horario="24hs", is_24h=True, activa=False))
    for suc in ("Centro", "Sede", "Cerrada"):
        db.add(Settings(clave="precio_hora", valor=1500.0, sucursal=suc))
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def _pago(db, i, patente, sucursal, monto, metodo="CAJA", tipo="Auto", fecha="2026-06-01 10:00:00"):
    db.add(AccessLog(id=i, patente_detectada=patente, tipo_evento=AccessEventType.ENTRADA.value,
                     sucursal=sucursal, fecha_hora=fecha, fecha_pago=fecha, tipo_vehiculo=tipo,
                     costo_estadia=monto, metodo_pago=metodo, pago_confirmado=True))
    db.commit()


def _admin():
    return User(rol="admin", sucursal=None)


def _local(sucursal):
    return User(rol="local_admin", sucursal=sucursal)


def test_admin_general_desglosa_por_sucursal_activa(db):
    _pago(db, 1, "AAA111", "Centro", 1500.0, "CAJA")
    _pago(db, 2, "BBB222", "Centro", 1500.0, "DIGITAL")
    _pago(db, 3, "CCC333", "Sede", 4500.0, "CAJA")

    res = ReportService.get_financial_summary(db, _admin(), period="total")

    assert res["total_recaudado"] == 7500.0
    assert [f["sucursal"] for f in res["por_sucursal"]] == ["Sede", "Centro"]
    por = {f["sucursal"]: f for f in res["por_sucursal"]}
    assert set(por) == {"Centro", "Sede"}  # la sede inactiva queda afuera
    assert por["Centro"]["total_recaudado"] == 3000.0
    assert por["Centro"]["cantidad_pagos"] == 2
    assert por["Centro"]["recaudado_efectivo"] == 1500.0
    assert por["Centro"]["recaudado_digital"] == 1500.0
    assert por["Sede"]["total_recaudado"] == 4500.0
    assert por["Sede"]["cantidad_pagos"] == 1


def test_admin_general_filtra_por_sucursal(db):
    _pago(db, 1, "AAA111", "Centro", 1500.0)
    _pago(db, 2, "CCC333", "Sede", 3000.0)

    res = ReportService.get_financial_summary(db, _admin(), period="total", sucursal="Sede")

    assert res["total_recaudado"] == 3000.0
    assert "por_sucursal" not in res


def test_local_admin_ignora_branch_y_queda_acotado_a_su_sede(db):
    _pago(db, 1, "AAA111", "Centro", 1500.0)
    _pago(db, 2, "CCC333", "Sede", 3000.0)

    res = ReportService.get_financial_summary(db, _local("Centro"), period="total", sucursal="Sede")

    assert res["total_recaudado"] == 1500.0
    assert "por_sucursal" not in res
