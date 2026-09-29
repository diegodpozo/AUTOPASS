"""Regresión: el monitoreo del dashboard mostraba INVITADO para patentes de usuarios.

Causa: services/report_service.get_access_logs resolvia el dueño del vehículo con
VehicleRepository.get_by_patentes(), que hace match EXACTO con IN(). Pero los logs
guardan la patente NORMALIZADA (patente_detectada="AB123CD", ver
services/access_service.py) mientras que el alta de vehículo la guarda CON formato
visual (patente=format_plate(...), "AB 123 CD", ver services/user_service.py).
El IN no encontraba nada -> usuario=None -> es_registrado=False -> "INVITADO".

La resolución debe hacerse por patente normalizada, igual que el resto del codebase
(access_service, reservation_service, user_service).
"""
import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base
from core.normalize import format_plate, normalize_plate
from models import AccessLog, User, Vehicle
from models.enums import AccessEventType
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


def _admin(db):
    return db.query(User).filter_by(rol="admin").first()


def _log(db, patente, tipo=AccessEventType.ENTRADA):
    db.add(AccessLog(
        patente_detectada=patente, tipo_evento=tipo,
        fecha_hora=datetime.datetime.now().isoformat(),
    ))
    db.commit()


def test_log_normalizado_resuelve_usuario_con_patente_formateada(db):
    """Patente "AB123CD" en el log vs "AB 123 CD" en vehicles: debe resolver el dueño."""
    user = User(nombre="Juan", apellido="Perez", dni="11111111", email="jp@test.com",
                password_hash="x", rol="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    # El alta real guarda la patente con formato visual (user_service.py:163)
    db.add(Vehicle(user_id=user.id, patente=format_plate("AB123CD"),
                   marca_modelo="TOYOTA", tipo="Auto"))
    # El log real guarda la patente normalizada (access_service.py:268)
    _log(db, normalize_plate("AB 123 CD"))
    db.commit()

    rows = ReportService.get_access_logs(db=db, staff=_admin(db), limit=10)

    assert len(rows) == 1
    assert rows[0]["usuario"] == "Juan Perez"
    assert rows[0]["es_registrado"] is True


def test_resuelve_usuario_ignoring_mayusculas_y_espacios(db):
    """La resolución es insensible a mayúsculas y espacios en ambos lados."""
    user = User(nombre="Ana", apellido="Gomez", dni="22222222", email="ag@test.com",
                password_hash="x", rol="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(Vehicle(user_id=user.id, patente=format_plate("ac123df"),
                   marca_modelo="FIAT", tipo="Auto"))
    _log(db, "ac123df")
    db.commit()

    rows = ReportService.get_access_logs(db=db, staff=_admin(db), limit=10)

    assert rows[0]["usuario"] == "Ana Gomez"
    assert rows[0]["es_registrado"] is True


def test_patente_sin_vehicle_sigue_siendo_invitado(db):
    """Una patente truly invitada (sin vehicle asociado) NO debe resolverse a un usuario."""
    _log(db, "XX999XX")

    rows = ReportService.get_access_logs(db=db, staff=_admin(db), limit=10)

    assert rows[0]["usuario"] is None
    assert rows[0]["es_registrado"] is False


def test_usa_normalized_patente_del_log_si_esta_disponible(db):
    """Si el log trae normalized_patente, se usa esa (ya normalizada) como fuente."""
    user = User(nombre="Luis", apellido="Soto", dni="33333333", email="ls@test.com",
                password_hash="x", rol="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(Vehicle(user_id=user.id, patente=format_plate("AB123CD"),
                   marca_modelo="RENAULT", tipo="Auto"))
    db.add(AccessLog(
        patente_detectada="AB 123 CD",           # con espacios
        normalized_patente="AB123CD",            # ya normalizada
        tipo_evento=AccessEventType.ENTRADA,
        fecha_hora=datetime.datetime.now().isoformat(),
    ))
    db.commit()

    rows = ReportService.get_access_logs(db=db, staff=_admin(db), limit=10)

    assert rows[0]["usuario"] == "Luis Soto"
    assert rows[0]["es_registrado"] is True


def test_log_sin_patente_no_desalinea_el_resolucion_de_los_demas(db):
    """Un log sin patente no debe correr el lugar de los siguientes (zip alineado)."""
    user = User(nombre="Mia", apellido="Rios", dni="44444444", email="mr@test.com",
                password_hash="x", rol="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(Vehicle(user_id=user.id, patente=format_plate("GH234GH"),
                   marca_modelo="FORD", tipo="Auto"))
    # Log sin ninguna patente, seguido del de una patente registrada
    db.add(AccessLog(patente_detectada=None, tipo_evento=AccessEventType.ENTRADA,
                     fecha_hora=datetime.datetime.now().isoformat()))
    _log(db, "GH234GH")
    db.commit()

    rows = ReportService.get_access_logs(db=db, staff=_admin(db), limit=10)

    assert len(rows) == 2
    por_placa = {r["patente_detectada"]: r for r in rows}
    assert por_placa[None]["usuario"] is None
    assert por_placa[None]["es_registrado"] is False
    assert por_placa["GH234GH"]["usuario"] == "Mia Rios"
    assert por_placa["GH234GH"]["es_registrado"] is True
