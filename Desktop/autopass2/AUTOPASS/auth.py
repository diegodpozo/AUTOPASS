import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import models, database

# --- CONFIGURACIÓN DE SEGURIDAD ---
SECRET_KEY = os.getenv("SECRET_KEY", "tu_super_secreto_para_produccion")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")

def verify_password(plain_password, hashed_password):
    """Verifica si una contraseña en texto plano coincide con su hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    """Genera un hash seguro utilizando bcrypt para una contraseña dada."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Genera un token JWT firmado para la sesión del usuario."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """
    Middleware de dependencia para obtener el usuario autenticado.
    Lanza una excepción 401 si el token es inválido o expiró.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales o la sesión expiró",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_super_admin(current_user: models.User = Depends(get_current_user)):
    """Valida si el usuario es Administrador Global (Control Total)."""
    if current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="Requiere permisos de Administrador Global")
    return current_user

def get_local_manager(current_user: models.User = Depends(get_current_user)):
    """Valida si el usuario es Administrador (Global o Local)."""
    if current_user.rol not in ["admin", "local_admin"]:
        raise HTTPException(status_code=403, detail="Requiere permisos de gestión administrativa")
    return current_user

def get_operational_user(current_user: models.User = Depends(get_current_user)):
    """Valida si el usuario es personal operativo (Admin, Local Admin o Staff)."""
    if current_user.rol not in ["admin", "local_admin", "staff"]:
        raise HTTPException(status_code=403, detail="Acceso restringido a personal autorizado")
    return current_user

def authenticate_user(db: Session, email: str, password: str):
    """Verifica las credenciales de un usuario contra la base de datos."""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    
    # Verificar si el usuario está bloqueado
    if hasattr(user, 'is_blocked') and user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta ha sido suspendida. Contactá al administrador."
        )
    return user
