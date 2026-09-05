import datetime 
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
from core.database import get_db
from core.security import get_operational_user
from core.logger import get_logger
from services.user_notification_service import UserNotificationService

logger = get_logger("AdminOps")

router = APIRouter()

@router.post("/open-barrier")
def open_barrier(gate_id: str, command: str = "OPEN", db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user), request: Request = None):
    """ENVIA UN COMANDO DE APERTURA O CIERRE DE BARRERA VIA MQTT Y SERIAL (ARDUINO)."""
    from services.hardware_service import HardwareService
    res = HardwareService.trigger_barrier(
        gate_id=gate_id,
        command=command,
        method="MANUAL_OP",
        details={"staff_id": staff.id, "sucursal": staff.sucursal},
        request=request
    )
    return {"status": "ok", "message": f"Comando {command} enviado a barrera {gate_id} ({staff.sucursal or 'Global'})", "data": res}

@router.post("/manual-entry")
def manual_entry(plate: str, tipo_vehiculo: str = "Auto", floor_id: int = None, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user), request: Request = None):
    """REGISTRA UN INGRESO FORZADO AL PREDIO DE LA SEDE."""
    from services.access_service import AccessService
    return AccessService.manual_entry(db, plate=plate, sucursal=staff.sucursal, tipo_vehiculo=tipo_vehiculo, floor_id=floor_id, request=request)

@router.post("/manual-exit")
def manual_exit(plate: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user), request: Request = None):
    """REGISTRA UNA SALIDA MANUAL DE LA SEDE."""
    from services.access_service import AccessService
    return AccessService.manual_exit(db, plate=plate, sucursal=staff.sucursal, request=request)

@router.post("/cancel-stay")
def cancel_stay(plate: str, db: Session = Depends(get_db), staff: models.User = Depends(get_operational_user)):
    """CANCELA UNA ESTADIA ACTUAL. SI ESTA DENTRO DE LOS 10 MIN DE CORTESIA, NO COBRA."""
    from services.access_service import AccessService
    return AccessService.cancel_stay(db, plate=plate, sucursal=staff.sucursal)

