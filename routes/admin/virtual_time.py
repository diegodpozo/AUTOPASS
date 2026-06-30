from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.database import get_db, SessionLocal
from services.time_service import TimeService
from services.worker_service import WorkerService
from services.reservation_service import ReservationService
from core.security import get_current_user

router = APIRouter(prefix="/virtual-time", tags=["Virtual Time"])

class AdvanceRequest(BaseModel):
    minutes: int = 0
    hours: int = 0
    days: int = 0

class SetOffsetRequest(BaseModel):
    offset_seconds: int

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
        print(f"[VIRTUAL TIME] Error en chequeo inmediato: {e}")

@router.get("")
@router.get("/status")
def get_virtual_time(user=Depends(get_current_user)):
    return TimeService.get_info()

@router.post("/advance")
def advance_virtual_time(req: AdvanceRequest, user=Depends(get_current_user)):
    if req.days:
        TimeService.advance(days=req.days)
    elif req.hours:
        TimeService.advance(hours=req.hours)
    elif req.minutes:
        TimeService.advance(minutes=req.minutes)
    _run_all_checks()
    return TimeService.get_info()

@router.post("/set")
def set_virtual_time(req: SetOffsetRequest, user=Depends(get_current_user)):
    TimeService.set_offset(req.offset_seconds)
    _run_all_checks()
    return TimeService.get_info()

@router.post("/reset")
def reset_virtual_time(user=Depends(get_current_user)):
    TimeService.reset()
    _run_all_checks()
    return TimeService.get_info()
