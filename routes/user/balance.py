from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from core.database import get_db
from core.security import get_current_user
from core.logger import get_logger
from services.billing_service import BillingService
from repositories.access_log_repository import AccessRepository
from repositories.settings_repository import SettingsRepository

logger = get_logger("UserBalance")

router = APIRouter()

@router.get("/active-stays")
def get_user_active_stays(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """LISTA LAS ESTADIAS ACTUALES (DENTRO DEL PREDIO) PARA LOS VEHICULOS DEL USUARIO."""
    user_plates = [v.patente for v in current_user.vehicles]
    if not user_plates:
        return []

    # 1. Obtenemos la última entrada por cada patente en 1 sola consulta
    ultimo_ingresos = AccessRepository.get_last_entries_by_patentes(db, user_plates)

    if not ultimo_ingresos:
        return []

    # 2. Obtenemos las salidas posteriores en 1 sola consulta agrupada
    ingreso_patentes = [e.patente_detectada for e in ultimo_ingresos]
    salidas = AccessRepository.get_exit_times_by_patentes(db, ingreso_patentes)

    salida_map = {}
    for patente, fecha_salida in salidas:
        if patente not in salida_map or fecha_salida > salida_map[patente]:
            salida_map[patente] = fecha_salida

    res = []
    for ing in ultimo_ingresos:
        p = ing.patente_detectada
        f_salida = salida_map.get(p)
        if not f_salida or f_salida < ing.fecha_hora:
            if ing.pago_confirmado:
                deuda = 0.0
            else:
                deuda = BillingService.calculate_debt(ing.fecha_hora, db, sucursal=ing.sucursal, tipo_vehiculo=ing.tipo_vehiculo)
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
    return AccessRepository.get_paid_logs_by_patentes(db, user_plates)

@router.get("/rates")
def get_current_rates(sucursal: str = None, db: Session = Depends(get_db)):
    """RETORNA LAS TARIFAS CONFIGURADAS (NO INVENTA PRECIOS).
    Sin sucursal: tarifas globales. Con sucursal: SOLO las de esa sede (sin heredar globales).
    Si falta '30min' pero existe 'hora', la fracción vale la mitad de la hora."""
    keys = [
        "precio_30min", "precio_hora", "precio_dia", "precio_semana", "precio_quincena", "precio_mes",
        "precio_30min_moto", "precio_hora_moto", "precio_dia_moto", "precio_semana_moto", "precio_quincena_moto", "precio_mes_moto",
        "precio_30min_camioneta", "precio_hora_camioneta", "precio_dia_camioneta", "precio_semana_camioneta", "precio_quincena_camioneta", "precio_mes_camioneta"
    ]

    res = {
        s.clave.replace("precio_", ""): s.valor
        for s in SettingsRepository.get_all_by_sucursal(db, sucursal)
        if s.clave in keys
    }

    for familia in ("", "_moto", "_camioneta"):
        clave_hora = f"hora{familia}"
        clave_30 = f"30min{familia}"
        if clave_30 not in res and res.get(clave_hora):
            res[clave_30] = res[clave_hora] / 2

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
