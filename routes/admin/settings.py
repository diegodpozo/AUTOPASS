import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models
from core.database import get_db
from core.security import get_local_manager

router = APIRouter()

@router.get("/settings")
def get_admin_settings(db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """Retorna las configuraciones vigentes. Los locales solo ven las de su sede."""
    q = db.query(models.Settings)
    if admin.rol != "admin":
        q = q.filter(models.Settings.sucursal == admin.sucursal)
    else:
        q = q.filter(models.Settings.sucursal == None)
        
    all_settings = q.all()
    config_dict = {s.clave: s.valor for s in all_settings}

    sucursal = admin.sucursal if admin.rol != "admin" else None
    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
    if aforo:
        config_dict["capacidad_total"] = aforo.capacidad_total
    
    return config_dict

@router.post("/settings/prices")
def update_price(clave: str, valor: float, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """Actualiza o crea un valor de configuración para la sede del administrador."""
    sucursal = admin.sucursal if admin.rol != "admin" else None

    if clave == "capacidad_total":
        aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
        if aforo:
            aforo.capacidad_total = int(valor)
            db.commit()
            return {"status": "ok"}
        else:
            db.add(models.ParkingAforo(
                capacidad_total=int(valor), 
                ocupacion_actual=0, 
                ultima_actualizacion=datetime.datetime.now().isoformat(),
                sucursal=sucursal
            ))
            db.commit()
            return {"status": "ok"}

    setting = db.query(models.Settings).filter(
        models.Settings.clave == clave, 
        models.Settings.sucursal == sucursal
    ).first()
    
    if setting: 
        setting.valor = valor
    else: 
        db.add(models.Settings(clave=clave, valor=valor, sucursal=sucursal))
    
    db.commit()
    return {"status": "ok", "message": f"Precio {clave} actualizado para {sucursal or 'Global'}"}
