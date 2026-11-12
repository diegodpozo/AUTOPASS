import pytest
from fastapi.testclient import TestClient
from main import app
from core.config import settings
from core.security import create_access_token
from services.hardware_service import HardwareService
from models.enums import UserRole
from scripts.arduino_bridge import build_ws_url, process_barrier_payload, ArduinoController

client = TestClient(app)


def test_hardware_ws_sin_auth_es_rechazado(monkeypatch):
    """Cliente sin secreto ni token con IP no confiable debe ser rechazado con 4403."""
    monkeypatch.setattr(settings, "ALPR_NODE_SECRET", "super_secreto_hardware")
    
    with pytest.raises(Exception):
        with client.websocket_connect("/v1/system/ws/hardware") as ws:
            ws.receive_json()


def test_hardware_ws_con_secret_autorizado(monkeypatch):
    """Cliente con secreto correcto se conecta y recibe mensaje de bienvenida."""
    monkeypatch.setattr(settings, "ALPR_NODE_SECRET", "super_secreto_hardware")

    with client.websocket_connect("/v1/system/ws/hardware?node_secret=super_secreto_hardware") as ws:
        data = ws.receive_json()
        assert data.get("type") == "info"
        assert "conectado" in data.get("message", "").lower()

        # Probar ping -> pong
        ws.send_text("ping")
        resp = ws.receive_text()
        assert resp == "pong"


def test_hardware_ws_con_secret_key_autorizado(monkeypatch):
    """Cliente con SECRET_KEY como fallback se conecta exitosamente."""
    monkeypatch.setattr(settings, "ALPR_NODE_SECRET", "")
    monkeypatch.setattr(settings, "SECRET_KEY", "mi_secret_key_demo")

    with client.websocket_connect("/v1/system/ws/hardware?secret=mi_secret_key_demo") as ws:
        data = ws.receive_json()
        assert data.get("type") == "info"


def test_hardware_ws_con_token_operativo():
    """Personal operativo con JWT válido puede conectarse al WebSocket de hardware."""
    token = create_access_token(data={"sub": "admin@autopass.com", "rol": UserRole.ADMIN.value})

    with client.websocket_connect(f"/v1/system/ws/hardware?token={token}") as ws:
        data = ws.receive_json()
        assert data.get("type") == "info"


def test_hardware_service_broadcast_ws(monkeypatch):
    """Al disparar trigger_barrier, los clientes WebSocket reciben el payload."""
    monkeypatch.setattr(settings, "ALPR_NODE_SECRET", "test_sec")
    # Desactivar serial y mqtt en el test
    monkeypatch.setattr(HardwareService, "publish_mqtt", classmethod(lambda cls, *a, **k: None))
    monkeypatch.setattr(HardwareService, "send_serial_command", staticmethod(lambda *a, **k: False))

    with client.websocket_connect("/v1/system/ws/hardware?secret=test_sec") as ws:
        # Bienvenida
        ws.receive_json()

        # Disparar barrera
        HardwareService.trigger_barrier("ENTRADA", "OPEN", method="TEST_WS", details={"test": 123})

        evento = ws.receive_json()
        assert evento["command"] == "OPEN"
        assert evento["gate"] == "ENTRADA"
        assert evento["method"] == "TEST_WS"
        assert evento["test"] == 123


def test_build_ws_url():
    """Valida la conversión de URLs HTTP/HTTPS a WS/WSS."""
    assert build_ws_url("https://prueba.trycloudflare.com", "secreto123") == "wss://prueba.trycloudflare.com/v1/system/ws/hardware?node_secret=secreto123"
    assert build_ws_url("http://100.64.0.1:8000") == "ws://100.64.0.1:8000/v1/system/ws/hardware"
    assert build_ws_url("ws://localhost:8000/v1/system/ws/hardware") == "ws://localhost:8000/v1/system/ws/hardware"


def test_process_barrier_payload(monkeypatch):
    """Verifica que el payload recibido se transforme en el comando para Arduino."""
    sent = []
    ctrl = ArduinoController(target_port="MOCK")
    monkeypatch.setattr(ctrl, "send_command", lambda cmd: sent.append(cmd))

    process_barrier_payload({"command": "OPEN", "gate": "ENTRADA", "method": "ALPR"}, ctrl)
    assert sent == ["OPEN_ENTRADA"]

    process_barrier_payload({"command": "CLOSE", "gate": "SALIDA", "method": "MANUAL"}, ctrl)
    assert sent == ["OPEN_ENTRADA", "CLOSE_SALIDA"]
