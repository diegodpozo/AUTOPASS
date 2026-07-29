"""
Paquete ALPR (Automatic License Plate Recognition) para AUTOPASS.
Procesamiento de video, visión artificial, EasyOCR y comunicación WebSocket.
"""

from alpr.config import GATE_TYPE, GATE_ID, VIDEO_SOURCE, BACKEND_URL
from alpr.ocr_engine import ALPREngine
from alpr.video_streamer import VideoStreamer
from alpr.ws_client import ws_monitoring_worker

__all__ = ["GATE_TYPE", "GATE_ID", "VIDEO_SOURCE", "BACKEND_URL", "ALPREngine", "VideoStreamer", "ws_monitoring_worker"]
