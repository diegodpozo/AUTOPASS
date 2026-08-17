import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import and_
from sqlalchemy.orm import Session
import models, schemas
from core.database import get_db
from core.security import authenticate_user, create_access_token, get_password_hash
from core.config import settings
from services.email_service import EmailService
from services.user_service import UserService
from services.user_notification_service import UserNotificationService
from models.enums import UserRole

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])

@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """REGISTRA UN NUEVO USUARIO EN EL SISTEMA."""
    # USERSERVICE YA MANEJA VALIDACIONES DE DUPLICADOS Y NORMALIZACION
    try:
        new_user = UserService.create_user(db, user, rol=UserRole.USER)
        return {"status": "ok", "message": "Usuario registrado exitosamente"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno al guardar el usuario.")

@router.post("/forgot-password")
def forgot_password(request: schemas.auth.ForgotPasswordRequest, db: Session = Depends(get_db)):
    """GENERA UN TOKEN DE RECUPERACION Y ENVIA UN CORREO AL USUARIO."""
    user = db.query(models.User).filter(models.User.email == request.email.lower().strip(), models.User.is_deleted == False).first()
    if not user:
        #POR SEGURIDAD, NO REVELAMOS SI EL CORREO EXISTE O NO
        return {"status": "ok", "message": "Si el correo está registrado, recibirás un enlace de recuperación."}
    
    # GENERAR TOKEN CON PROPOSITO DE RECUPERACION
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
    """VALIDA EL TOKEN Y ACTUALIZA LA CONTRASENA DEL USUARIO."""
    from jose import jwt, JWTError
    
    try:
        payload = jwt.decode(request.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        purpose: str = payload.get("purpose")
        
        if email is None or purpose != "recovery":
            raise HTTPException(status_code=400, detail="Token de recuperación inválido o mal formado.")
            
    except JWTError:
        raise HTTPException(status_code=400, detail="El enlace de recuperación ha expirado o es inválido.")
    
    user = db.query(models.User).filter(models.User.email == email, models.User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    # ACTUALIZAR CONTRASENA
    user.password_hash = get_password_hash(request.new_password)
    db.commit()
    
    return {"status": "ok", "message": "Tu contraseña ha sido actualizada exitosamente. Ya podés iniciar sesión."}

@router.post("/login")
def login(form_data: schemas.UserLogin, request: Request, db: Session = Depends(get_db)):
    """AUTENTICA AL USUARIO Y RETORNA UN TOKEN JWT DE ACCESO."""
    # NORMALIZAR EMAIL PARA EVITAR ERRORES DE TIPEO O MAYUSCULAS
    email_normalized = form_data.email.lower().strip()
    user = authenticate_user(db, email_normalized, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas. Verificá tu correo y contraseña.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # DETECCION MULTI-DISPOSITIVO: REGISTRAR SESION DEL DISPOSITIVO Y AVISAR
    # SOLO SI HAY OTRO DISPOSITIVO REAL CON SESION ACTIVA.
    nuevo_dispositivo = False
    device_id = (form_data.device_id or "").strip()
    if device_id:
        now = datetime.datetime.utcnow()
        user_agent = request.headers.get("user-agent") or None
        ip_address = request.client.host if request.client else None
        since = now - datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # 1) SESION CON LA MISMA DEVICE_ID (CASO NORMAL: MISMO NAVEGADOR)
        session = db.query(models.UserSession).filter(
            models.UserSession.user_id == user.id,
            models.UserSession.device_id == device_id
        ).first()

        # 2) SI EL NAVEGADOR REGENERO EL DEVICE_ID (INCOGNITO, STORAGE BORRADO,
        #    OTRO ORIGEN localhost vs 127.0.0.1) PERO ES EL MISMO PC
        #    (MISMO USER-AGENT + MISMA IP), ABSORBEMOS LA SESION RECIENTE.
        if not session and user_agent and ip_address:
            session = db.query(models.UserSession).filter(
                models.UserSession.user_id == user.id,
                models.UserSession.user_agent == user_agent,
                models.UserSession.ip_address == ip_address,
                models.UserSession.last_login_at >= since
            ).order_by(models.UserSession.last_login_at.desc()).first()
            if session:
                session.device_id = device_id

        if session:
            session.last_login_at = now
            if user_agent:
                session.user_agent = user_agent
            if ip_address:
                session.ip_address = ip_address
        else:
            db.add(models.UserSession(
                user_id=user.id,
                device_id=device_id,
                user_agent=user_agent,
                ip_address=ip_address,
                created_at=now,
                last_login_at=now,
            ))
        db.commit()

        # CONTAR OTROS DISPOSITIVOS CON SESION ACTIVA (LOGIN DENTRO DE LA VENTANA DEL TOKEN).
        # SE IGNORAN SESIONES DEL MISMO PC (MISMO USER-AGENT + MISMA IP) PARA QUE
        # EL CAMBIO DE DEVICE_ID NO DISPARE AVISOS FALSOS.
        other_q = db.query(models.UserSession.device_id).filter(
            models.UserSession.user_id == user.id,
            models.UserSession.device_id != device_id,
            models.UserSession.last_login_at >= since
        )
        if user_agent and ip_address:
            other_q = other_q.filter(~and_(
                models.UserSession.user_agent == user_agent,
                models.UserSession.ip_address == ip_address,
            ))
        other_active = other_q.distinct().count()

        if other_active > 0:
            nuevo_dispositivo = True
            UserNotificationService.create_notification(
                db,
                user.id,
                tipo="NEW_DEVICE_LOGIN",
                titulo="Nuevo inicio de sesión",
                mensaje="Detectamos un inicio de sesión desde otro dispositivo. Si no fuiste vos, te recomendamos cambiar tu contraseña.",
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
        "sucursal": user.sucursal,
        "nuevo_dispositivo": nuevo_dispositivo
    }
