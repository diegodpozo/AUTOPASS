"""Tests de routes/admin/virtual_time.py (A3: el gap declarado era la ruta completa).

test_virtual_time.py cubria SOLO services/time_service.py (advance/rewind/set_target).
Las 6 rutas de admin —incluido el parsing de fecha, el rollback de _run_all_checks y
el gate de rol— estaban sin cubrir.

Cubre: GET /status y GET "" (alias), POST /advance, /rewind, /set-target (con ISO
valido e invalido -> 400), /set, /reset, el gate de local_manager (403 para staff) y
_run_all_checks ejecutando los 5 workers sin tumbar la ruta si uno falla.
"""
import datetime
import importlib
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.security import get_current_user
from models.enums import UserRole
from services.time_service import TimeService

vt_mod = importlib.import_module("routes.admin.virtual_time")

# Referencia al helper REAL, porque el fixture _no_side_effects reemplaza
# vt_mod._run_all_checks por un stub. Los tests que necesitan ejercitar el
# helper de verdad (tolerancia a fallos y guarda de los 5 pasos) la invocan
# por esta via, en vez de la referencia por el atributo del modulo.
_REAL_RUN_ALL_CHECKS = vt_mod._run_all_checks


class FakeUser:
    def __init__(self, rol=UserRole.ADMIN.value, sucursal=None):
        self.rol = rol
        self.sucursal = sucursal


CURRENT = {"user": FakeUser()}


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(vt_mod.router)
    app.dependency_overrides[get_current_user] = lambda: CURRENT["user"]
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _reset_clock():
    """Aislar el reloj virtual: es estado GLOBAL, persistido en disco.

    TimeService guarda el offset en data/virtual_time_offset.json. Sin este
    fixture, cada test que avanza el reloj deja el archivo modificado y el
    estado se filtra entre tests y entre corridas. Se restaura el archivo tal
    como estaba, para no dejar data/ sucio en el repo.
    """
    original = _leer_offset_de_disco()
    TimeService.reset()
    yield
    TimeService.reset()
    _restaurar_offset_en_disco(original)


