'''Detección y resolución automática de fuentes de video (USB / Celular USB vs. IP) para cámaras ALPR y de monitoreo.'''

import os
import sys
from typing import List, Tuple, Union
import cv2

from core.logger import get_logger

logger = get_logger("CameraDetector")


def is_dummy_green_frame(frame) -> bool:
    """Detecta si un frame es una imagen sólida verde de standby/inactividad

    (típica de drivers virtuales como DroidCam / OBS cuando no tienen transmisión activa).
    """
    if frame is None or getattr(frame, "size", 0) == 0:
        return True
    try:
        mean_b = float(frame[:, :, 0].mean())
        mean_g = float(frame[:, :, 1].mean())
        mean_r = float(frame[:, :, 2].mean())
        std = float(frame.std())
        return mean_g > 80 and mean_b < 40 and mean_r < 40 and std < 10.0
    except Exception:
        return False


def is_device_available(index: int, timeout_sec: float = 0.5) -> bool:
    """Verifica si un índice local de cámara (webcam física o celular en modo USB)

    está disponible, no está tomado por otro proceso y entrega frames válidos.
    """
    cap = None
    try:
        # En Windows DirectShow suele ser el más rápido para detectar disponibilidad
        if os.name == 'nt' and hasattr(cv2, 'CAP_DSHOW'):
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap.release()
                cap = cv2.VideoCapture(index)
        else:
            cap = cv2.VideoCapture(index)

        if not cap or not cap.isOpened():
            return False

        # Intentar leer 2 frames separados para certificar que el dispositivo responde con video en vivo
        # y no con una imagen fija/placeholder de espera (como 'Start DroidCam' o pantalla de prueba)
        ret1, f1 = cap.read()
        if not ret1 or f1 is None or getattr(f1, "size", 0) == 0:
            return False

        # Si entrega pantalla verde sólida de standby, no es una cámara lista
        if is_dummy_green_frame(f1):
            logger.info(f"Dispositivo índice {index} entrega imagen verde de standby (espera de DroidCam)")
            return False

        import time
        import numpy as np
        time.sleep(0.15)
        ret2, f2 = cap.read()
        if not ret2 or f2 is None:
            return False

        # Si la imagen es absolutamente estática (diff == 0.0) y oscura/placeholder,
        # es el cartel 'Start DroidCam' del driver virtual sin transmisión activa
        diff = float(np.abs(f1.astype(np.float32) - f2.astype(np.float32)).mean())
        if diff == 0.0 and float(f1.mean()) < 25.0:
            logger.info(f"Dispositivo índice {index} es placeholder estático de driver (Start DroidCam)")
            return False

        return True
    except Exception as e:
        logger.debug(f"Error comprobando dispositivo USB índice {index}: {e}")
        return False
    finally:
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass


def find_available_usb_cameras(max_devices: int = 4) -> List[int]:
    """Escanea índices 0..max_devices-1 buscando cámaras USB / DirectShow

    activas y libres. Retorna la lista de índices funcionales.
    """
    # Silenciar logs ruidosos de OpenCV durante el sondeo
    prev_log_level = os.environ.get("OPENCV_LOG_LEVEL", "")
    os.environ["OPENCV_LOG_LEVEL"] = "OFF"
    try:
        if hasattr(cv2, "utils") and hasattr(cv2.utils, "logging"):
            cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)
    except Exception:
        pass

    available: List[int] = []
    try:
        for idx in range(max_devices):
            if is_device_available(idx):
                available.append(idx)
    finally:
        if prev_log_level:
            os.environ["OPENCV_LOG_LEVEL"] = prev_log_level

    return available


def resolve_video_source(
    configured_source: Union[str, int],
    gate_type: str = "entrada",
    auto_detect_usb: bool = True,
    available_devices: List[int] = None
) -> Tuple[Union[str, int], str]:
    """Resuelve la fuente de video adecuada:

    1. Si `auto_detect_usb` está activo y es carril de patente/acceso (entrada o salida):
       - Si hay webcam USB disponible: la conecta automáticamente (prioridad USB).
       - Si hay solo 1 USB y se usa secuencialmente (entrada parada, luego salida):
         ambas pueden aprovechar el dispositivo 0.
       - Si hay 2 USBs simultáneas: entrada toma 0 y salida toma 1.
    2. Si no hay cámara USB disponible: conmuta automáticamente a la IP configurada.
    3. Si es PREDIO / vigilancia y no se forzó USB: usa la fuente configurada.

    Retorna: (fuente_resuelta, mensaje_diagnostico)
    """
    gt = (gate_type or "").lower().strip()
    is_alpr_gate = any(k in gt for k in ("entrada", "ingreso", "salida", "egreso", "patente", "qr"))

    # Si no es un carril de acceso ni tiene autodetección activada, mantener fuente configurada
    if not auto_detect_usb or not is_alpr_gate:
        return configured_source, f"[INFO] Modo {gt.upper()}: Usando fuente configurada ({configured_source})"

    # Si el usuario configuró explícitamente un índice numérico local (ej: "0", "1", 0, 1),
    # respetar esa selección manual en vez de forzar el primer dispositivo detectado
    is_explicit_local = (
        isinstance(configured_source, int) or
        (isinstance(configured_source, str) and str(configured_source).strip().isdigit())
    )
    if is_explicit_local:
        chosen_idx = int(configured_source)
        if available_devices is not None and len(available_devices) > 0:
            if chosen_idx in available_devices:
                return chosen_idx, f"[OK] Usando cámara USB configurada explícitamente (Dispositivo {chosen_idx})"
            else:
                return chosen_idx, f"[AVISO] Cámara USB {chosen_idx} configurada pero no figura en dispositivos disponibles"
        return chosen_idx, f"[OK] Usando cámara USB configurada explícitamente (Dispositivo {chosen_idx})"

    # Obtener dispositivos disponibles si no fueron inyectados (inyección útil para tests)
    if available_devices is None:
        available_devices = find_available_usb_cameras(max_devices=4)

    is_exit = any(k in gt for k in ("salida", "egreso"))

    if is_exit:
        # Carril de salida
        if len(available_devices) >= 2:
            # Hay 2 o más cámaras USB: Salida toma la segunda para permitir concurrencia
            chosen = available_devices[1]
            return chosen, f"[OK] Salida conectada automáticamente a cámara USB (Dispositivo {chosen})"
        elif len(available_devices) == 1:
            # Hay 1 sola cámara USB libre: Salida la aprovecha directamente
            chosen = available_devices[0]
            return chosen, f"[OK] Salida conectada automáticamente a cámara USB disponible (Dispositivo {chosen})"
        else:
            # No hay cámaras USB conectadas: fallback a IP
            msg = f"[INFO] No se detectó cámara USB conectada para Salida. Conectando a IP: {configured_source}"
            return configured_source, msg
    else:
        # Carril de entrada o patente general
        if len(available_devices) >= 1:
            chosen = available_devices[0]
            return chosen, f"[OK] Entrada conectada automáticamente a cámara USB (Dispositivo {chosen})"
        else:
            # No hay cámaras USB conectadas: fallback a IP
            msg = f"[INFO] No se detectó cámara USB conectada para Entrada. Conectando a IP: {configured_source}"
            return configured_source, msg
