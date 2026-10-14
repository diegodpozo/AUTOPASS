import bcrypt
import uuid
from datetime import timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import models
from core.database import get_db
from core.config import settings
from core.time import utcnow
from core.normalize import normalize_branch_name
from models.enums import UserRole

# --- CONFIGURACION DE SEGURIDAD ---
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")

# JTIS REVOCADOS (LOGOUT): IN-MEMORY, SE LIMPIA AL REINICIAR
_revoked_jtis = set()

def revoke_token(token: str) -> None:
    """AGREGA EL jti DE UN TOKEN A LA LISTA DE REVOCADOS (LOGOUT)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return
    jti = payload.get("jti")
    if jti:
        _revoked_jtis.add(jti)

def verify_password(plain_password, hashed_password):
    """VERIFICA SI UNA CONTRASENA EN TEXTO PLANO COINCIDE CON SU HASH."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    """GENERA UN HASH SEGURO UTILIZANDO BCRYPT PARA UNA CONTRASENA DADA."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """GENERA UN TOKEN JWT FIRMADO PARA LA SESION DEL USUARIO."""
    to_encode = data.copy()
    if expires_delta:
        expire = utcnow() + expires_delta
    else:
        expire = utcnow() + timedelta(minutes=15)
    now = utcnow()
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": uuid.uuid4().hex,
        "token_type": to_encode.get("purpose") or "access",
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    """DECODIFICA UN TOKEN JWT Y DEVUELVE EL PAYLOAD SI ES VALIDO.
    SOLO ACEPTA TOKENS DE ACCESO (NO recovery/oauth_signup) Y NO REVOCADOS."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
    if payload.get("token_type", "access") != "access":
        return None
    jti = payload.get("jti")
    if jti and jti in _revoked_jtis:
        return None
    return payload

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    MIDDLEWARE DE DEPENDENCIA PARA OBTENER EL USUARIO AUTENTICADO.
    LANZA UNA EXCEPCION 401 SI EL TOKEN ES INVALIDO O EXPIRO.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales o la sesión expiró",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("token_type", "access") != "access":
            raise credentials_exception
        jti = payload.get("jti")
        if jti and jti in _revoked_jtis:
            raise credentials_exception
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email, models.User.is_deleted == False).first()
    if user is None:
        raise credentials_exception
    if hasattr(user, 'is_blocked') and user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta ha sido suspendida. Contactá al administrador."
        )
    return user

def get_super_admin(current_user: models.User = Depends(get_current_user)):
    """VALIDA SI EL USUARIO ES ADMINISTRADOR GLOBAL (CONTROL TOTAL)."""
    if str(current_user.rol) != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Requiere permisos de Administrador Global")
    return current_user

def get_local_manager(current_user: models.User = Depends(get_current_user)):
    """VALIDA SI EL USUARIO ES ADMINISTRADOR (GLOBAL O LOCAL)."""
    role_str = str(current_user.rol)
    if role_str not in [UserRole.ADMIN.value, UserRole.LOCAL_ADMIN.value]:
        raise HTTPException(status_code=403, detail="Requiere permisos de gestión administrativa")
    return current_user

OPERATIONAL_ROLES = (UserRole.ADMIN.value, UserRole.LOCAL_ADMIN.value, UserRole.STAFF.value)

def is_operational_role(rol) -> bool:
    """True si el rol pertenece al personal operativo (ADMIN, LOCAL ADMIN O STAFF)."""
    return getattr(rol, "value", rol) in OPERATIONAL_ROLES

def get_operational_user(current_user: models.User = Depends(get_current_user)):
    """VALIDA SI EL USUARIO ES PERSONAL OPERATIVO (ADMIN, LOCAL ADMIN O STAFF)."""
    if not is_operational_role(current_user.rol):
        raise HTTPException(status_code=403, detail="Acceso restringido a personal autorizado")
    return current_user
  
def validate_local_admin_branch(admin: models.User, branch_nombre: str):
    """Valida que un LOCAL_ADMIN solo pueda operar sobre los recursos de SU sede.

    ADMIN global no tiene restricciones. Para LOCAL_ADMIN compara la sede del
    usuario con la del recurso usando la misma normalizacion que el resto del
    proyecto, asi "Castelar" y "castelar" se consideran la misma sede.

    get_local_manager NO puede hacer esto: es una dependencia que no sabe sobre que
    sede opera cada endpoint (los recursos llegan por id de path o de body). Por eso
    los endpoints de pisos, que solo verifican el rol, deben llamar a esta funcion.
    """
    if str(admin.rol) == UserRole.ADMIN.value:
        return
    admin_suc_norm = normalize_branch_name(admin.sucursal or "")
    if normalize_branch_name(branch_nombre or "") != admin_suc_norm:
        raise HTTPException(status_code=403, detail="No tenés permisos sobre recursos de otra sucursal")

def is_principal_org_admin(user) -> bool:
    """True si el usuario es ADMIN de la organizacion principal (super-admin de plataforma).

    El Admin General de la organizacion marcada como `es_principal` administra TODAS
    las organizaciones: puede ver, editar y dar de baja a los Admin Generales que
    invita. El resto de los administradores sigue aislado a su propia organizacion.
    Es TOLERANTE: ante cualquier dato faltante (sin rol, sin organizacion o instancia
    desligada de la sesion) retorna False en vez de fallar."""
    if user is None or str(getattr(user, "rol", "")) != UserRole.ADMIN.value:
        return False
    try:
        org = getattr(user, "organization", None)
        return bool(getattr(org, "es_principal", False))
    except Exception:
        return False

def enforce_organization_scope(actor, resource_organization_id, detail: str = "No tenés permisos sobre recursos de otra organización", status_code: int = 403):
    """AISLAMIENTO MULTIEMPRESA: un administrador solo opera recursos de SU organizacion.

    Centraliza la regla para no repetirla en cada endpoint que recibe un recurso por
    id (usuarios, sucursales, pisos, promociones, camaras). Es TOLERANTE: si el actor
    o el recurso no tienen organizacion asignada (datos legacy o de tests) no se
    restringe, preservando el comportamiento single-tenant. El super-admin (ADMIN de
    la organizacion principal) queda exento para poder gestionar cualquier organizacion."""
    actor_org = getattr(actor, "organization_id", None)
    if actor_org is None or resource_organization_id is None:
        return
    if is_principal_org_admin(actor):
        return
    if resource_organization_id != actor_org:
        raise HTTPException(status_code=status_code, detail=detail)

def authenticate_user(db: Session, email: str, password: str):
    """VERIFICA LAS CREDENCIALES DE UN USUARIO CONTRA LA BASE DE DATOS."""
    user = db.query(models.User).filter(models.User.email == email, models.User.is_deleted == False).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    
    # VERIFICAR SI EL USUARIO ESTA BLOQUEADO
    if hasattr(user, 'is_blocked') and user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta ha sido suspendida. Contactá al administrador."
        )
    return user
