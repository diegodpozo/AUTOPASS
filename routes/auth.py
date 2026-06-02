import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from core.database import get_db
from core.security import authenticate_user, create_access_token, get_password_hash
from core.config import settings
from services.email_service import EmailService

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])

@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario en el sistema."""
    # Verificar si el email ya existe
    existing_user = db.query(models.User).filter(models.User.email == user.email.lower().strip()).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El correo electrónico ya se encuentra registrado.")
    
    # Verificar si el DNI ya existe
    existing_dni = db.query(models.User).filter(models.User.dni == user.dni).first()
    if existing_dni:
        raise HTTPException(status_code=400, detail="El DNI ya se encuentra registrado.")
        
    # Crear el nuevo usuario
    new_user = models.User(
        nombre=user.nombre,
        apellido=user.apellido,
        dni=user.dni,
        telefono=user.telefono,
        email=user.email.lower().strip(),
        password_hash=get_password_hash(user.password),
        rol="user"
    )
    
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno al guardar el usuario.")
    
    return {"status": "ok", "message": "Usuario registrado exitosamente"}

@router.post("/forgot-password")
def forgot_password(request: schemas.auth.ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Genera un token de recuperación y envía un correo al usuario."""
    user = db.query(models.User).filter(models.User.email == request.email.lower().strip()).first()
    if not user:
        # Por seguridad, no revelamos si el correo existe o no
        return {"status": "ok", "message": "Si el correo está registrado, recibirás un enlace de recuperación."}
    
    # Generar token con propósito de recuperación (30 min)
    expires = datetime.timedelta(minutes=settings.RECOVERY_TOKEN_EXPIRE_MINUTES)
    recovery_token = create_access_token(
        data={"sub": user.email, "purpose": "recovery"},
        expires_delta=expires
    )
    
    recovery_url = f"{settings.BASE_URL}/reset-password?token={recovery_token}"
    EmailService.send_recovery_email(user.email, user.nombre, recovery_url)
    
    return {"status": "ok", "message": "Si el correo está registrado, recibirás un enlace de recuperación."}

@router.post("/reset-password")
def reset_password(request: schemas.auth.ResetPasswordRequest, db: Session = Depends(get_db)):
    """Valida el token y actualiza la contraseña del usuario."""
    from jose import jwt, JWTError
    
    try:
        payload = jwt.decode(request.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        purpose: str = payload.get("purpose")
        
        if email is None or purpose != "recovery":
            raise HTTPException(status_code=400, detail="Token de recuperación inválido o mal formado.")
            
    except JWTError:
        raise HTTPException(status_code=400, detail="El enlace de recuperación ha expirado o es inválido.")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    # Actualizar contraseña
    user.password_hash = get_password_hash(request.new_password)
    db.commit()
    
    return {"status": "ok", "message": "Tu contraseña ha sido actualizada exitosamente. Ya podés iniciar sesión."}

@router.post("/login")
def login(form_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """Autentica al usuario y retorna un token JWT de acceso."""
    user = authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas. Verificá tu correo y contraseña.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "rol": user.rol}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "rol": user.rol,
        "nombre": user.nombre,
        "apellido": user.apellido,
        "sucursal": user.sucursal
    }
