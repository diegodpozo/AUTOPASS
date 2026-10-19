import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from models.enums import UserRole
from services.report_service import ReportService


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    models.Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    models.Base.metadata.drop_all(bind=engine)


def test_reporte_financiero_resuelve_castelar_con_prefijo_y_acento(db):
    branch = models.ParkingBranch(nombre="Castelar", direccion="d", horario="24hs", is_24h=True, activa=True)
    db.add(branch)
    db.add(models.Settings(clave="precio_hora", valor=1500.0, sucursal="Castelar"))
    db.flush()
    db.add(models.AccessLog(
        patente_detectada="AA475HX",
        tipo_evento="ENTRADA",
        sucursal_id=branch.id,
        fecha_hora=datetime.datetime.now().isoformat(),
        fecha_pago=datetime.datetime.now().isoformat(),
        costo_estadia=80000.0,
        metodo_pago="CAJA",
        pago_confirmado=True,
    ))
    db.commit()

    admin = models.User(rol=UserRole.ADMIN.value, sucursal=None)
    result = ReportService.get_financial_summary(db, admin, period="total", sucursal="AUTOPASS Castelar")

    assert result["recaudado_efectivo"] == 80000.0
    assert result["total_recaudado"] == 80000.0
