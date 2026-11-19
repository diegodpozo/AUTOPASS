"""Pruebas unitarias para la detección automática de cámaras USB / celulares USB

y conmutación inteligente entre USB e IP (alpr/camera_detector.py).
"""
import numpy as np
import pytest
from unittest.mock import MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

import models
from models.enums import UserRole
from core.security import get_operational_user
from routes.system.cameras import router as cameras_router
from alpr.camera_detector import (
    is_device_available,
    find_available_usb_cameras,
    resolve_video_source,
)


def _make_fake_cap(is_opened=True, read_ok=True, has_frame=True, is_static_placeholder=False):
    mock = MagicMock()
    mock.isOpened.return_value = is_opened
    call_count = {"n": 0}

    def fake_read():
        call_count["n"] += 1
        if read_ok and has_frame:
            if is_static_placeholder:
                # Placeholder estático 'Start DroidCam': idéntico en cada lectura y oscuro
                return True, np.full((480, 640, 3), 4, dtype=np.uint8)
            # Frame real con variación temporal natural
            base_val = 100 + (call_count["n"] * 5)
            return True, np.full((480, 640, 3), base_val, dtype=np.uint8)
        elif read_ok and not has_frame:
            return True, None
        return False, None

    mock.read.side_effect = fake_read
    return mock


class TestDeviceAvailable:
    def test_device_available_success(self, monkeypatch):
        fake_cap = _make_fake_cap(is_opened=True, read_ok=True)
        monkeypatch.setattr("cv2.VideoCapture", lambda *args, **kwargs: fake_cap)

        assert is_device_available(0) is True
        assert fake_cap.release.called

    def test_device_not_opened(self, monkeypatch):
        fake_cap = _make_fake_cap(is_opened=False)
        monkeypatch.setattr("cv2.VideoCapture", lambda *args, **kwargs: fake_cap)

        assert is_device_available(0) is False
        assert fake_cap.release.called

    def test_device_read_fails(self, monkeypatch):
        fake_cap = _make_fake_cap(is_opened=True, read_ok=False)
        monkeypatch.setattr("cv2.VideoCapture", lambda *args, **kwargs: fake_cap)

        assert is_device_available(0) is False

    def test_device_exception_handled(self, monkeypatch):
        def raise_err(*args, **kwargs):
            raise RuntimeError("Dispositivo ocupado o desconectado")

        monkeypatch.setattr("cv2.VideoCapture", raise_err)
        assert is_device_available(0) is False

    def test_device_detected_as_static_placeholder_rejected(self, monkeypatch):
        fake_cap = _make_fake_cap(is_opened=True, read_ok=True, is_static_placeholder=True)
        monkeypatch.setattr("cv2.VideoCapture", lambda *args, **kwargs: fake_cap)
        assert is_device_available(0) is False


class TestFindAvailableUsbCameras:
    def test_find_cameras_returns_available_indices(self, monkeypatch):
        # 0 disponible, 1 ocupado, 2 disponible, 3 ocupado
        status_map = {0: True, 1: False, 2: True, 3: False}
        monkeypatch.setattr(
            "alpr.camera_detector.is_device_available",
            lambda idx: status_map.get(idx, False)
        )

        found = find_available_usb_cameras(max_devices=4)
        assert found == [0, 2]

    def test_find_cameras_none_available(self, monkeypatch):
        monkeypatch.setattr("alpr.camera_detector.is_device_available", lambda idx: False)
        assert find_available_usb_cameras(max_devices=4) == []


