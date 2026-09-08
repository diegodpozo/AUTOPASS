import os
import shutil
import subprocess
import uuid
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from core.database import get_db
from core.normalize import normalize_name as normalize_system_name
from core.security import get_super_admin, get_local_manager
from services.branch_service import BranchService

router = APIRouter()

@router.get("/branches", response_model=List[schemas.BranchResponse])
def list_branches(db: Session = Depends(get_db)):
    """RETORNA LA LISTA DE TODAS LAS SUCURSALES CON RESUMEN DE CAPACIDAD Y OCUPACION."""
    return BranchService.list_branches_with_summary(db)

# --- GESTION DE PISOS ---

@router.post("/{branch_id}/floors", response_model=schemas.FloorResponse)
def add_floor(branch_id: int, data: schemas.FloorCreate, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """AGREGA UN NUEVO PISO A LA SUCURSAL."""
    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    
    cap_res_autos = getattr(data, 'capacidad_reservas_autos', 0) or 0
    cap_res_motos = getattr(data, 'capacidad_reservas_motos', 0) or 0
    cap_res_camionetas = getattr(data, 'capacidad_reservas_camionetas', 0) or 0
    cap_res_total = getattr(data, 'capacidad_reservas', 0) or (cap_res_autos + cap_res_motos + cap_res_camionetas)

    new_floor = models.ParkingFloor(
        branch_id=branch_id,
        nombre=data.nombre,
        capacidad_total=data.capacidad_total,
        capacidad_motos=data.capacidad_motos,
        capacidad_camionetas=data.capacidad_camionetas,
        capacidad_reservas=cap_res_total,
        capacidad_reservas_autos=cap_res_autos,
        capacidad_reservas_motos=cap_res_motos,
        capacidad_reservas_camionetas=cap_res_camionetas
    )
    db.add(new_floor)
    db.commit()
    db.refresh(new_floor)
    try:
        from services.notification_service import NotificationService
        NotificationService.notify_occupancy_change(db, branch.nombre)
    except Exception:
        pass
    return new_floor

@router.delete("/floors/{floor_id}")
def delete_floor(floor_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ELIMINA UN PISO DE LA SUCURSAL TRAS VALIDAR QUE NO HAYA VEHICULOS ESTACIONADOS."""
    floor = db.query(models.ParkingFloor).filter(models.ParkingFloor.id == floor_id).first()
    if not floor: raise HTTPException(status_code=404, detail="Piso no encontrado")
    
    if (floor.ocupacion_actual or 0) > 0 or (floor.ocupacion_motos or 0) > 0 or (floor.ocupacion_camionetas or 0) > 0 or (getattr(floor, 'ocupacion_reservas', 0) or 0) > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar un piso que posee vehículos actualmente estacionados en él.")

    branch_id = floor.branch_id
    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.id == branch_id).first()

    db.delete(floor)
    db.commit()
    if branch:
        try:
            from services.notification_service import NotificationService
            NotificationService.notify_occupancy_change(db, branch.nombre)
        except Exception:
            pass
    return {"status": "ok"}

@router.patch("/floors/{floor_id}", response_model=schemas.FloorResponse)
def update_floor_capacity(
    floor_id: int, 
    cap_autos: int, 
    cap_motos: int, 
    cap_camionetas: int = 5, 
    cap_reservas: int = 0, 
    cap_reservas_autos: Optional[int] = None,
    cap_reservas_motos: Optional[int] = None,
    cap_reservas_camionetas: Optional[int] = None,
    db: Session = Depends(get_db), 
    admin: models.User = Depends(get_local_manager)
):
    """ACTUALIZA LA CAPACIDAD DE UN PISO VALIDANDO QUE SEA MAYOR O IGUAL A LA OCUPACION ACTUAL."""
    floor = db.query(models.ParkingFloor).filter(models.ParkingFloor.id == floor_id).first()
    if not floor: raise HTTPException(status_code=404, detail="Piso no encontrado")
    
    if cap_autos < (floor.ocupacion_actual or 0):
        raise HTTPException(status_code=400, detail=f"La capacidad de autos ({cap_autos}) no puede ser menor a la ocupación actual ({floor.ocupacion_actual}).")
    if cap_motos < (floor.ocupacion_motos or 0):
        raise HTTPException(status_code=400, detail=f"La capacidad de motos ({cap_motos}) no puede ser menor a la ocupación actual ({floor.ocupacion_motos}).")
    if cap_camionetas < (floor.ocupacion_camionetas or 0):
        raise HTTPException(status_code=400, detail=f"La capacidad de camionetas ({cap_camionetas}) no puede ser menor a la ocupación actual ({floor.ocupacion_camionetas}).")

    if cap_reservas_autos is not None and cap_reservas_autos < (getattr(floor, 'ocupacion_reservas_autos', 0) or 0):
        raise HTTPException(status_code=400, detail=f"La capacidad de reservas autos ({cap_reservas_autos}) no puede ser menor a la ocupación actual ({floor.ocupacion_reservas_autos}).")
    if cap_reservas_motos is not None and cap_reservas_motos < (getattr(floor, 'ocupacion_reservas_motos', 0) or 0):
        raise HTTPException(status_code=400, detail=f"La capacidad de reservas motos ({cap_reservas_motos}) no puede ser menor a la ocupación actual ({floor.ocupacion_reservas_motos}).")
    if cap_reservas_camionetas is not None and cap_reservas_camionetas < (getattr(floor, 'ocupacion_reservas_camionetas', 0) or 0):
        raise HTTPException(status_code=400, detail=f"La capacidad de reservas camionetas ({cap_reservas_camionetas}) no puede ser menor a la ocupación actual ({floor.ocupacion_reservas_camionetas}).")

    floor.capacidad_total = cap_autos
    floor.capacidad_motos = cap_motos
    floor.capacidad_camionetas = cap_camionetas

    if cap_reservas_autos is not None:
        floor.capacidad_reservas_autos = cap_reservas_autos
    if cap_reservas_motos is not None:
        floor.capacidad_reservas_motos = cap_reservas_motos
    if cap_reservas_camionetas is not None:
        floor.capacidad_reservas_camionetas = cap_reservas_camionetas

    if cap_reservas_autos is not None or cap_reservas_motos is not None or cap_reservas_camionetas is not None:
        floor.capacidad_reservas = (floor.capacidad_reservas_autos or 0) + (floor.capacidad_reservas_motos or 0) + (floor.capacidad_reservas_camionetas or 0)
    else:
        floor.capacidad_reservas = cap_reservas

    db.commit()
    db.refresh(floor)
    if floor.branch:
        try:
            from services.notification_service import NotificationService
            NotificationService.notify_occupancy_change(db, floor.branch.nombre)
        except Exception:
            pass
    return floor

@router.post("/branches")
async def create_branch(
    nombre: str = Form(...),
    direccion: str = Form(...),
    telefono: str = Form(...),
    horario: str = Form(...),
    is_24h: bool = Form(False),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    logo_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db), 
    admin: models.User = Depends(get_super_admin)
):
    nombre_clean = nombre.strip()
    existing = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == nombre_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="La sucursal ya existe")
    
    logo_url = "/static/images/logo.png"
    if logo_file:
        file_ext = logo_file.filename.split(".")[-1]
        file_name = f"branch_{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join("static", "uploads", "branches", file_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(logo_file.file, buffer)
        logo_url = f"/static/uploads/branches/{file_name}"

    new_branch = models.ParkingBranch(
        nombre=nombre,
        direccion=direccion,
        telefono=telefono,
        horario=horario,
        is_24h=is_24h,
        logo_url=logo_url,
        activa=True,
        latitude=latitude,
        longitude=longitude
    )
    db.add(new_branch)
    db.commit()
    return {"status": "ok", "message": f"Sucursal '{new_branch.nombre}' creada"}

@router.delete("/branches/{branch_id}")
def delete_branch(branch_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_super_admin)):
    """ELIMINA UNA SUCURSAL TRAS VALIDAR QUE NO TENGA VEHICULOS EN SU INTERIOR NI RESERVAS ACTIVAS."""
def _check_physical_occupancy(db: Session, branch: models.ParkingBranch) -> bool:
    """RETORNA TRUE SI HAY VEHICULOS ESTACIONADOS FISICAMENTE EN LA SUCURSAL."""
    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == branch.nombre).first()
    if aforo and ((aforo.ocupacion_actual or 0) > 0 or (aforo.ocupacion_motos or 0) > 0 or (aforo.ocupacion_camionetas or 0) > 0 or (getattr(aforo, 'ocupacion_reservas', 0) or 0) > 0):
        return True
    if branch.floors:
        total_occ = sum((f.ocupacion_actual or 0) + (f.ocupacion_motos or 0) + (f.ocupacion_camionetas or 0) + (getattr(f, 'ocupacion_reservas', 0) or 0) for f in branch.floors)
        if total_occ > 0:
            return True
    return False


@router.delete("/branches/{branch_id}")
def delete_branch(branch_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_super_admin)):
    """ELIMINA UNA SUCURSAL TRAS VALIDAR QUE NO TENGA VEHICULOS EN SU INTERIOR NI RESERVAS ACTIVAS."""
    import datetime

    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    
    # 1. VALIDAR OCUPACION FISICA
    if _check_physical_occupancy(db, branch):
        raise HTTPException(status_code=400, detail="No se puede eliminar una sucursal con vehículos físicamente en su interior.")

    # 2. VALIDAR RESERVAS ACTIVAS O PENDIENTES
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    active_res = db.query(models.Reservation).filter(
        models.Reservation.sucursal_nombre == branch.nombre,
        models.Reservation.estado_reserva.in_(["Pendiente", "Activa"]),
        models.Reservation.fecha_fin >= now_str
    ).first()
    if active_res:
        raise HTTPException(status_code=400, detail="No se puede eliminar una sucursal con reservas activas o pendientes.")

    # 3. ELIMINAR LOGO ASOCIADO SI NO ES EL LOGO POR DEFECTO
    if branch.logo_url and branch.logo_url != '/static/images/logo.png':
        old_path = branch.logo_url.lstrip('/')
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass

    db.delete(branch)
    db.commit()
    return {"status": "ok", "message": "Sucursal eliminada"}

@router.patch("/branches/{branch_id}")
async def update_branch(
    branch_id: int,
    nombre: str = Form(...),
    direccion: str = Form(...),
    telefono: str = Form(...),
    horario: str = Form(...),
    is_24h: bool = Form(False),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    logo_file: Optional[UploadFile] = File(None),
    logo_clear: Optional[bool] = Form(False),
    db: Session = Depends(get_db), 
    admin: models.User = Depends(get_super_admin)
):
    """ACTUALIZA LA INFORMACION DE UNA SUCURSAL CON SOPORTE PARA NUEVO LOGO."""
    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    
    new_nombre = nombre.strip()
    old_nombre = branch.nombre

    if old_nombre != new_nombre:
        existing = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == new_nombre, models.ParkingBranch.id != branch_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ya existe una sucursal con ese nombre")

        old_prefix = normalize_system_name(old_nombre)
        new_prefix = normalize_system_name(new_nombre)

        # Propagar el cambio de nombre a tablas dependientes
        db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == old_nombre).update({models.ParkingAforo.sucursal: new_nombre})
        db.query(models.Settings).filter(models.Settings.sucursal == old_nombre).update({models.Settings.sucursal: new_nombre})
        db.query(models.User).filter(models.User.sucursal == old_nombre).update({models.User.sucursal: new_nombre})
        db.query(models.Reservation).filter(models.Reservation.sucursal_nombre == old_nombre).update({models.Reservation.sucursal_nombre: new_nombre})
        db.query(models.AccessLog).filter(models.AccessLog.sucursal == old_nombre).update({models.AccessLog.sucursal: new_nombre})
        db.query(models.SupportTicket).filter(models.SupportTicket.sucursal == old_nombre).update({models.SupportTicket.sucursal: new_nombre})
        db.query(models.ParkingCamera).filter(models.ParkingCamera.sucursal == old_nombre).update({models.ParkingCamera.sucursal: new_nombre})
        db.query(models.Promotion).filter(models.Promotion.sucursal == old_nombre).update({models.Promotion.sucursal: new_nombre})

        # El gate_id/WS de cada camara se compone con el prefijo normalizado del nombre
        # de sucursal. Si el prefijo cambia, remapear las claves legacy CAMERA_SOURCE_* y
        # detener los subprocesos ALPR del prefijo viejo para que espectador y proceso
        # converjan al mismo canal (si no, la camara queda en negro).
        if old_prefix and old_prefix != new_prefix:
            source_rows = db.query(models.Settings).filter(models.Settings.clave.like(f"CAMERA_SOURCE_{old_prefix}_%")).all()
            for row in source_rows:
                row.clave = row.clave.replace(f"CAMERA_SOURCE_{old_prefix}", f"CAMERA_SOURCE_{new_prefix}", 1)

            from routes.system.common import CAMERA_PROCESSES
            stale_gates = [g for g in list(CAMERA_PROCESSES.keys()) if g.startswith(f"{old_prefix}_")]
            for gate_id in stale_gates:
                proc = CAMERA_PROCESSES.get(gate_id)
                if proc and proc.poll() is None:
                    try:
                        if os.name == 'nt':
                            subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        else:
                            proc.terminate()
                    except Exception:
                        pass
                CAMERA_PROCESSES.pop(gate_id, None)

    branch.nombre = new_nombre
    branch.direccion = direccion
    branch.telefono = telefono
    branch.horario = horario
    branch.is_24h = is_24h
    branch.latitude = latitude
    branch.longitude = longitude

    if logo_file:
        # Borrar logo anterior si existe
        if branch.logo_url and branch.logo_url != '/static/images/logo.png':
            old_path = os.path.join(branch.logo_url.lstrip('/'))
            if os.path.exists(old_path):
                os.remove(old_path)
        # Guardar nuevo logo
        file_ext = logo_file.filename.split(".")[-1]
        file_name = f"branch_{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join("static", "uploads", "branches", file_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(logo_file.file, buffer)
        branch.logo_url = f"/static/uploads/branches/{file_name}"
    elif logo_clear:
        # Borrar logo sin reemplazar
        if branch.logo_url and branch.logo_url != '/static/images/logo.png':
            old_path = branch.logo_url.lstrip('/')
            if os.path.exists(old_path):
                os.remove(old_path)
        branch.logo_url = '/static/images/logo.png'
    
    db.commit()
    return {"status": "ok", "message": "Sucursal actualizada"}

@router.post("/branches/{branch_id}/toggle")
def toggle_branch_status(branch_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_super_admin)):
    """ACTIVA O SUSPENDE UNA SUCURSAL VALIDANDO QUE NO HAYA VEHICULOS EN SU INTERIOR AL DESACTIVAR."""
    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    
    if branch.activa and _check_physical_occupancy(db, branch):
        raise HTTPException(status_code=400, detail="No se puede desactivar una sucursal con vehículos en su interior.")

    branch.activa = not branch.activa
    db.commit()
    return {"status": "ok", "activa": branch.activa}

