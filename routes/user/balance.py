import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from core.database import get_db
from core.security import get_current_user
from services.billing_service import BillingService

router = APIRouter()

@router.get("/active-stays")
def get_user_active_stays(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Lista las estadías actuales (dentro del predio) para los vehículos del usuario."""
    user_plates = [v.patente for v in current_user.vehicles]
    res = []
    for p in user_plates:
        ultimo_ingreso = db.query(models.AccessLog).filter(models.AccessLog.patente_detectada == p, models.AccessLog.tipo_evento == "ENTRADA").order_by(models.AccessLog.id.desc()).first()
        if ultimo_ingreso:
            tiene_salida = db.query(models.AccessLog).filter(models.AccessLog.patente_detectada == p, models.AccessLog.tipo_evento == "SALIDA", models.AccessLog.fecha_hora > ultimo_ingreso.fecha_hora).first()
            if not tiene_salida:
                deuda = 0.0 if ultimo_ingreso.pago_confirmado else BillingService.calculate_debt(ultimo_ingreso.fecha_hora, db)
                res.append({"patente": p, "ingreso": ultimo_ingreso.fecha_hora, "deuda": deuda, "pago_confirmado": ultimo_ingreso.pago_confirmado})
    return res

@router.get("/payment-history")
def get_user_payment_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Historial cronológico de pagos realizados por el usuario."""
    user_plates = [v.patente for v in current_user.vehicles]
    return db.query(models.AccessLog).filter(
        models.AccessLog.patente_detectada.in_(user_plates),
        models.AccessLog.pago_confirmado == True,
        models.AccessLog.costo_estadia > 0
    ).order_by(models.AccessLog.id.desc()).all()

@router.get("/rates")
def get_current_rates(sucursal: str = None, db: Session = Depends(get_db)):
    """Retorna las tarifas vigentes. Si hay sede, prioriza sus precios y completa con globales."""
    keys = ["precio_hora", "precio_dia", "precio_semana", "precio_quincena", "precio_mes"]
    
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
            
    defaults = {"hora": 1500, "dia": 15000, "semana": 70000, "quincena": 120000, "mes": 200000}
    for k, v in defaults.items():
        if k not in res: res[k] = v
        
    return res

@router.post("/recharge-balance")
def recharge_balance(data: schemas.RechargeBalance, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Simula la carga de saldo en la cuenta del usuario."""
    if data.monto <= 0: raise HTTPException(status_code=400, detail="Monto inválido")
    current_user.saldo += data.monto
    db.commit()
    return {"status": "ok", "message": f"Carga de ${data.monto:.2f} exitosa"}
