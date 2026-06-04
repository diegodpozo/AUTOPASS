import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from core.database import get_db
from core.security import get_super_admin

router = APIRouter()

@router.get("/branches", response_model=List[schemas.BranchResponse])
def list_branches(db: Session = Depends(get_db)):
    """Retorna la lista de todas las sucursales con el nombre de su administrador."""
    branches = db.query(models.ParkingBranch).all()
    
    for b in branches:
        admin_sede = db.query(models.User).filter(
            models.User.sucursal == b.nombre,
            models.User.rol == "local_admin"
        ).first()
        b.admin_name = f"{admin_sede.nombre} {admin_sede.apellido}" if admin_sede else "Sin asignar"
        
    return branches

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
    """Crea una nueva sucursal con carga de logo local."""
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
    """Elimina una sucursal (Solo Super Admin)."""
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
    db: Session = Depends(get_db), 
    admin: models.User = Depends(get_super_admin)
):
    """Actualiza la información de una sucursal con soporte para nuevo logo."""
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
        file_ext = logo_file.filename.split(".")[-1]
        file_name = f"branch_{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join("static", "uploads", "branches", file_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(logo_file.file, buffer)
        branch.logo_url = f"/static/uploads/branches/{file_name}"
    
    db.commit()
    return {"status": "ok", "message": "Sucursal actualizada"}

@router.post("/branches/{branch_id}/toggle")
def toggle_branch_status(branch_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_super_admin)):
    """Activa o suspende una sucursal."""
    branch = db.query(models.ParkingBranch).filter(models.ParkingBranch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    
    branch.activa = not branch.activa
    db.commit()
    return {"status": "ok", "activa": branch.activa}
