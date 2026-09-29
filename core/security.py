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

def get_operational_user(current_user: models.User = Depends(get_current_user)):
    """VALIDA SI EL USUARIO ES PERSONAL OPERATIVO (ADMIN, LOCAL ADMIN O STAFF)."""
    role_str = str(current_user.rol)
    if role_str not in [UserRole.ADMIN.value, UserRole.LOCAL_ADMIN.value, UserRole.STAFF.value]:
        raise HTTPException(status_code=403, detail="Acceso restringido a personal autorizado")
    return current_user

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
