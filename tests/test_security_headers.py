"""Regresión de headers de seguridad (CSP) en main.py.

Verifica que la CSP permita los orígenes externos que usa la landing:
fonts de Font Awesome (cdnjs) y APIs de mapas (overpass/nominatim).
"""
from fastapi.testclient import TestClient

from main import app


def test_csp_permite_fuentes_de_cdnjs_y_apis_de_mapas():
    r = TestClient(app).get("/static/manifest.json")
    csp = r.headers.get("content-security-policy", "")

    font_src = next(d for d in csp.split("; ") if d.startswith("font-src"))
    assert "https://cdnjs.cloudflare.com" in font_src

    connect_src = next(d for d in csp.split("; ") if d.startswith("connect-src"))
    assert "https://overpass-api.de" in connect_src
    assert "https://nominatim.openstreetmap.org" in connect_src
    assert "https://cdn.jsdelivr.net" in connect_src
    assert "https://unpkg.com" in connect_src


def test_headers_de_seguridad_basicos_presentes():
    r = TestClient(app).get("/static/manifest.json")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"