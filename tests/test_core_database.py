"""Test #10 de la auditoría A3: esquema de base de datos (core/database.py).

Cubre normalize_database_url, init_db (create_all) y sync_schema en sus ramas:
alembic no disponible, ya en head, upgrade exitoso, upgrade no reproducible con
stamp de rescate, y fallo total (re-raise).
"""
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

import alembic.command
import alembic.config
import alembic.runtime.migration
import alembic.script

import core.database as core_db


@pytest.fixture
def mem_engine(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    monkeypatch.setattr(core_db, "engine", engine)
    yield engine
    engine.dispose()


def _patch_alembic(monkeypatch, heads=("abc",), current="abc", upgrade=None, stamp=None):
    calls = {"upgrade": [], "stamp": []}
    monkeypatch.setattr(alembic.config, "Config", lambda *a, **k: object())

    class FakeScript:
        def get_heads(self):
            return list(heads)

    monkeypatch.setattr(alembic.script.ScriptDirectory, "from_config",
                        classmethod(lambda cls, cfg: FakeScript()))

    class FakeMigrationCtx:
        def get_current_revision(self):
            return current

    monkeypatch.setattr(alembic.runtime.migration.MigrationContext, "configure",
                        classmethod(lambda cls, conn: FakeMigrationCtx()))

    def fake_upgrade(cfg, rev):
        calls["upgrade"].append(rev)
        if upgrade:
            upgrade(rev)

    def fake_stamp(cfg, rev):
        calls["stamp"].append(rev)
        if stamp:
            stamp(rev)

    monkeypatch.setattr(alembic.command, "upgrade", fake_upgrade)
    monkeypatch.setattr(alembic.command, "stamp", fake_stamp)
    return calls


# ---------------------------------------------------------------------------
# normalize_database_url
# ---------------------------------------------------------------------------

def test_normalize_url_vacia_devuelve_sqlite():
    assert core_db.normalize_database_url("") == "sqlite:///./parking.db"
    assert core_db.normalize_database_url(None) == "sqlite:///./parking.db"


def test_normalize_postgres_a_psycopg():
    assert core_db.normalize_database_url("postgresql://u:p@h/db") == "postgresql+psycopg://u:p@h/db"


def test_normalize_respeta_urls_ya_normalizadas():
    assert core_db.normalize_database_url("postgresql+psycopg://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert core_db.normalize_database_url("sqlite:///./x.db") == "sqlite:///./x.db"
    assert core_db.normalize_database_url("sqlite+libsql://x") == "sqlite+libsql://x"


# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------

def test_init_db_crea_tablas(mem_engine):
    core_db.init_db()
    tables = inspect(mem_engine).get_table_names()
    assert "users" in tables
    assert "parking_branches" in tables
    assert "access_logs" in tables


# ---------------------------------------------------------------------------
# sync_schema
# ---------------------------------------------------------------------------

def test_sync_schema_sin_alembic_devuelve_false(mem_engine, monkeypatch):
    monkeypatch.setattr(alembic.config, "Config",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("sin alembic.ini")))
    assert core_db.sync_schema() is False


def test_sync_schema_ya_en_head_no_migra(mem_engine, monkeypatch):
    calls = _patch_alembic(monkeypatch, heads=["abc"], current="abc")
    assert core_db.sync_schema() is True
    assert calls["upgrade"] == []
    assert calls["stamp"] == []


def test_sync_schema_upgrade_exitoso(mem_engine, monkeypatch):
    calls = _patch_alembic(monkeypatch, heads=["abc"], current=None)
    assert core_db.sync_schema() is True
    assert calls["upgrade"] == ["head"]
    assert calls["stamp"] == []


def test_sync_schema_upgrade_falla_stamp_rescata(mem_engine, monkeypatch):
    def falla(rev):
        raise RuntimeError("no reproducible")

    calls = _patch_alembic(monkeypatch, heads=["abc"], current=None, upgrade=falla)
    assert core_db.sync_schema() is True
    assert calls["upgrade"] == ["head"]
    assert calls["stamp"] == ["head"]


def test_sync_schema_upgrade_y_stamp_fallan_re_raise(mem_engine, monkeypatch):
    def falla_upgrade(rev):
        raise RuntimeError("no reproducible")

    def falla_stamp(rev):
        raise RuntimeError("stamp imposible")

    _patch_alembic(monkeypatch, heads=["abc"], current=None, upgrade=falla_upgrade, stamp=falla_stamp)
    with pytest.raises(RuntimeError, match="stamp imposible"):
        core_db.sync_schema()