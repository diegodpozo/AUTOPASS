import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
from models.enums import UserRole
from core.database import get_db
from core.limiter import admin_rate_limit
from core.security import get_local_manager
from repositories.settings_repository import SettingsRepository
from repositories.branch_repository import BranchRepository

router = APIRouter()


def _aforo_vigente(db: Session, sucursal, organization_id):
    """AFORO DE LA SEDE. SI ES LA FILA GLOBAL (sucursal=None), LA ACOTA A LA ORGANIZACION
    DEL ADMIN PARA NO LEER LA DE OTRA EMPRESA. Tolerante con filas sin organizacion."""
    aforo = BranchRepository.get_aforo_by_sucursal(db, sucursal)
    if aforo is not None and organization_id is not None and getattr(aforo, "organization_id", None) not in (None, organization_id):
        return None
    return aforo

# CLAVES PERMITIDAS PARA update_price: tarifas (por tipo de vehiculo) y
# capacidades de aforo. Evita inyectar claves arbitrarias en la tabla Settings.
ALLOWED_SETTINGS_KEYS = {
    "precio_30min", "precio_hora", "precio_dia", "precio_semana", "precio_quincena", "precio_mes",
    "precio_30min_moto", "precio_hora_moto", "precio_dia_moto", "precio_semana_moto", "precio_quincena_moto", "precio_mes_moto",
    "precio_30min_camioneta", "precio_hora_camioneta", "precio_dia_camioneta", "precio_semana_camioneta", "precio_quincena_camioneta", "precio_mes_camioneta",
    "capacidad_total", "capacidad_motos", "capacidad_camionetas",
    "capacidad_reservas", "capacidad_reservas_autos", "capacidad_reservas_motos", "capacidad_reservas_camionetas",
}

@router.get("/settings")
def get_admin_settings(db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """RETORNA LAS CONFIGURACIONES VIGENTES DE LA ORGANIZACION. LOS LOCALES SOLO VEN LAS DE SU SEDE."""
    org_id = getattr(admin, "organization_id", None)
    q = SettingsRepository.get_all_by_sucursal(
        db, sucursal=admin.sucursal if admin.rol != UserRole.ADMIN else None, organization_id=org_id
    )
    all_settings = q
    config_dict = {s.clave: s.valor for s in all_settings}
    config_dict["sucursal_nombre"] = admin.sucursal

    sucursal = admin.sucursal if admin.rol != UserRole.ADMIN else None
    aforo = _aforo_vigente(db, sucursal, org_id)
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

@router.post("/settings/prices", dependencies=[Depends(admin_rate_limit)])
def update_price(clave: str, valor: float, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ACTUALIZA O CREA UN VALOR DE CONFIGURACION PARA LA ORGANIZACION DEL ADMINISTRADOR."""
    org_id = getattr(admin, "organization_id", None)
    if valor < 0:
        raise HTTPException(status_code=400, detail="El valor no puede ser negativo")
    if clave not in ALLOWED_SETTINGS_KEYS:
        raise HTTPException(status_code=400, detail="Clave de configuración no permitida")
    sucursal = admin.sucursal if admin.rol != UserRole.ADMIN else None

    if clave in ["capacidad_total", "capacidad_motos", "capacidad_camionetas", "capacidad_reservas", "capacidad_reservas_autos", "capacidad_reservas_motos", "capacidad_reservas_camionetas"]:
        aforo = _aforo_vigente(db, sucursal, org_id)
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
                sucursal=sucursal,
                organization_id=org_id
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

    setting = SettingsRepository.get_by_clave_and_sucursal(db, clave, sucursal=sucursal, organization_id=org_id)
    
    if setting: 
        setting.valor = valor
    else: 
        db.add(models.Settings(clave=clave, valor=valor, sucursal=sucursal, organization_id=org_id))
    
    db.commit()
    from core.cache import ttl_cache
    ttl_cache.invalidate("rate_")
    return {"status": "ok", "message": f"Precio {clave} actualizado para {sucursal or 'Global'}"}
