"""Cobertura de `_version()` en core/config.py.

La version se deriva del historial de commits, no de un valor fijo. El repo
usa dos estilos de subject, conviven:

- canonico   `v9.34.79: la documentacion afirmaba un estado que ya no tenia`
- incidental `refactor(v9.34.17): COMPONENTES P2 - migracion BEM ...`

Por eso la busqueda retrocede en el historial en vez de mirar solo HEAD: hay
commits `fix(sw):`, `docs:` y `wipNN` que no llevan ninguna version, y con
solo HEAD la app reportaba `0.0.0` en silencio.

Se testean las ramas: canonico, incidental, retroceso, prioridad del canonico,
sin git, historial vacio, sin version y cache.
"""
import subprocess

import pytest

from core import config
from core.config import _FALLBACK_VERSION


class _Result:
    """Imita CompletedProcess. Con `raise_exc` hace fallar el `.stdout`,
    que es donde `_version()` lee la salida (y donde fallaria git de verdad)."""

    def __init__(self, stdout="", raise_exc=False):
        self._stdout = stdout
        self._raise = raise_exc

    @property
    def stdout(self):
        if self._raise:
            raise subprocess.CalledProcessError(1, "git", stderr="not a git repository")
        return self._stdout


@pytest.fixture(autouse=True)
def _clear_cache():
    config._version.cache_clear()
    yield
    config._version.cache_clear()


def _fake_history(monkeypatch, subjects, raise_exc=False):
    """Devuelve la salida de `git log` como la lista de subjects mas recientes."""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return _Result("\n".join(subjects) + ("\n" if subjects else ""), raise_exc)

    monkeypatch.setattr(config.subprocess, "run", fake_run)
    return calls


# --- camino feliz -----------------------------------------------------------

def test_lee_version_canonica_de_head(monkeypatch):
    _fake_history(monkeypatch, ["v9.34.79: la documentacion afirmaba un estado viejo"])
    assert config._version() == "9.34.79"


def test_acepta_subject_sin_espacio_tras_los_dos_puntos(monkeypatch):
    _fake_history(monkeypatch, ["v9.34.80:algo"])
    assert config._version() == "9.34.80"


# --- el bug: HEAD sin version ----------------------------------------------

def test_retrocede_cuando_head_no_lleva_version(monkeypatch):
    """`fix(sw): ...` en HEAD no debe dejar la version en 0.0.0."""
    _fake_history(monkeypatch, [
        "fix(sw): servicio worker robusto en peticiones CDN",
        "wip77",
        "v9.34.77: estado de error visible en los campos obligatorios",
    ])
    assert config._version() == "9.34.77"


def test_retrocede_por_varios_commits_sin_version(monkeypatch):
    _fake_history(monkeypatch, [
        "Merge branch 'main' of https://github.com/MarianoJAC/AUTOPASS",
        "fix(sw): algo roto",
        "docs: informes de auditoria",
        "v9.34.74: la superficie del select era --bg-input",
    ])
    assert config._version() == "9.34.74"


# --- version incidental -----------------------------------------------------

def test_acepta_version_incidental_en_parentesis(monkeypatch):
    """455 de los 579 commits del repo usan `refactor(v9.34.17):` o `docs(v9.31.3):`."""
    _fake_history(monkeypatch, ["refactor(v9.34.17): COMPONENTES P2 - migracion BEM"])
    assert config._version() == "9.34.17"


def test_acepta_fix_con_version_incidental(monkeypatch):
    _fake_history(monkeypatch, [
        "fix(v9.21.0): delegacion de reservas/vehiculos a servicios",
    ])
    assert config._version() == "9.21.0"


# --- prioridad del canonico ------------------------------------------------

def test_canonico_gana_sobre_mencion_incidental_mas_antigua(monkeypatch):
    """Un commit viejo que menciona una version no debe pisar la canonica actual."""
    _fake_history(monkeypatch, [
        "fix(sw): algo roto",
        "revert(v9.30.0): volver a v9.30.0 por un problema de CSS",
        "v9.34.79: la version vigente",
    ])
    assert config._version() == "9.34.79"


# --- degradaciones ----------------------------------------------------------

def test_devuelve_fallback_si_git_falla(monkeypatch):
    _fake_history(monkeypatch, [], raise_exc=True)
    assert config._version() == _FALLBACK_VERSION


def test_devuelve_fallback_si_historial_vacio(monkeypatch):
    _fake_history(monkeypatch, [])
    assert config._version() == _FALLBACK_VERSION


def test_devuelve_fallback_si_ningun_commit_menciona_version(monkeypatch):
    _fake_history(monkeypatch, ["wip77", "wip76", "docs: sin version", "Merge branch"])
    assert config._version() == _FALLBACK_VERSION


def test_ignora_lines_vacias(monkeypatch):
    _fake_history(monkeypatch, ["", "   ", "v9.34.70: con lineas vacias alrededor"])
    assert config._version() == "9.34.70"


# --- parametros del comando -------------------------------------------------

def test_pide_una_ventana_de_commits_limitada(monkeypatch):
    """Un repo con 579 commits no debe leerlos todos para versionar."""
    calls = _fake_history(monkeypatch, ["v9.34.79: algo"])
    config._version()
    assert "-50" in calls[0]
    assert "-1" not in calls[0]


def test_settings_expone_la_forma_del_dato():
    assert config.Settings.VERSION.count(".") == 2


def test_cache_evita_reinvocar_git(monkeypatch):
    calls = _fake_history(monkeypatch, ["v9.34.79: algo"])
    config._version()
    config._version()
    config._version()
    assert len(calls) == 1