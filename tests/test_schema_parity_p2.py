"""Test A5-P2: paridad de índices entre el modelo (create_all) y la cadena Alembic.

Previene el re-desfase de índices modelo<->alembic documentado en
AUDITORIA_RENDIMIENTO.md (ix_access_logs_id + ix_{tabla}_id redundantes sobre
la PK y el fix de ix_mercadopago_payments_user_id).
"""
import os
import sqlite3

import logging.config

import pytest
import sqlalchemy as sa

import models  # noqa: F401
from core.config import settings
from core.database import Base


def _run_alembic_head(tmp_file, monkeypatch):
    from alembic import command
    from alembic.config import Config

    monkeypatch.setattr(settings, "DATABASE_URL", "sqlite:///" + tmp_file.replace("\\", "/"))
    monkeypatch.setattr(logging.config, "fileConfig", lambda *a, **k: None)
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", "sqlite:///" + tmp_file.replace("\\", "/"))
    command.upgrade(cfg, "head")


def _index_names_from_models():
    return {f"{t.name}.{i.name}" for t in Base.metadata.sorted_tables for i in t.indexes}


def _index_names_from_db(tmp_file):
    con = sqlite3.connect(tmp_file)
    try:
        return {
            f"{tbl}.{name}"
            for name, tbl in con.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
            if "sqlite_autoindex" not in name
        }
    finally:
        con.close()


def test_paridad_indices_modelo_vs_alembic(tmp_path, monkeypatch):
    db = str(tmp_path / "parity.db")
    _run_alembic_head(db, monkeypatch)

    model_idx = _index_names_from_models()
    db_idx = _index_names_from_db(db)

    missing = sorted(model_idx - db_idx)
    extra = sorted(db_idx - model_idx)
    assert missing == [], f"Índices del modelo que faltan en alembic: {missing}"
    assert extra == [], f"Índices en alembic que no declara el modelo: {extra}"


def test_no_hay_indices_redundantes_sobre_pk(tmp_path):
    """La PK ya indexa id: ningún modelo debe pedir un índice adicional sobre el PK."""
    for t in Base.metadata.sorted_tables:
        for col in t.primary_key.columns:
            assert not col.index, (
                f"{t.name}.{col.name} declara index=True sobre la PK (redundante, se alinea a alembic sin él)"
            )