from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from core.database import get_db
from core.security import get_local_manager, get_super_admin, get_password_hash

router = APIRouter()

@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """Retorna la lista de usuarios. Los administradores locales solo ven personal de su sede."""
    q = db.query(models.User)
    if admin.rol != "admin":
        q = q.filter(models.User.sucursal == admin.sucursal)
        q = q.filter(models.User.rol.in_(["local_admin", "staff"]))
    return q.all()

@router.post("/users")
def create_user_admin(user_data: schemas.UserCreate, rol: str = "user", db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """Permite al administrador crear un nuevo usuario. Los locales solo crean para su sede."""
    from routes.parking import normalize_name, normalize_dni
    
    if admin.rol != "admin":
        if rol == "admin": raise HTTPException(status_code=403, detail="No podés crear un Administrador Global")
        user_data.sucursal = admin.sucursal
    
    existing = db.query(models.User).filter(models.User.email == user_data.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    if rol not in ["admin", "local_admin", "staff", "user"]:
        raise HTTPException(status_code=400, detail="Rol no válido")

    new_user = models.User(
        nombre=normalize_name(user_data.nombre),
        apellido=normalize_name(user_data.apellido),
        dni=normalize_dni(user_data.dni),
        telefono=user_data.telefono,
        email=user_data.email.lower().strip(),
        password_hash=get_password_hash(user_data.password),
        rol=rol,
        sucursal=user_data.sucursal
    )
    
    db.add(new_user)
    db.commit()
    return {"status": "ok", "message": f"Usuario {new_user.nombre} creado con rol {rol} en {new_user.sucursal or 'Global'}"}

@router.patch("/users/{user_id}")
def update_user_admin(user_id: int, user_data: schemas.UserAdminUpdate, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """Actualiza la información de un usuario desde el panel administrativo."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if admin.rol != "admin":
        if user.sucursal != admin.sucursal:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre este usuario")
        if user_data.rol and user_data.rol == "admin":
            raise HTTPException(status_code=403, detail="No podés asignar el rol de Administrador Global")
        if user_data.sucursal and user_data.sucursal != admin.sucursal:
             raise HTTPException(status_code=403, detail="No podés cambiar la sucursal de un usuario fuera de tu jurisdicción")

    if user_data.nombre: user.nombre = user_data.nombre
    if user_data.apellido: user.apellido = user_data.apellido
    if user_data.email: user.email = user_data.email.lower().strip()
    if user_data.dni: user.dni = user_data.dni
    if user_data.telefono: user.telefono = user_data.telefono
    if user_data.sucursal is not None: user.sucursal = user_data.sucursal
    if user_data.rol: user.rol = user_data.rol

    try:
        db.commit()
        return {"status": "ok", "message": "Usuario actualizado correctamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error al actualizar el usuario (posible email o DNI duplicado)")

@router.post("/users/{user_id}/role")
def change_user_role(user_id: int, nuevo_rol: str, db: Session = Depends(get_db), admin: models.User = Depends(get_super_admin)):
    """Solo el Admin Global puede cambiar roles de nivel jerárquico."""
    if nuevo_rol not in ["admin", "local_admin", "staff", "user"]:
        raise HTTPException(status_code=400, detail="Rol no válido")
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
    
    if admin.rol != "admin" and user.sucursal != admin.sucursal:
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
    
    if admin.rol != "admin" and user.sucursal != admin.sucursal:
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
    
    if admin.rol != "admin" and user.sucursal != admin.sucursal:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre este usuario")

    user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return {"status": "ok", "message": f"Contraseña de {user.nombre} actualizada correctamente"}

@router.delete("/users/{user_id}")
@router.post("/users/{user_id}/delete")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_super_admin)):
    """Solo el Admin Global puede borrar cuentas definitivamente."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.id == admin.id: raise HTTPException(status_code=400, detail="No podés eliminar tu propia cuenta")
    
    db.query(models.Vehicle).filter(models.Vehicle.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"status": "ok"}
