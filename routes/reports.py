from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import models
from core.database import get_db
from core.security import get_local_manager, get_operational_user
from services.report_service import ReportService

router = APIRouter(prefix="/v1/reports", tags=["Reports & Analytics"])

@router.get("/financial-summary")
def get_financial_summary(
    period: str = "total",
    start: str = None,
    end: str = None,
    vehicle_type: str = "all",
    payment_method: str = "all",
    db: Session = Depends(get_db),
    user: models.User = Depends(get_operational_user)
):
    """Calcula el resumen de recaudación unificado delegando en ReportService."""
    return ReportService.get_financial_summary(
        db=db,
        user=user,
        period=period,
        start=start,
        end=end,
        vehicle_type=vehicle_type,
        payment_method=payment_method
    )

@router.get("/payment-history")
def get_payment_history(
    period: str = "total",
    start: str = None,
    end: str = None,
    vehicle_type: str = "all",
    payment_method: str = "all",
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_local_manager)
):
    """Lista el historial de transacciones delegando en ReportService."""
    return ReportService.get_payment_history(
        db=db,
        admin=admin,
        period=period,
        start=start,
        end=end,
        vehicle_type=vehicle_type,
        payment_method=payment_method,
        page=page,
        limit=limit
    )

@router.get("/access")
def get_reports_access(
    patente: str = None,
    limit: int = Query(300, ge=1, le=1000),
    db: Session = Depends(get_db),
    staff: models.User = Depends(get_operational_user)
):
    """Consulta el historial de eventos ALPR delegando en ReportService."""
    return ReportService.get_access_logs(db=db, staff=staff, patente=patente, limit=limit)

@router.get("/ocr-stats")
def get_ocr_stats(
    limit: int = 100,
    db: Session = Depends(get_db),
    staff: models.User = Depends(get_operational_user)
):
    """Estadísticas de tiempos de procesamiento OCR."""
    return ReportService.get_ocr_stats(db=db, staff=staff, limit=limit)

@router.get("/metrics/access-activity")
def get_metrics_access_activity(
    desde: str = None,
    hasta: str = None,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_local_manager)
):
    """Serie temporal horaria de accesos (ENTRADA/SALIDA) con filtro opcional de rango (desde/hasta)."""
    return ReportService.get_access_activity(db=db, admin=admin, desde=desde, hasta=hasta)

@router.get("/ocr-activity")
def get_ocr_activity(
    db: Session = Depends(get_db),
    staff: models.User = Depends(get_operational_user)
):
    """Serie cronológica completa de tiempos OCR para el gráfico móvil."""
    return ReportService.get_ocr_activity(db=db, staff=staff)