def _leer_offset_de_disco():
    from services.time_service import _VIRTUAL_TIME_FILE

    try:
        with open(_VIRTUAL_TIME_FILE, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _restaurar_offset_en_disco(contenido):
    from services.time_service import _VIRTUAL_TIME_FILE

    try:
        if contenido is None:
            if os.path.exists(_VIRTUAL_TIME_FILE):
                os.remove(_VIRTUAL_TIME_FILE)
        else:
            with open(_VIRTUAL_TIME_FILE, "w", encoding="utf-8") as f:
                f.write(contenido)
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _no_side_effects(monkeypatch):
    """_run_all_checks() toca workers y BD reales: se stubean en todos los tests."""
    calls = []
    monkeypatch.setattr(
        vt_mod, "_run_all_checks", lambda: calls.append("checks")
    )
    return calls


def _set_user(rol=UserRole.ADMIN, sucursal=None):
    CURRENT["user"] = FakeUser(
        rol=rol.value if isinstance(rol, UserRole) else rol, sucursal=sucursal
    )


# --- GET status (y su alias "") ---

def test_get_status_devuelve_el_estado_del_reloj(client):
    r = client.get("/virtual-time/status")
    assert r.status_code == 200
    body = r.json()
    assert body["offset_seconds"] == 0
    assert body["active"] is False


def test_alias_raiz_sin_status(client):
    """El decorador doble monta "" y "/status": ambos deben responder."""
    assert client.get("/virtual-time").status_code == 200
    assert client.get("/virtual-time/status").status_code == 200


# --- POST advance / rewind ---

def test_advance_horas(client, _no_side_effects):
    r = client.post("/virtual-time/advance", json={"hours": 2})
    assert r.status_code == 200
    assert r.json()["offset_seconds"] == 7200
    assert r.json()["active"] is True
    # El ajuste siempre dispara el chequeo inmediato de workers.
    assert _no_side_effects == ["checks"]


def test_advance_todo_ceros_no_mueve_el_reloj(client, _no_side_effects):
    """Payload vacio: no debe tocar el offset, pero igual corre los checks."""
    r = client.post("/virtual-time/advance", json={})
    assert r.status_code == 200
    assert r.json()["offset_seconds"] == 0
    assert _no_side_effects == ["checks"]


def test_advance_combinado_dias_horas_minutos(client):
    r = client.post(
        "/virtual-time/advance", json={"days": 1, "hours": 1, "minutes": 1}
    )
    assert r.json()["offset_seconds"] == 90060


def test_rewind_resta_offset(client):
    client.post("/virtual-time/advance", json={"hours": 3})
    r = client.post("/virtual-time/rewind", json={"hours": 1})
    assert r.status_code == 200
    assert r.json()["offset_seconds"] == 7200


def test_rewind_puede_dejar_offset_negativo(client):
    r = client.post("/virtual-time/rewind", json={"hours": 1})
    assert r.status_code == 200
    assert r.json()["offset_seconds"] == -3600


# --- POST set-target ---

def test_set_target_con_iso_valido(client):
    target = (datetime.datetime.now() + datetime.timedelta(hours=5)).isoformat()
    r = client.post("/virtual-time/set-target", json={"target_datetime": target})
    assert r.status_code == 200
    assert 17900 <= r.json()["offset_seconds"] <= 18100


def test_set_target_con_fecha_invalida_devuelve_400(client, _no_side_effects):
    """Rama del HTTPException: no debe mover el reloj ni correr los checks."""
    r = client.post("/virtual-time/set-target", json={"target_datetime": "no-es-fecha"})
    assert r.status_code == 400
    assert "ISO" in r.json()["detail"]
    assert TimeService.get_offset() == 0
    assert _no_side_effects == []


def test_set_target_sin_campo_requerido_devuelve_422(client):
    """offset_seconds/target_datetime es obligatorio: Pydantic lo rechaza."""
    assert client.post("/virtual-time/set-target", json={}).status_code == 422


# --- POST set / reset ---

def test_set_offset_absoluto(client):
    r = client.post("/virtual-time/set", json={"offset_seconds": -600})
    assert r.status_code == 200
    assert r.json()["offset_seconds"] == -600


def test_reset_deja_el_reloj_en_cero(client):
    client.post("/virtual-time/set", json={"offset_seconds": 5000})
    r = client.post("/virtual-time/reset")
    assert r.status_code == 200
    assert r.json()["offset_seconds"] == 0
    assert r.json()["active"] is False


# --- Gate de rol ---

def test_staff_no_puede_manipular_el_reloj(client):
    """get_local_manager acepta ADMIN y LOCAL_ADMIN, pero NO staff."""
    _set_user(rol=UserRole.STAFF)
    r = client.post("/virtual-time/advance", json={"hours": 1})
    assert r.status_code == 403
    assert TimeService.get_offset() == 0


def test_admin_global_si_puede(client):
    """El docstring de get_local_manager dice 'global o local': admin global entra."""
    _set_user(rol=UserRole.ADMIN)
    assert client.post("/virtual-time/advance", json={"hours": 1}).status_code == 200


def test_local_admin_si_puede(client):
    _set_user(rol=UserRole.LOCAL_ADMIN, sucursal="AUTOPASS Central")
    assert client.post("/virtual-time/advance", json={"hours": 1}).status_code == 200


def test_status_tambien_exige_rol_administrativo(client):
    """El gate protege tambien la lectura: staff no ve el estado del reloj."""
    _set_user(rol=UserRole.STAFF)
    assert client.get("/virtual-time/status").status_code == 403


# --- _run_all_checks: tolerancia a fallos ---

class _DB:
    """Session stub: _run_all_checks abre y cierra una sesion real."""

    def close(self):
        pass


def test_run_all_checks_no_tumba_la_ruta_si_un_worker_falla(monkeypatch):
    """Un worker que explota se loguea, no propaga: la ruta debe responder 200."""
    def boom(db):
        raise RuntimeError("worker caido")

    monkeypatch.setattr(vt_mod.WorkerService, "_process_reminders", boom)
    monkeypatch.setattr(vt_mod.WorkerService, "_process_started_reservations", lambda db: None)
    monkeypatch.setattr(vt_mod.WorkerService, "_process_auto_cancellations", lambda db: None)
    monkeypatch.setattr(vt_mod.ReservationService, "cleanup_overdue_reservations", lambda db: None)
    monkeypatch.setattr(vt_mod.ReservationService, "auto_finalize_all_reservations", lambda db: None)
    monkeypatch.setattr(vt_mod, "SessionLocal", _DB)

    _REAL_RUN_ALL_CHECKS()  # no debe levantar


def test_run_all_checks_invoca_los_cinco_pasos(monkeypatch):
    """Guard contra regresiones: los 5 workers del chequeo inmediato se siguen invocando."""
    vistos = []
    for nombre in (
        "_process_reminders", "_process_started_reservations", "_process_auto_cancellations",
    ):
        monkeypatch.setattr(
            vt_mod.WorkerService, nombre,
            (lambda n: lambda db: vistos.append(n))(nombre),
        )
    for nombre in (
        "cleanup_overdue_reservations", "auto_finalize_all_reservations",
    ):
        monkeypatch.setattr(
            vt_mod.ReservationService, nombre,
            (lambda n: lambda db: vistos.append(n))(nombre),
        )
    monkeypatch.setattr(vt_mod, "SessionLocal", _DB)

    _REAL_RUN_ALL_CHECKS()

    assert len(vistos) == 5