class TestResolveVideoSource:
    def test_entrada_with_single_usb_camera(self):
        source, msg = resolve_video_source(
            configured_source="http://192.168.0.132:8080/video",
            gate_type="entrada",
            auto_detect_usb=True,
            available_devices=[0]
        )
        assert source == 0
        assert "Entrada conectada automáticamente a cámara USB (Dispositivo 0)" in msg

    def test_entrada_without_usb_falls_back_to_ip(self):
        source, msg = resolve_video_source(
            configured_source="http://192.168.0.132:8080/video",
            gate_type="entrada",
            auto_detect_usb=True,
            available_devices=[]
        )
        assert source == "http://192.168.0.132:8080/video"
        assert "No se detectó cámara USB conectada para Entrada" in msg
        assert "Conectando a IP: http://192.168.0.132:8080/video" in msg

    def test_salida_with_single_usb_camera_reuses_device_0(self):
        # Escenario: entrada se detuvo, salida toma el dispositivo 0 libre
        source, msg = resolve_video_source(
            configured_source="http://192.168.0.132:8080/video",
            gate_type="salida",
            auto_detect_usb=True,
            available_devices=[0]
        )
        assert source == 0
        assert "Salida conectada automáticamente a cámara USB disponible (Dispositivo 0)" in msg

    def test_salida_with_two_usb_cameras_uses_device_1(self):
        # Escenario: entrada y salida simultáneas con 2 cámaras USB conectadas
        source, msg = resolve_video_source(
            configured_source="http://192.168.0.132:8080/video",
            gate_type="salida",
            auto_detect_usb=True,
            available_devices=[0, 1]
        )
        assert source == 1
        assert "Salida conectada automáticamente a cámara USB (Dispositivo 1)" in msg

    def test_salida_without_usb_falls_back_to_ip(self):
        source, msg = resolve_video_source(
            configured_source="http://192.168.0.132:8080/video",
            gate_type="salida",
            auto_detect_usb=True,
            available_devices=[]
        )
        assert source == "http://192.168.0.132:8080/video"
        assert "No se detectó cámara USB conectada para Salida" in msg

    def test_patente_gate_aliases_supported(self):
        # Soporta PATENTE_INGRESO y PATENTE_EGRESO
        src_in, _ = resolve_video_source("http://ip/in", "PATENTE_INGRESO", available_devices=[0])
        src_out, _ = resolve_video_source("http://ip/out", "PATENTE_EGRESO", available_devices=[0])
        assert src_in == 0
        assert src_out == 0

    def test_predio_keeps_configured_ip_source(self):
        # Cámaras de vigilancia del predio mantienen su IP por defecto
        source, msg = resolve_video_source(
            configured_source="http://172.17.111.65:8080/video",
            gate_type="predio",
            auto_detect_usb=True,
            available_devices=[0]
        )
        assert source == "http://172.17.111.65:8080/video"
        assert "Usando fuente configurada" in msg

    def test_explicit_numeric_index_source_is_respected(self):
        # Si el usuario configura explícitamente el índice "1", no se debe forzar al índice 0
        src_str, msg_str = resolve_video_source(
            configured_source="1",
            gate_type="entrada",
            auto_detect_usb=True,
            available_devices=[0, 1]
        )
        assert src_str == 1
        assert "Usando cámara USB configurada explícitamente" in msg_str

        src_int, msg_int = resolve_video_source(
            configured_source=1,
            gate_type="entrada",
            auto_detect_usb=True,
            available_devices=[0, 1]
        )
        assert src_int == 1

    def test_auto_detect_disabled_respects_configured_source(self):
        source, msg = resolve_video_source(
            configured_source="http://192.168.0.132:8080/video",
            gate_type="entrada",
            auto_detect_usb=False,
            available_devices=[0]
        )
        assert source == "http://192.168.0.132:8080/video"


class TestDetectDevicesEndpoint:
    @pytest.fixture
    def test_client(self):
        app = FastAPI()
        fake_admin = models.User(id=1, email="admin@test.com", rol=UserRole.ADMIN)
        app.dependency_overrides[get_operational_user] = lambda: fake_admin
        app.include_router(cameras_router, prefix="/v1/system")
        return TestClient(app)

    def test_detect_devices_endpoint(self, test_client, monkeypatch):
        monkeypatch.setattr("alpr.camera_detector.find_available_usb_cameras", lambda max_devices: [0])

        res = test_client.get("/v1/system/cameras/detect-devices")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["available_usb_cameras"] == [0]
        assert data["count"] == 1
        assert "1 cámara(s) USB detectada(s)" in data["message"]

    def test_detect_devices_none_found(self, test_client, monkeypatch):
        monkeypatch.setattr("alpr.camera_detector.find_available_usb_cameras", lambda max_devices: [])

        res = test_client.get("/v1/system/cameras/detect-devices")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["available_usb_cameras"] == []
        assert data["count"] == 0
        assert "No se detectaron cámaras USB" in data["message"]
