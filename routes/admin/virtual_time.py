import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.database import get_db, SessionLocal
from core.logger import get_logger
from services.time_service import TimeService
from services.worker_service import WorkerService
from services.reservation_service import ReservationService
from core.security import get_local_manager

logger = get_logger("VirtualTime")

router = APIRouter(prefix="/virtual-time", tags=["Virtual Time"])

class TimeAdjustmentRequest(BaseModel):
    minutes: int = 0
    hours: int = 0
    days: int = 0

class SetOffsetRequest(BaseModel):
    offset_seconds: int

class SetTargetRequest(BaseModel):
    target_datetime: str  # ISO string ej: "2026-10-15T14:30:00"

def _run_all_checks():
    """EJECUTA TODOS LOS WORKERS INMEDIATAMENTE CONTRA LA HORA VIRTUAL."""
    try:
        db = SessionLocal()
        WorkerService._process_reminders(db)
        WorkerService._process_started_reservations(db)
        WorkerService._process_auto_cancellations(db)
        ReservationService.cleanup_overdue_reservations(db)
        ReservationService.auto_finalize_all_reservations(db)
        db.close()
    except Exception as e:
        logger.error(f"Error en chequeo inmediato de virtual-time: {e}")

@router.get("")
@router.get("/status")
def get_virtual_time(user=Depends(get_local_manager)):
    return TimeService.get_info()

@router.post("/advance")
def advance_virtual_time(req: TimeAdjustmentRequest, user=Depends(get_local_manager)):
    if req.days or req.hours or req.minutes:
        TimeService.advance(days=req.days, hours=req.hours, minutes=req.minutes)
    _run_all_checks()
    return TimeService.get_info()

@router.post("/rewind")
def rewind_virtual_time(req: TimeAdjustmentRequest, user=Depends(get_local_manager)):
    """RETRASAR EL RELOJ VIRTUAL DEL SISTEMA."""
    if req.days or req.hours or req.minutes:
        TimeService.rewind(days=req.days, hours=req.hours, minutes=req.minutes)
    _run_all_checks()
    return TimeService.get_info()

@router.post("/set-target")
def set_target_virtual_time(req: SetTargetRequest, user=Depends(get_local_manager)):
    """FIJAR LA FECHA Y HORA VIRTUAL A UN VALOR ESPECIFICO (EJ: '2026-10-15T14:30:00')."""
    try:
        target_dt = datetime.datetime.fromisoformat(req.target_datetime)
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de fecha/hora inválido. Usá formato ISO (ej: 2026-10-15T14:30:00).")
    
    TimeService.set_target_datetime(target_dt)
    _run_all_checks()
    return TimeService.get_info()

@router.post("/set")
def set_virtual_time(req: SetOffsetRequest, user=Depends(get_local_manager)):
    TimeService.set_offset(req.offset_seconds)
    _run_all_checks()
    return TimeService.get_info()

@router.post("/reset")
def reset_virtual_time(user=Depends(get_local_manager)):
    TimeService.reset()
    _run_all_checks()
    return TimeService.get_info()
