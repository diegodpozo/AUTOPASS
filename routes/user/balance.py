import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from models.enums import AccessEventType
from core.database import get_db
from core.security import get_current_user
from core.logger import get_logger
from services.billing_service import BillingService

logger = get_logger("UserBalance")

router = APIRouter()

@router.get("/active-stays")
def get_user_active_stays(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """LISTA LAS ESTADIAS ACTUALES (DENTRO DEL PREDIO) PARA LOS VEHICULOS DEL USUARIO."""
    user_plates = [v.patente for v in current_user.vehicles]
    if not user_plates:
        return []

    from sqlalchemy import func
    # 1. Obtenemos la última entrada por cada patente en 1 sola consulta
    subq = db.query(
        models.AccessLog.patente_detectada,
        func.max(models.AccessLog.id).label("max_id")
    ).filter(
        models.AccessLog.patente_detectada.in_(user_plates),
        models.AccessLog.tipo_evento == AccessEventType.ENTRADA
    ).group_by(models.AccessLog.patente_detectada).subquery()

    ultimo_ingresos = db.query(models.AccessLog).join(
        subq, models.AccessLog.id == subq.c.max_id
    ).all()

    if not ultimo_ingresos:
        return []

    # 2. Obtenemos las salidas posteriores en 1 sola consulta agrupada
    ingreso_patentes = [e.patente_detectada for e in ultimo_ingresos]
    salidas = db.query(
        models.AccessLog.patente_detectada,
        models.AccessLog.fecha_hora
    ).filter(
        models.AccessLog.patente_detectada.in_(ingreso_patentes),
        models.AccessLog.tipo_evento == AccessEventType.SALIDA
    ).all()

    salida_map = {}
    for patente, fecha_salida in salidas:
        if patente not in salida_map or fecha_salida > salida_map[patente]:
            salida_map[patente] = fecha_salida

    res = []
    for ing in ultimo_ingresos:
        p = ing.patente_detectada
        f_salida = salida_map.get(p)
        if not f_salida or f_salida < ing.fecha_hora:
            deuda = 0.0 if ing.pago_confirmado else BillingService.calculate_debt(ing.fecha_hora, db)
            res.append({
                "id": ing.id,
                "patente": p,
                "ingreso": ing.fecha_hora,
                "deuda": deuda,
                "pago_confirmado": ing.pago_confirmado
            })
    return res

@router.get("/payment-history")
def get_user_payment_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """HISTORIAL CRONOLOGICO DE PAGOS REALIZADOS POR EL USUARIO."""
    user_plates = [v.patente for v in current_user.vehicles]
    return db.query(models.AccessLog).filter(
        models.AccessLog.patente_detectada.in_(user_plates),
        models.AccessLog.pago_confirmado == True,
        models.AccessLog.costo_estadia > 0
    ).order_by(models.AccessLog.id.desc()).all()

@router.get("/rates")
def get_current_rates(sucursal: str = None, db: Session = Depends(get_db)):
    """RETORNA LAS TARIFAS VIGENTES. SI HAY SEDE, PRIORIZA SUS PRECIOS Y COMPLETA CON GLOBALES."""
    keys = [
        "precio_30min", "precio_hora", "precio_dia", "precio_semana", "precio_quincena", "precio_mes",
        "precio_30min_moto", "precio_hora_moto", "precio_dia_moto", "precio_semana_moto", "precio_quincena_moto", "precio_mes_moto"
    ]

    global_settings = db.query(models.Settings).filter(
        models.Settings.clave.in_(keys),
        models.Settings.sucursal == None
    ).all()

    res = {s.clave.replace("precio_", ""): s.valor for s in global_settings}

    if sucursal:
        branch_settings = db.query(models.Settings).filter(
            models.Settings.clave.in_(keys),
            models.Settings.sucursal == sucursal
        ).all()
        for s in branch_settings:
            res[s.clave.replace("precio_", "")] = s.valor

    # FALLBACK DE SEGURIDAD PARA ASEGURAR QUE EXISTAN LAS CLAVES BASICAS
    defaults = {"30min": 750, "hora": 1500, "dia": 15000, "semana": 70000, "quincena": 120000, "mes": 200000}
    for k, v in defaults.items():
        if k not in res: res[k] = v
        
    return res

@router.post("/recharge-balance")
def recharge_balance(data: schemas.RechargeBalance, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """SIMULA LA CARGA DE SALDO EN LA CUENTA DEL USUARIO."""
    if data.monto <= 0: raise HTTPException(status_code=400, detail="Monto inválido")
    current_user.saldo += data.monto
    db.commit()

    try:
        from services.user_notification_service import UserNotificationService
        UserNotificationService.create_notification(
            db, current_user.id, "BALANCE_RECHARGED",
            "Carga de saldo exitosa",
            f"Se acreditó con éxito ${data.monto:,.2f} en tu cuenta. Saldo actual: ${current_user.saldo:,.2f}."
        )
    except Exception as e:
        logger.error(f"No se pudo notificar carga de saldo: {e}")

    return {"status": "ok", "message": f"Carga de ${data.monto:.2f} exitosa"}
