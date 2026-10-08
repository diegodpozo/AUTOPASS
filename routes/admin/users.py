from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import models, schemas
from core.database import get_db
from core.limiter import limiter, admin_rate_limit
from core.security import get_local_manager, get_password_hash
from core.normalize import normalize_branch_name
from models.enums import UserRole, NotificationType
from services.user_service import UserService
from services.user_notification_service import UserNotificationService
from repositories.user_repository import UserRepository

router = APIRouter()


def validate_local_admin_user_permission(admin: models.User, target_user: models.User):
    """VERIFICA SI UN ADMINISTRADOR TIENE PERMISOS DE JURISDICCION SOBRE UN USUARIO OBJETIVO."""
    if str(admin.rol) == UserRole.ADMIN.value:
        return
    admin_suc_norm = normalize_branch_name(admin.sucursal or "")
    user_suc_norm = normalize_branch_name(target_user.sucursal or "")
    if str(target_user.rol) == UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre un Administrador Global")
    if str(target_user.rol) != UserRole.USER.value and user_suc_norm != admin_suc_norm:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre usuarios de otra sucursal")


def validate_staff_role_assignment(admin: models.User, nuevo_rol):
    """SOLO EL ADMINISTRADOR GLOBAL PUEDE CREAR/PROMOVER PERSONAL (STAFF/LOCAL_ADMIN).
    Un administrador local solo gestiona el rol base (USER, clientes)."""
    if str(admin.rol) == UserRole.ADMIN.value:
        return
    target = getattr(nuevo_rol, "value", nuevo_rol)
    if str(target) != UserRole.USER.value:
        raise HTTPException(
            status_code=403,
            detail="Solo el Administrador Global puede crear o asignar roles de personal (STAFF/LOCAL_ADMIN)",
        )


@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """RETORNA LA LISTA DE USUARIOS. LOS ADMINISTRADORES LOCALES VEN PERSONAL DE SU SEDE Y CLIENTES REGISTRADOS."""
    all_users = UserRepository.get_all_active(db)
    if str(admin.rol) != UserRole.ADMIN.value:
        admin_suc_norm = normalize_branch_name(admin.sucursal or "")
        filtered = []
        for u in all_users:
            if str(u.rol) == UserRole.USER.value or normalize_branch_name(u.sucursal or "") == admin_suc_norm:
                filtered.append(u)
        return filtered
    return all_users


