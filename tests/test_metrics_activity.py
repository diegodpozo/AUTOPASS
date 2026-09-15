import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, AccessLog, User
from services.report_service import ReportService

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    admin = User(nombre="Admin", apellido="Global", dni="99999999", email="admin@autopass.com",
                 password_hash="x", rol="admin", sucursal=None)
    db.add(admin)
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def _seed(db, items):
    for i, (fecha, tipo, sucursal) in enumerate(items):
        db.add(AccessLog(id=i + 1, patente_detectada=f"P{i}",
                         tipo_evento=tipo, sucursal=sucursal, fecha_hora=fecha))
    db.commit()


def _admin(db):
    return db.query(User).filter_by(rol="admin").first()


def test_access_activity_sin_filtro_incluye_todas(db):
    _seed(db, [
        ("2025-01-05 10:00:00", "ENTRADA", "Centro"),
        ("2025-01-05 10:00:00", "SALIDA", "Centro"),
        ("2025-01-06 09:00:00", "ENTRADA", "Centro"),
        ("2025-01-06 09:00:00", "ENTRADA", "Centro"),
        ("2025-01-06 18:00:00", "SALIDA", "Centro"),
    ])
    res = ReportService.get_access_activity(db=db, admin=_admin(db))
    assert res["totals"] == {"entrada": 3, "salida": 2, "total": 5}
    assert res["first_datetime"].startswith("2025-01-05")


def test_access_activity_desde_excluye_anteriores(db):
    _seed(db, [
        ("2025-01-05 10:00:00", "ENTRADA", "Centro"),
        ("2025-01-06 09:00:00", "ENTRADA", "Centro"),
        ("2025-01-06 18:00:00", "SALIDA", "Centro"),
    ])
    res = ReportService.get_access_activity(db=db, admin=_admin(db), desde="2025-01-06")
    assert res["totals"] == {"entrada": 1, "salida": 1, "total": 2}
    assert res["first_datetime"].startswith("2025-01-06")


def test_access_activity_rango_completo(db):
    _seed(db, [
        ("2025-01-05 10:00:00", "ENTRADA", "Centro"),
        ("2025-01-06 09:00:00", "ENTRADA", "Centro"),
        ("2025-01-06 18:00:00", "SALIDA", "Centro"),
        ("2025-01-07 08:00:00", "ENTRADA", "Centro"),
    ])
    res = ReportService.get_access_activity(db=db, admin=_admin(db),
                                            desde="2025-01-06", hasta="2025-01-06")
    assert res["totals"] == {"entrada": 1, "salida": 1, "total": 2}
    labels = [b["label"] for b in res["buckets"]]
    assert "2025-01-06 09:00" in labels
    assert "2025-01-05 10:00" not in labels
    assert "2025-01-07 08:00" not in labels


def test_access_activity_rango_invalido_devuelve_vacio(db):
    _seed(db, [
        ("2025-01-06 09:00:00", "ENTRADA", "Centro"),
    ])
    res = ReportService.get_access_activity(db=db, admin=_admin(db),
                                            desde="2025-01-07", hasta="2025-01-06")
    assert res["buckets"] == []
    assert res["totals"] == {"entrada": 0, "salida": 0, "total": 0}


def test_access_activity_hasta_excluye_posteriores(db):
    _seed(db, [
        ("2025-01-05 10:00:00", "ENTRADA", "Centro"),
        ("2025-01-06 09:00:00", "SALIDA", "Centro"),
        ("2025-01-07 08:00:00", "ENTRADA", "Centro"),
    ])
    res = ReportService.get_access_activity(db=db, admin=_admin(db), hasta="2025-01-06")
    assert res["totals"] == {"entrada": 1, "salida": 1, "total": 2}