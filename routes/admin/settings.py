import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models
from models.enums import UserRole
from core.database import get_db
from core.security import get_local_manager

router = APIRouter()

@router.get("/settings")
def get_admin_settings(db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """RETORNA LAS CONFIGURACIONES VIGENTES. LOS LOCALES SOLO VEN LAS DE SU SEDE."""
    q = db.query(models.Settings)
    if admin.rol != UserRole.ADMIN:
        q = q.filter(models.Settings.sucursal == admin.sucursal)
    else:
        q = q.filter(models.Settings.sucursal == None)
        
    all_settings = q.all()
    config_dict = {s.clave: s.valor for s in all_settings}
    config_dict["sucursal_nombre"] = admin.sucursal

    sucursal = admin.sucursal if admin.rol != UserRole.ADMIN else None
    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
    if aforo:
        config_dict["capacidad_total"] = aforo.capacidad_total
        config_dict["capacidad_motos"] = aforo.capacidad_motos
        config_dict["capacidad_camionetas"] = getattr(aforo, "capacidad_camionetas", 5)
        config_dict["capacidad_reservas"] = getattr(aforo, "capacidad_reservas", 0)
        config_dict["capacidad_reservas_autos"] = getattr(aforo, "capacidad_reservas_autos", 0)
        config_dict["capacidad_reservas_motos"] = getattr(aforo, "capacidad_reservas_motos", 0)
        config_dict["capacidad_reservas_camionetas"] = getattr(aforo, "capacidad_reservas_camionetas", 0)
        config_dict["ocupacion_actual"] = aforo.ocupacion_actual
        config_dict["ocupacion_motos"] = aforo.ocupacion_motos
        config_dict["ocupacion_camionetas"] = getattr(aforo, "ocupacion_camionetas", 0)
        config_dict["ocupacion_reservas"] = getattr(aforo, "ocupacion_reservas", 0)
        config_dict["ocupacion_reservas_autos"] = getattr(aforo, "ocupacion_reservas_autos", 0)
        config_dict["ocupacion_reservas_motos"] = getattr(aforo, "ocupacion_reservas_motos", 0)
        config_dict["ocupacion_reservas_camionetas"] = getattr(aforo, "ocupacion_reservas_camionetas", 0)
    
    return config_dict

@router.post("/settings/prices")
def update_price(clave: str, valor: float, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ACTUALIZA O CREA UN VALOR DE CONFIGURACION PARA LA SEDE DEL ADMINISTRADOR."""
    sucursal = admin.sucursal if admin.rol != UserRole.ADMIN else None

    if clave in ["capacidad_total", "capacidad_motos", "capacidad_camionetas", "capacidad_reservas", "capacidad_reservas_autos", "capacidad_reservas_motos", "capacidad_reservas_camionetas"]:
        aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == sucursal).first()
        if not aforo:
            aforo = models.ParkingAforo(
                capacidad_total=20,
                capacidad_motos=10,
                capacidad_camionetas=5,
                capacidad_reservas=0,
                capacidad_reservas_autos=0,
                capacidad_reservas_motos=0,
                capacidad_reservas_camionetas=0,
                ocupacion_actual=0,
                ocupacion_motos=0,
                ocupacion_camionetas=0,
                ocupacion_reservas=0,
                ocupacion_reservas_autos=0,
                ocupacion_reservas_motos=0,
                ocupacion_reservas_camionetas=0,
                ultima_actualizacion=datetime.datetime.now().isoformat(),
                sucursal=sucursal
            )
            db.add(aforo)

        val_int = int(valor)
        if clave == "capacidad_total": aforo.capacidad_total = val_int
        elif clave == "capacidad_motos": aforo.capacidad_motos = val_int
        elif clave == "capacidad_camionetas": aforo.capacidad_camionetas = val_int
        elif clave == "capacidad_reservas": aforo.capacidad_reservas = val_int
        elif clave == "capacidad_reservas_autos": aforo.capacidad_reservas_autos = val_int
        elif clave == "capacidad_reservas_motos": aforo.capacidad_reservas_motos = val_int
        elif clave == "capacidad_reservas_camionetas": aforo.capacidad_reservas_camionetas = val_int

        if clave in ["capacidad_reservas_autos", "capacidad_reservas_motos", "capacidad_reservas_camionetas"]:
            aforo.capacidad_reservas = (aforo.capacidad_reservas_autos or 0) + (aforo.capacidad_reservas_motos or 0) + (aforo.capacidad_reservas_camionetas or 0)

        db.commit()
        try:
            from services.notification_service import NotificationService
            NotificationService.notify_occupancy_change(db, sucursal)
        except Exception:
            pass
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
    from core.cache import ttl_cache
    ttl_cache.invalidate("rate_")
    return {"status": "ok", "message": f"Precio {clave} actualizado para {sucursal or 'Global'}"}
