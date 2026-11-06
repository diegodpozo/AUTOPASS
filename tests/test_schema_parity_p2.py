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


def _run_alembic_revision(tmp_file, monkeypatch, revision):
    from alembic import command
    from alembic.config import Config

    monkeypatch.setattr(settings, "DATABASE_URL", "sqlite:///" + tmp_file.replace("\\", "/"))
    monkeypatch.setattr(logging.config, "fileConfig", lambda *a, **k: None)
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", "sqlite:///" + tmp_file.replace("\\", "/"))
    command.upgrade(cfg, revision)


def _run_alembic_head(tmp_file, monkeypatch):
    _run_alembic_revision(tmp_file, monkeypatch, "head")


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


def test_datetime_migration_preserves_sqlite_text_values(tmp_path, monkeypatch):
    from datetime import datetime
    from sqlalchemy.orm import Session

    from models.organization import Organization
    from models.parking import ParkingAforo
    from models.user import RedemptionTicket

    db = str(tmp_path / "datetime-migration.db")
    _run_alembic_revision(db, monkeypatch, "b1c2d3e4f5a6")

    expected = {
        ("parking_aforo", "ultima_actualizacion"): "2026-10-08 00:36:31.444579+00",
        ("organizations", "created_at"): "2026-10-13T20:19:20.389478",
        ("redemption_tickets", "created_at"): "2026-09-01T11:07:53.949775",
        ("redemption_tickets", "fecha_uso"): "2026-09-01T12:07:53.949775",
    }
    row_id = 987654
    con = sqlite3.connect(db)
    con.execute(
        "INSERT INTO parking_aforo (id, ultima_actualizacion) VALUES (?, ?)",
        (row_id, expected[("parking_aforo", "ultima_actualizacion")]),
    )
    con.execute(
        "INSERT INTO organizations (id, nombre, created_at) VALUES (?, ?, ?)",
        (row_id, "migration timestamp test", expected[("organizations", "created_at")]),
    )
    con.execute(
        "INSERT INTO redemption_tickets (id, created_at, fecha_uso) VALUES (?, ?, ?)",
        (
            row_id,
            expected[("redemption_tickets", "created_at")],
            expected[("redemption_tickets", "fecha_uso")],
        ),
    )
    con.commit()
    con.close()

    _run_alembic_head(db, monkeypatch)

    con = sqlite3.connect(db)
    try:
        for (table, column), value in expected.items():
            saved_value, storage_type = con.execute(
                f'SELECT "{column}", typeof("{column}") FROM "{table}" WHERE id = ?',
                (row_id,),
            ).fetchone()
            assert saved_value == value
            assert storage_type == "text"
    finally:
        con.close()

    engine = sa.create_engine("sqlite:///" + db.replace("\\", "/"))
    try:
        with Session(engine) as session:
            assert isinstance(session.get(ParkingAforo, row_id).ultima_actualizacion, datetime)
            assert isinstance(session.get(Organization, row_id).created_at, datetime)
            ticket = session.get(RedemptionTicket, row_id)
            assert isinstance(ticket.created_at, datetime)
            assert isinstance(ticket.fecha_uso, datetime)
    finally:
        engine.dispose()