@router.post("/users", dependencies=[Depends(admin_rate_limit)])
def create_user_admin(user_data: schemas.UserCreate, rol: UserRole = UserRole.USER, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """PERMITE AL ADMINISTRADOR CREAR UN NUEVO USUARIO. LOS LOCALES SOLO CREAN PARA SU SEDE."""
    if str(admin.rol) != UserRole.ADMIN.value:
        if rol == UserRole.ADMIN: 
            raise HTTPException(status_code=403, detail="No podés crear un Administrador Global")
        user_data.sucursal = admin.sucursal
    
    validate_staff_role_assignment(admin, rol)
    return UserService.create_user(db, user_data, rol, user_data.sucursal)


@router.patch("/users/{user_id}", dependencies=[Depends(admin_rate_limit)])
def update_user_admin(user_id: int, user_data: schemas.UserAdminUpdate, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ACTUALIZA LA INFORMACION DE UN USUARIO DESDE EL PANEL ADMINISTRATIVO."""
    user = UserRepository.get_active_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    validate_local_admin_user_permission(admin, user)
    if user_data.rol:
        validate_staff_role_assignment(admin, user_data.rol)
    if str(admin.rol) != UserRole.ADMIN.value:
        admin_suc_norm = normalize_branch_name(admin.sucursal or "")
        if user_data.rol and str(user_data.rol) == UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="No podés asignar el rol de Administrador Global")
        if user_data.sucursal and normalize_branch_name(user_data.sucursal) != admin_suc_norm:
             raise HTTPException(status_code=403, detail="No podés cambiar la sucursal de un usuario fuera de tu jurisdicción")

    updated = UserService.update_user(db, user_id, user_data)
    if updated:
        if user.rol == UserRole.USER:
            UserNotificationService.create_notification(
                db, user_id=user.id,
                tipo=NotificationType.USER_PROFILE_UPDATED,
                titulo="Tus datos fueron actualizados",
                mensaje="Un administrador modificó tus datos de perfil."
            )
        return {"status": "ok", "message": "Usuario actualizado correctamente"}
    raise HTTPException(status_code=400, detail="Error al actualizar el usuario")


@router.post("/users/{user_id}/role")
@limiter.limit("30/minute")
def change_user_role(request: Request, user_id: int, nuevo_rol: UserRole, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """PERMITE CAMBIAR EL ROL DE UN USUARIO. LOS LOCALES SOLO GESTIONAN ROLES DE SU SUCURSAL."""
    user = UserRepository.get_active_by_id(db, user_id)
    if not user: raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    validate_local_admin_user_permission(admin, user)
    validate_staff_role_assignment(admin, nuevo_rol)
    if str(admin.rol) != UserRole.ADMIN.value and nuevo_rol == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="No tenés permisos para asignar o modificar el rol de Administrador Global")

    user.rol = nuevo_rol
    db.commit()

    if user.rol == UserRole.USER or nuevo_rol == UserRole.USER:
        UserNotificationService.create_notification(
            db, user_id=user.id,
            tipo=NotificationType.USER_ROLE_CHANGED,
            titulo="Tu rol fue modificado",
            mensaje=f"Un administrador cambió tu rol a {nuevo_rol.value}."
        )

    return {"status": "ok"}


@router.post("/users/{user_id}/toggle-block")
@limiter.limit("30/minute")
def toggle_user_block(request: Request, user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """ALTERNA EL ESTADO DE BLOQUEO. LOS LOCALES SOLO BLOQUEAN A SU GENTE O CLIENTES."""
    user = UserRepository.get_active_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    validate_local_admin_user_permission(admin, user)

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="No podés bloquear tu propia cuenta")

    user.is_blocked = not getattr(user, 'is_blocked', False)
    db.commit()

    if user.rol == UserRole.USER:
        estado = "bloqueado" if user.is_blocked else "desbloqueado"
        UserNotificationService.create_notification(
            db, user_id=user.id,
            tipo=NotificationType.USER_BLOCK_STATUS_CHANGED,
            titulo="Estado de tu cuenta modificado",
            mensaje=f"Un administrador {estado} tu cuenta."
        )

    estado = "BLOQUEADO" if user.is_blocked else "ACTIVO"
    return {"status": "ok", "is_blocked": user.is_blocked, "message": f"Usuario {user.nombre} ahora está {estado}"}


@router.post("/users/{user_id}/balance")
@limiter.limit("30/minute")
def adjust_user_balance(request: Request, user_id: int, monto: float, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """AJUSTA EL SALDO DE UN USUARIO."""
    user = UserRepository.get_active_by_id(db, user_id)
    if not user: raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    validate_local_admin_user_permission(admin, user)
        
    user.saldo = monto
    db.commit()

    if user.rol == UserRole.USER:
        UserNotificationService.create_notification(
            db, user_id=user.id,
            tipo=NotificationType.BALANCE_ADJUSTED_ADMIN,
            titulo="Tu saldo fue ajustado",
            mensaje=f"Un administrador ajustó tu saldo a ${monto:,.2f}."
        )

    return {"status": "ok"}


@router.post("/users/{user_id}/password")
@limiter.limit("30/minute")
def change_user_password(request: Request, user_id: int, payload: schemas.UserPasswordChange, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """PERMITE AL ADMINISTRADOR CAMBIAR LA CONTRASENA DE UN USUARIO."""
    user = UserRepository.get_active_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    validate_local_admin_user_permission(admin, user)

    user.password_hash = get_password_hash(payload.new_password)
    db.commit()

    if user.rol == UserRole.USER:
        UserNotificationService.create_notification(
            db, user_id=user.id,
            tipo=NotificationType.PASSWORD_CHANGED_ADMIN,
            titulo="Tu contraseña fue cambiada",
            mensaje="Un administrador cambió tu contraseña."
        )

    return {"status": "ok", "message": f"Contraseña de {user.nombre} actualizada correctamente"}


@router.delete("/users/{user_id}")
@router.post("/users/{user_id}/delete")
@limiter.limit("30/minute")
def delete_user(request: Request, user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_local_manager)):
    """PERMITE A UN ADMINISTRADOR BORRAR CUENTAS DE SU SUCURSAL O CLIENTES."""
    if user_id == admin.id: 
        raise HTTPException(status_code=400, detail="No podés eliminar tu propia cuenta")
    
    user = UserRepository.get_active_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    validate_local_admin_user_permission(admin, user)

    if UserService.delete_user(db, user_id):
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

