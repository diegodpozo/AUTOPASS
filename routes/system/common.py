import os
import json
import subprocess
from typing import Dict, List
from fastapi import WebSocket
from pydantic import BaseModel
import models
from models.enums import UserRole
from core.logger import get_logger

logger = get_logger("SystemCommon")

CAMERA_PROCESSES: Dict[str, subprocess.Popen] = {}
ALPR_HEARTBEATS = {}

class CameraConfig(BaseModel):
    gate_id: str
    source: str

def stop_all_cameras():
    """Detiene todos los servicios ALPR activos al apagar el servidor."""
    for gate_id in list(CAMERA_PROCESSES.keys()):
        try:
            proc = CAMERA_PROCESSES[gate_id]
            if proc.poll() is None:
                if os.name == 'nt':
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    proc.terminate()
            logger.info(f"Cámara {gate_id} detenida correctamente.")
        except Exception:
            pass
    CAMERA_PROCESSES.clear()

from core.normalize import normalize_name as normalize_system_name


class ConnectionManager:
    """Gestión de WebSockets para espectadores de streaming de video por sucursal."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.last_frames: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, camera_id: str, user: models.User) -> bool:
        """Valida permisos por sucursal antes de conectar al espectador."""
        if user.rol != UserRole.ADMIN:
            branch_prefix = camera_id.split('_')[0] if '_' in camera_id else ""
            user_branch_norm = normalize_system_name(user.sucursal)
            
            if branch_prefix and user_branch_norm and branch_prefix != user_branch_norm:
                logger.warning(f"Bloqueado: Usuario de {user_branch_norm} intentó ver {branch_prefix}")
                await websocket.close(code=4003)
                return False

        await websocket.accept()
        if camera_id not in self.active_connections:
            self.active_connections[camera_id] = []
        self.active_connections[camera_id].append(websocket)
        
        if camera_id in self.last_frames:
            await websocket.send_text(self.last_frames[camera_id])
        return True

    def disconnect(self, websocket: WebSocket, camera_id: str):
        if camera_id in self.active_connections:
            try:
                self.active_connections[camera_id].remove(websocket)
            except ValueError:
                pass

    async def broadcast_frame(self, camera_id: str, frame_base64: str):
        self.last_frames[camera_id] = frame_base64
        if camera_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[camera_id]:
                try:
                    await connection.send_text(frame_base64)
                except Exception:
                    disconnected.append(connection)
            
            for conn in disconnected:
                self.disconnect(conn, camera_id)

    async def broadcast_console(self, camera_id: str, line: str):
        """ENVIA UNA LINEA DE CONSOLA DEL SUBPROCESO ALPR A LOS ESPECTADORES DE ESA CAMARA.
        Se envia como JSON con prefijo CONSOLE para diferenciarla del frame (base64)."""
        if camera_id in self.active_connections:
            payload = {"__console__": True, "gate": camera_id, "line": line}
            disconnected = []
            for connection in self.active_connections[camera_id]:
                try:
                    await connection.send_text(json.dumps(payload))
                except Exception:
                    disconnected.append(connection)
            for conn in disconnected:
                self.disconnect(conn, camera_id)

manager = ConnectionManager()
