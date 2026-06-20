import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models
from core.database import get_db
from core.security import get_local_manager

router = APIRouter()

@router.get("/settings")
def get_admin_settings(db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """RETORNA LAS CONFIGURACIONES VIGENTES. LOS LOCALES SOLO VEN LAS DE SU SEDE."""
    q = db.query(models.Settings)
    if admin.rol != "admin":
        q = q.filter(models.Settings.sucursal == admin.sucursal)
    else:
        q = q.filter(models.Settings.sucursal == None)
        
    all_settings = q.all()
    config_dict = {s.clave: s.valor for s in all_settings}
    config_dict["sucursal_nombre"] = admin.sucursal

    sucursal = admin.sucursal if admin.rol != "admin" else None
    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
    if aforo:
        config_dict["capacidad_total"] = aforo.capacidad_total
        config_dict["capacidad_motos"] = aforo.capacidad_motos
        config_dict["ocupacion_actual"] = aforo.ocupacion_actual
        config_dict["ocupacion_motos"] = aforo.ocupacion_motos
    
    return config_dict

@router.post("/settings/prices")
def update_price(clave: str, valor: float, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ACTUALIZA O CREA UN VALOR DE CONFIGURACION PARA LA SEDE DEL ADMINISTRADOR."""
    sucursal = admin.sucursal if admin.rol != "admin" else None

    if clave in ["capacidad_total", "capacidad_motos"]:
        aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
        if aforo:
            if clave == "capacidad_total": aforo.capacidad_total = int(valor)
            else: aforo.capacidad_motos = int(valor)
            db.commit()
            return {"status": "ok"}
        else:
            db.add(models.ParkingAforo(
                capacidad_total=int(valor) if clave == "capacidad_total" else 20,
                capacidad_motos=int(valor) if clave == "capacidad_motos" else 10,
                ocupacion_actual=0,
                ocupacion_motos=0,
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
