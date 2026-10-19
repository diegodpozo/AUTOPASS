"""FASE 1 - TESTS UNITARIOS DE LA ARITMETICA ATOMICA DE LA CUENTA.

Cubre el API nuevo de `UserRepository` (saldo y puntos en un solo UPDATE):
valor devuelto, variantes condicionales (0 filas = no alcanza), el tope cero de
puntos y los usuarios viejos con la columna en NULL.

Los tests de carrera real (dos hilos) estan en
`tests/test_concurrencia_saldo_puntos.py`; aca se fija el contrato de cada helper.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.database import Base
from repositories.user_repository import UserRepository


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    sesion = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield sesion
    finally:
        sesion.close()


def _usuario(db, saldo=0.0, puntos=0):
    u = models.User(
        nombre="Cuenta", apellido="Atomica", dni="12345678", email="cuenta@test.com",
        password_hash="x", rol="user", saldo=saldo, puntos_acumulados=puntos,
    )
    db.add(u)
    db.commit()
    return u


def test_sumar_saldo_devuelve_el_valor_nuevo_y_sincroniza_el_objeto(db):
    u = _usuario(db, saldo=100.0)
    assert UserRepository.sumar_saldo(db, u, 50.0) == 150.0
    # El objeto ORM quedo sincronizado: leer el atributo trae el valor nuevo.
    assert u.saldo == 150.0


def test_descontar_saldo_con_saldo_suficiente(db):
    u = _usuario(db, saldo=100.0)
    assert UserRepository.descontar_saldo(db, u, 60.0) == 40.0
    assert u.saldo == 40.0


def test_descontar_saldo_sin_saldo_suficiente_no_modifica_nada(db):
    u = _usuario(db, saldo=100.0)
    # None = no alcanzaba; y el saldo tiene que quedar intacto.
    assert UserRepository.descontar_saldo(db, u, 500.0) is None
    assert u.saldo == 100.0


def test_descontar_saldo_con_saldo_nulo_es_insuficiente(db):
    """Usuarios viejos con saldo NULL: COALESCE lo trata como 0, no revienta."""
    u = _usuario(db, saldo=None)
    assert UserRepository.descontar_saldo(db, u, 1.0) is None


def test_fijar_saldo_es_absoluto(db):
    u = _usuario(db, saldo=100.0)
    assert UserRepository.fijar_saldo(db, u, 500.0) == 500.0
    assert u.saldo == 500.0


def test_sumar_puntos_devuelve_el_total(db):
    u = _usuario(db, puntos=10)
    assert UserRepository.sumar_puntos(db, u, 5) == 15
    assert u.puntos_acumulados == 15


def test_canjear_puntos_sin_puntos_suficientes_no_descuenta(db):
    u = _usuario(db, puntos=80)
    assert UserRepository.canjear_puntos(db, u, 100) is None
    assert u.puntos_acumulados == 80


def test_canjear_puntos_con_puntos_suficientes(db):
    u = _usuario(db, puntos=80)
    assert UserRepository.canjear_puntos(db, u, 50) == 30
    assert u.puntos_acumulados == 30


def test_descontar_puntos_tope_cero_nunca_deja_negativo(db):
    u = _usuario(db, puntos=5)
    assert UserRepository.descontar_puntos_tope_cero(db, u, 10) == 0
    assert u.puntos_acumulados == 0


def test_puntos_nulos_se_tratan_como_cero(db):
    u = _usuario(db, puntos=None)
    assert UserRepository.sumar_puntos(db, u, 7) == 7
    assert UserRepository.canjear_puntos(db, u, 100) is None
    assert UserRepository.descontar_puntos_tope_cero(db, u, 3) == 4
