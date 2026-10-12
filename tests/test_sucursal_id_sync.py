"""Test del traductor central de sede: el nombre vive solo en parking_branches y
las tablas dependientes guardan unicamente `sucursal_id`.

Cubre: alta, update (re-apunta id si cambia el nombre), nombre inexistente (id NULL)
y renombre de la sede (NO cambia ids, el display se actualiza solo).
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    models.Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSession()
    yield db, TestSession
    db.close()
    engine.dispose()


def _seed(TestSession, nombre):
    db = TestSession()
    b = models.ParkingBranch(nombre=nombre, activa=True)
    db.add(b)
    db.commit()
    db.refresh(b)
    db.close()
    return b.id


def test_reservacion_insert_deriva_sucursal_id(session):
    db, TS = session
    bid = _seed(TS, "Central Sync")
    r = models.Reservation(patente="AA111BB", sucursal_nombre="Central Sync", monto_total=10.0)
    db.add(r)
    db.commit()
    assert r.sucursal_id == bid


@pytest.mark.parametrize("kwargs", [
    {"clase": models.Reservation, "args": {"patente": "AB222CD", "sucursal_nombre": "Morón Sync", "monto_total": 5.0}},
    {"clase": models.AccessLog, "args": {"patente_detectada": "AB222CD", "tipo_evento": "ENTRADA", "sucursal": "Morón Sync"}},
    {"clase": models.User, "args": {"nombre": "Ana", "apellido": "Luz", "dni": "12345678", "email": "sync@test.com", "sucursal": "Morón Sync"}},
    {"clase": models.SupportTicket, "args": {"user_id": 1, "categoria": "Consulta", "sucursal": "Morón Sync", "asunto": "Horarios", "mensaje": "¿Abren?"}},
    {"clase": models.RedemptionTicket, "args": {"codigo": "SYNC-" + "1234", "titulo": "Lavado", "descripcion": "d", "sucursal": "Morón Sync"}},
])
def test_insert_en_todas_las_tablas_deriva_id(session, kwargs):
    db, TS = session
    bid = _seed(TS, "Morón Sync")
    obj = kwargs["clase"](**kwargs["args"])
    db.add(obj)
    db.commit()
    assert obj.sucursal_id == bid


def test_nombre_inexistente_deja_sucursal_id_none(session):
    db, _ = session
    r = models.Reservation(patente="CC333DD", sucursal_nombre="Sucursal Fantasma", monto_total=1.0)
    db.add(r)
    db.commit()
    assert r.sucursal_id is None


def test_update_repunta_id_al_cambiar_nombre(session):
    db, TS = session
    id_central = _seed(TS, "Central Ora")
    id_otra = _seed(TS, "Otra Ora")
    r = models.Reservation(patente="DD444EE", sucursal_nombre="Central Ora", monto_total=2.0)
    db.add(r)
    db.commit()
    assert r.sucursal_id == id_central
    r.sucursal_nombre = "Otra Ora"
    db.commit()
    assert r.sucursal_id == id_otra


def test_renombrar_sede_no_cambia_ids_y_actualiza_display(session):
    db, TS = session
    bid = _seed(TS, "Vieja Sede")
    r = models.Reservation(patente="EE555FF", sucursal_nombre="Vieja Sede", monto_total=3.0)
    db.add(r)
    db.commit()

    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.id == bid).first()
    branch.nombre = "Sede Nueva"
    db.commit()
    db.expire_all()

    r2 = db.query(models.Reservation).filter(models.Reservation.patente == "EE555FF").first()
    assert r2.sucursal_id == bid
    assert r2.sucursal_nombre == "Sede Nueva"
