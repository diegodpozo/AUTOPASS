from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas
from core.database import get_db
from core.security import get_local_manager, get_super_admin, get_password_hash
from core.normalize import normalize_branch_name
from models.enums import UserRole
from services.user_service import UserService
from services.user_notification_service import UserNotificationService

router = APIRouter()

@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """RETORNA LA LISTA DE USUARIOS. LOS ADMINISTRADORES LOCALES VEN PERSONAL DE SU SEDE Y CLIENTES REGISTRADOS."""
    q = db.query(models.User).filter(models.User.is_deleted == False)
    if str(admin.rol) != UserRole.ADMIN.value:
        admin_suc_norm = normalize_branch_name(admin.sucursal or "")
        all_users = q.all()
        filtered = []
        for u in all_users:
            if str(u.rol) == UserRole.USER.value or normalize_branch_name(u.sucursal or "") == admin_suc_norm:
                filtered.append(u)
        return filtered
    return q.all()

@router.post("/users")
def create_user_admin(user_data: schemas.UserCreate, rol: UserRole = UserRole.USER, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """PERMITE AL ADMINISTRADOR CREAR UN NUEVO USUARIO. LOS LOCALES SOLO CREAN PARA SU SEDE."""
    if str(admin.rol) != UserRole.ADMIN.value:
        if str(rol) == UserRole.ADMIN.value: 
            raise HTTPException(status_code=403, detail="No podés crear un Administrador Global")
        user_data.sucursal = admin.sucursal
    
    return UserService.create_user(db, user_data, rol, user_data.sucursal)

@router.patch("/users/{user_id}")
def update_user_admin(user_id: int, user_data: schemas.UserAdminUpdate, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ACTUALIZA LA INFORMACION DE UN USUARIO DESDE EL PANEL ADMINISTRATIVO."""
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if str(admin.rol) != UserRole.ADMIN.value:
        admin_suc_norm = normalize_branch_name(admin.sucursal or "")
        user_suc_norm = normalize_branch_name(user.sucursal or "")
        
        if str(user.rol) == UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="No tenés permisos para modificar a un Administrador Global")

        if str(user.rol) != UserRole.USER.value and user_suc_norm != admin_suc_norm:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre un usuario de otra sucursal")

        if user_data.rol and str(user_data.rol) == UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="No podés asignar el rol de Administrador Global")

        if user_data.sucursal and normalize_branch_name(user_data.sucursal) != admin_suc_norm:
             raise HTTPException(status_code=403, detail="No podés cambiar la sucursal de un usuario fuera de tu jurisdicción")

    updated = UserService.update_user(db, user_id, user_data)
    if updated:
        if user.rol == UserRole.USER:
            UserNotificationService.create_notification(
                db, user_id=user.id,
                tipo="datos_actualizados_admin",
                titulo="Tus datos fueron actualizados",
                mensaje="Un administrador modificó tus datos de perfil."
            )
        return {"status": "ok", "message": "Usuario actualizado correctamente"}
    raise HTTPException(status_code=400, detail="Error al actualizar el usuario")

@router.post("/users/{user_id}/role")
def change_user_role(user_id: int, nuevo_rol: UserRole, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """PERMITE CAMBIAR EL ROL DE UN USUARIO. LOS LOCALES SOLO GESTIONAN ROLES DE SU SUCURSAL."""
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted == False).first()
    if not user: raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if str(admin.rol) != UserRole.ADMIN.value:
        admin_suc_norm = normalize_branch_name(admin.sucursal or "")
        user_suc_norm = normalize_branch_name(user.sucursal or "")
        if str(user.rol) == UserRole.ADMIN.value or str(nuevo_rol) == UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="No tenés permisos para asignar o modificar el rol de Administrador Global")
        if str(user.rol) != UserRole.USER.value and user_suc_norm != admin_suc_norm:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre usuarios de otra sucursal")

    user.rol = nuevo_rol
    db.commit()

    if user.rol == UserRole.USER or nuevo_rol == UserRole.USER:
        UserNotificationService.create_notification(
            db, user_id=user.id,
            tipo="rol_cambiado_admin",
            titulo="Tu rol fue modificado",
            mensaje=f"Un administrador cambió tu rol a {nuevo_rol.value}."
        )

    return {"status": "ok"}

@router.post("/users/{user_id}/toggle-block")
def toggle_user_block(user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ALTERNA EL ESTADO DE BLOQUEO. LOS LOCALES SOLO BLOQUEAN A SU GENTE O CLIENTES."""
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if str(admin.rol) != UserRole.ADMIN.value:
        admin_suc_norm = normalize_branch_name(admin.sucursal or "")
        user_suc_norm = normalize_branch_name(user.sucursal or "")
        if str(user.rol) == UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre un Administrador Global")
        if str(user.rol) != UserRole.USER.value and user_suc_norm != admin_suc_norm:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre este usuario")

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="No podés bloquear tu propia cuenta")

    user.is_blocked = not getattr(user, 'is_blocked', False)
    db.commit()

    if user.rol == UserRole.USER:
        estado = "bloqueado" if user.is_blocked else "desbloqueado"
        UserNotificationService.create_notification(
            db, user_id=user.id,
            tipo="bloqueo_cambiado_admin",
            titulo="Estado de tu cuenta modificado",
            mensaje=f"Un administrador {estado} tu cuenta."
        )

    estado = "BLOQUEADO" if user.is_blocked else "ACTIVO"
    return {"status": "ok", "is_blocked": user.is_blocked, "message": f"Usuario {user.nombre} ahora está {estado}"}

@router.post("/users/{user_id}/balance")
def adjust_user_balance(user_id: int, monto: float, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """AJUSTA EL SALDO DE UN USUARIO."""
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted == False).first()
    if not user: raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if str(admin.rol) != UserRole.ADMIN.value:
        admin_suc_norm = normalize_branch_name(admin.sucursal or "")
        user_suc_norm = normalize_branch_name(user.sucursal or "")
        if str(user.rol) == UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre un Administrador Global")
        if str(user.rol) != UserRole.USER.value and user_suc_norm != admin_suc_norm:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre este usuario")
        
    user.saldo = monto
    db.commit()

    if user.rol == UserRole.USER:
        UserNotificationService.create_notification(
            db, user_id=user.id,
            tipo="saldo_ajustado_admin",
            titulo="Tu saldo fue ajustado",
            mensaje=f"Un administrador ajustó tu saldo a ${monto}."
        )

    return {"status": "ok"}

@router.post("/users/{user_id}/password")
def change_user_password(user_id: int, payload: schemas.UserPasswordChange, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """PERMITE AL ADMINISTRADOR CAMBIAR LA CONTRASENA DE UN USUARIO."""
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if str(admin.rol) != UserRole.ADMIN.value:
        admin_suc_norm = normalize_branch_name(admin.sucursal or "")
        user_suc_norm = normalize_branch_name(user.sucursal or "")
        if str(user.rol) == UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre un Administrador Global")
        if str(user.rol) != UserRole.USER.value and user_suc_norm != admin_suc_norm:
            raise HTTPException(status_code=403, detail="No tenés permisos sobre este usuario")

    user.password_hash = get_password_hash(payload.new_password)
    db.commit()

    if user.rol == UserRole.USER:
        UserNotificationService.create_notification(
            db, user_id=user.id,
            tipo="password_cambiada_admin",
            titulo="Tu contraseña fue cambiada",
            mensaje="Un administrador cambió tu contraseña."
        )

    return {"status": "ok", "message": f"Contraseña de {user.nombre} actualizada correctamente"}

@router.delete("/users/{user_id}")
@router.post("/users/{user_id}/delete")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """PERMITE A UN ADMINISTRADOR BORRAR CUENTAS DE SU SUCURSAL O CLIENTES."""
    if user_id == admin.id: 
        raise HTTPException(status_code=400, detail="No podés eliminar tu propia cuenta")
    
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if str(admin.rol) != UserRole.ADMIN.value:
        admin_suc_norm = normalize_branch_name(admin.sucursal or "")
        user_suc_norm = normalize_branch_name(user.sucursal or "")
        if str(user.rol) == UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="No podés eliminar a un Administrador Global")
        if str(user.rol) != UserRole.USER.value and user_suc_norm != admin_suc_norm:
            raise HTTPException(status_code=403, detail="No tenés permisos para eliminar usuarios de otra sucursal")

    if user.rol == UserRole.USER:
        UserNotificationService.create_notification(
            db, user_id=user.id,
            tipo="cuenta_eliminada_admin",
            titulo="Tu cuenta fue eliminada",
            mensaje="Un administrador eliminó tu cuenta del sistema."
        )
    db.flush()

    if UserService.delete_user(db, user_id):
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")
