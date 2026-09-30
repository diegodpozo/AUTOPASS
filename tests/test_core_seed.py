"""Cobertura de core/seed.py (A3: el gap declarado era 0% en este modulo).

seed_initial_data() es el orquestador de datos maestros que corre init_db.py.
Crea usuarios, aforo global, tarifas, promociones y la red inicial de
sucursales, y es idempotente: correrlo dos veces no debe duplicar nada.

Se testean las 5 ramas y las 2 guardas de idempotencia:

- crea los 4 usuarios iniciales con password hasheado (no en claro);
- no duplica usuarios, aforo, tarifas, promos ni sucursales al re-correr;
- normaliza el DNI de un usuario preexistente que tenga puntos ("12.345.678");
- respeta el aforo/tarifas preexistentes en vez de sobreescribirlos;
- carga el catalogo de beneficios y la red de 4 sucursales solo si estan vacias.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base
from core.seed import (
    DEFAULT_PRICES,
    INITIAL_PROMOS,
    INITIAL_USERS,
    seed_initial_data,
)
from models import ParkingAforo, ParkingBranch, Promotion, Settings, User

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


def test_crea_los_cuatro_usuarios_iniciales(db):
    seed_initial_data(db)

    emails = {u.email for u in db.query(User).all()}
    assert emails == {u["email"] for u in INITIAL_USERS}

    admin = db.query(User).filter_by(email="admin@autopass.com").one()
    assert admin.rol == "admin"
    assert admin.sucursal is None
    # El password NUNCA debe quedar en claro ni ser el hash sin hashear.
    assert admin.password_hash
    assert admin.password_hash != "admin123"
    assert "admin123" not in admin.password_hash

    # El DNI se guarda sin puntos.
    assert admin.dni == "00000001"


def test_password_hash_es_verificable_por_el_mismo_sistema(db):
    """El hash debe servir para el login real, no ser un placeholder."""
    from core.security import verify_password

    seed_initial_data(db)
    admin = db.query(User).filter_by(email="admin@autopass.com").one()
    assert verify_password("admin123", admin.password_hash)
    assert not verify_password("clave-incorrecta", admin.password_hash)


def test_crea_aforo_global_y_tarifas(db):
    seed_initial_data(db)

    aforo = db.query(ParkingAforo).filter_by(sucursal=None).one()
    assert aforo.capacidad_total == 20
    assert aforo.ocupacion_actual == 0
    assert aforo.capacidad_motos == 10
    assert aforo.capacidad_camionetas == 5
    assert aforo.capacidad_reservas == 5

    for clave, valor in DEFAULT_PRICES.items():
        fila = db.query(Settings).filter_by(clave=clave, sucursal=None).one()
        assert fila.valor == valor

    assert db.query(Settings).filter_by(sucursal=None).count() == len(DEFAULT_PRICES)


def test_carga_promociones_y_red_de_sucursales(db):
    seed_initial_data(db)

    promos = db.query(Promotion).all()
    assert len(promos) == len(INITIAL_PROMOS)
    assert {p.titulo for p in promos} == {"Día Libre", "Lavado Premium", "Café Express"}

    sucursales = db.query(ParkingBranch).all()
    assert len(sucursales) == 4
    assert all(s.logo_url == "/static/images/logo.png" for s in sucursales)
    assert {s.nombre for s in sucursales} == {
        "AUTOPASS Central", "AUTOPASS Ituzaingó",
        "AUTOPASS Castelar", "AUTOPASS Morón",
    }


def test_es_idempotente_no_duplica_nada(db):
    """init_db.py puede correr mas de una vez: debe ser seguro."""
    seed_initial_data(db)
    seed_initial_data(db)
    seed_initial_data(db)

    assert db.query(User).count() == len(INITIAL_USERS)
    assert db.query(ParkingAforo).filter_by(sucursal=None).count() == 1
    assert db.query(Settings).filter_by(sucursal=None).count() == len(DEFAULT_PRICES)
    assert db.query(Promotion).count() == len(INITIAL_PROMOS)
    assert db.query(ParkingBranch).count() == 4


def test_normaliza_dni_con_puntos_de_usuario_preexistente(db):
    """Rama exists + dni con puntos: debe normalizarlo, no crear duplicado."""
    db.add(User(
        nombre="Pablo", apellido="Valente", dni="11.232.444",
        email="admcastelar@autopass.com", password_hash="x",
        rol="local_admin", sucursal="AUTOPASS Castelar",
    ))
    db.commit()

    seed_initial_data(db)

    u = db.query(User).filter_by(email="admcastelar@autopass.com").one()
    assert u.dni == "11232444"
    # Sigue siendo UNO solo, no lo duplico por el DNI distinto.
    assert db.query(User).filter_by(email="admcastelar@autopass.com").count() == 1


def test_no_pisa_tarifas_ni_aforo_preexistentes(db):
    """Si el operador ya ajusto precios o aforo, el seed no debe pisarlos."""
    db.add(Settings(clave="precio_hora", valor=9999.0, sucursal=None))
    db.add(ParkingAforo(
        capacidad_total=777, ocupacion_actual=42, sucursal=None,
        ultima_actualizacion="2026-01-01T00:00:00",
    ))
    db.commit()

    seed_initial_data(db)

    assert db.query(Settings).filter_by(clave="precio_hora", sucursal=None).one().valor == 9999.0
    aforo = db.query(ParkingAforo).filter_by(sucursal=None).one()
    assert aforo.capacidad_total == 777
    assert aforo.ocupacion_actual == 42


def test_no_toca_promos_ni_sucursales_ya_cargadas(db):
    """Las guardas son count()==0: si ya hay data, no se agrega la del seed."""
    db.add(Promotion(
        titulo="Promo Real", descripcion="Cargada por el operador",
        costo_puntos=1, icono="fas fa-star", categoria="Test",
    ))
    db.add(ParkingBranch(
        nombre="Sucursal Propia", direccion="x", telefono="x",
        horario="x", is_24h=False, latitude=0.0, longitude=0.0,
    ))
    db.commit()

    seed_initial_data(db)

    assert db.query(Promotion).count() == 1
    assert db.query(Promotion).one().titulo == "Promo Real"
    assert db.query(ParkingBranch).count() == 1
    assert db.query(ParkingBranch).one().nombre == "Sucursal Propia"
