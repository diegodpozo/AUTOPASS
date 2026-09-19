import os
import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import models
from core.database import get_db
from core.security import get_super_admin, get_operational_user
from core.config import settings
from services.time_service import TimeService
from routes.system.common import ALPR_HEARTBEATS, normalize_system_name
from models.enums import UserRole
from repositories.camera_repository import CameraRepository
from repositories.system_repository import SystemRepository

router = APIRouter()

@router.get("/health")
def get_health(db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    
    now = datetime.datetime.now()
    alpr_status = {}
    
    if staff.rol == UserRole.ADMIN:
        for gate, ts in ALPR_HEARTBEATS.items():
            alpr_status[gate] = "ONLINE" if (now - ts).total_seconds() < 90 else "OFFLINE"
    else:
        cameras = [c for c in CameraRepository.get_all(db) if c.sucursal == staff.sucursal]
        if not cameras:
            prefix = normalize_system_name(staff.sucursal)
            gates_to_check = [f"{prefix}_ENTRADA", f"{prefix}_SALIDA"]
            for gate in gates_to_check:
                status = "OFFLINE"
                if gate in ALPR_HEARTBEATS:
                    if (now - ALPR_HEARTBEATS[gate]).total_seconds() < 90:
                        status = "ONLINE"
                alpr_status[gate] = status
        else:
            for c in cameras:
                norm_suc = normalize_system_name(c.sucursal) if c.sucursal else "GLOBAL"
                proc_id = f"{norm_suc}_{c.tipo}_{c.id}".upper()
                status = "OFFLINE"
                if proc_id in ALPR_HEARTBEATS:
                    if (now - ALPR_HEARTBEATS[proc_id]).total_seconds() < 90:
                        status = "ONLINE"
                alpr_status[proc_id] = status
        
    return {"database": "ONLINE" if db_ok else "OFFLINE", "alpr": alpr_status, "api": "ONLINE"}

@router.post("/heartbeat")
def alpr_heartbeat(gate_id: str):
    gate_id = gate_id.strip().upper()
    ALPR_HEARTBEATS[gate_id] = datetime.datetime.now()
    return {"status": "ok"}

@router.post("/reset")
def reset_system(db: Session = Depends(get_db), admin: models.User = Depends(get_super_admin)):
    IMAGE_DIR = settings.IMAGE_DIR
    SystemRepository.reset_all_data(db)
    if os.path.exists(IMAGE_DIR):
        for f in os.listdir(IMAGE_DIR):
            try:
                os.unlink(os.path.join(IMAGE_DIR, f))
            except Exception:
                pass
    return {"status": "ok"}

@router.get("/virtual-time")
def get_virtual_time_public():
    return TimeService.get_info()
