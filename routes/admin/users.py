from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from core.database import get_db
from core.security import get_local_manager, get_super_admin, get_password_hash
from models.enums import UserRole
from services.user_service import UserService

router = APIRouter()

@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """Retorna la lista de usuarios. Los administradores locales ven personal de su sede y clientes registrados."""
    q = db.query(models.User)
    if str(admin.rol) != UserRole.ADMIN.value:
        from sqlalchemy import or_
        q = q.filter(
            or_(
                models.User.rol == UserRole.USER,  # Clientes registrados son visibles para todos los gestores
                models.User.sucursal == admin.sucursal # Personal y clientes específicos de la sede
            )
        )
    return q.all()

@router.post("/users")
def create_user_admin(user_data: schemas.UserCreate, rol: UserRole = UserRole.USER, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """Permite al administrador crear un nuevo usuario. Los locales solo crean para su sede."""
    if str(admin.rol) != UserRole.ADMIN.value:
        if rol == UserRole.ADMIN: 
            raise HTTPException(status_code=403, detail="No podés crear un Administrador Global")
        user_data.sucursal = admin.sucursal
    
    return UserService.create_user(db, user_data, rol, user_data.sucursal)

@router.patch("/users/{user_id}")
def update_user_admin(user_id: int, user_data: schemas.UserAdminUpdate, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """Actualiza la información de un usuario desde el panel administrativo."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if str(admin.rol) != UserRole.ADMIN.value:
        if user.sucursal != admin.sucursal and user.rol != UserRole.USER:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre este usuario")
        if user_data.rol and user_data.rol == UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="No podés asignar el rol de Administrador Global")
        if user_data.sucursal and user_data.sucursal != admin.sucursal:
             raise HTTPException(status_code=403, detail="No podés cambiar la sucursal de un usuario fuera de tu jurisdicción")

    updated = UserService.update_user(db, user_id, user_data)
    if updated:
        return {"status": "ok", "message": "Usuario actualizado correctamente"}
    raise HTTPException(status_code=400, detail="Error al actualizar el usuario")

@router.post("/users/{user_id}/role")
def change_user_role(user_id: int, nuevo_rol: UserRole, db: Session = Depends(get_db), admin: models.User = Depends(get_super_admin)):
    """Solo el Admin Global puede cambiar roles de nivel jerárquico."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.rol = nuevo_rol
    db.commit()
    return {"status": "ok"}

@router.post("/users/{user_id}/toggle-block")
def toggle_user_block(user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """Alterna el estado de bloqueo. Los locales solo bloquean a su gente."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if str(admin.rol) != UserRole.ADMIN.value and user.sucursal != admin.sucursal and user.rol != UserRole.USER:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre este usuario")

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="No podés bloquear tu propia cuenta")

    user.is_blocked = not getattr(user, 'is_blocked', False)
    db.commit()
    
    estado = "BLOQUEADO" if user.is_blocked else "ACTIVO"
    return {"status": "ok", "is_blocked": user.is_blocked, "message": f"Usuario {user.nombre} ahora está {estado}"}

@router.post("/users/{user_id}/balance")
def adjust_user_balance(user_id: int, monto: float, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """Ajusta el saldo de un usuario."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if str(admin.rol) != UserRole.ADMIN.value and user.sucursal != admin.sucursal and user.rol != UserRole.USER:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre este usuario")
        
    user.saldo = monto
    db.commit()
    return {"status": "ok"}

@router.post("/users/{user_id}/password")
def change_user_password(user_id: int, payload: schemas.UserPasswordChange, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """Permite al administrador cambiar la contraseña de un usuario."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if str(admin.rol) != UserRole.ADMIN.value and user.sucursal != admin.sucursal and user.rol != UserRole.USER:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre este usuario")

    user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return {"status": "ok", "message": f"Contraseña de {user.nombre} actualizada correctamente"}

@router.delete("/users/{user_id}")
@router.post("/users/{user_id}/delete")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_super_admin)):
    """Solo el Admin Global puede borrar cuentas definitivamente."""
    if user_id == admin.id: 
        raise HTTPException(status_code=400, detail="No podés eliminar tu propia cuenta")
    
    if UserService.delete_user(db, user_id):
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")
