import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from core.database import get_db
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
    if not branch: raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    
    new_floor = models.ParkingFloor(
        branch_id=branch_id,
        nombre=data.nombre,
        capacidad_total=data.capacidad_total,
        capacidad_motos=data.capacidad_motos
    )
    db.add(new_floor)
    db.commit()
    db.refresh(new_floor)
    return new_floor

@router.delete("/floors/{floor_id}")
def delete_floor(floor_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ELIMINA UN PISO DE LA SUCURSAL."""
    floor = db.query(models.ParkingFloor).filter(models.ParkingFloor.id == floor_id).first()
    if not floor: raise HTTPException(status_code=404, detail="Piso no encontrado")
    
    db.delete(floor)
    db.commit()
    return {"status": "ok"}

@router.patch("/floors/{floor_id}", response_model=schemas.FloorResponse)
def update_floor_capacity(floor_id: int, cap_autos: int, cap_motos: int, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ACTUALIZA LA CAPACIDAD DE UN PISO."""
    floor = db.query(models.ParkingFloor).filter(models.ParkingFloor.id == floor_id).first()
    if not floor: raise HTTPException(status_code=404, detail="Piso no encontrado")
    
    floor.capacidad_total = cap_autos
    floor.capacidad_motos = cap_motos
    db.commit()
    db.refresh(floor)
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
    """CREA UNA NUEVA SUCURSAL CON CARGA DE LOGO LOCAL."""
    existing = db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == nombre).first()
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
    """ELIMINA UNA SUCURSAL (SOLO SUPER ADMIN)."""
    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    
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
    
    branch.nombre = nombre
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
    """ACTIVA O SUSPENDE UNA SUCURSAL."""
    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    
    branch.activa = not branch.activa
    db.commit()
    return {"status": "ok", "activa": branch.activa}
