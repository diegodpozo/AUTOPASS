import datetime
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import models, schemas
from core.database import get_db
from core.security import get_current_user, authenticate_user, create_access_token, get_password_hash, revoke_token, oauth2_scheme
from core.config import settings
from services.email_service import EmailService
from services.user_service import UserService
from services.user_notification_service import UserNotificationService
from services import oauth_service
from core.limiter import limiter
from models.enums import UserRole
from repositories.user_repository import UserRepository
from repositories.session_repository import SessionRepository

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])

def _oauth_redirect(**params):
    """REDIRIGE AL FRONTEND CON PARAMETROS EN EL FRAGMENTO (#...) PARA NO EXPONERLOS EN LOGS."""
    fragment = "&".join(
        f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items() if v is not None
    )
    return RedirectResponse(url=f"/#{fragment}", status_code=303)

def _login_payload(user: models.User, nuevo_dispositivo: bool = False) -> dict:
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

@router.post("/register")
@limiter.limit("10/minute")
def register(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    """REGISTRA UN NUEVO USUARIO EN EL SISTEMA."""
    # USERSERVICE YA MANEJA VALIDACIONES DE DUPLICADOS Y NORMALIZACION
    try:
        UserService.create_user(db, user, rol=UserRole.USER)
        return {"status": "ok", "message": "Usuario registrado exitosamente"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno al guardar el usuario.")

@router.post("/forgot-password")
@limiter.limit("5/minute")
def forgot_password(request: Request, body: schemas.auth.ForgotPasswordRequest, db: Session = Depends(get_db)):
    """GENERA UN TOKEN DE RECUPERACION Y ENVIA UN CORREO AL USUARIO."""
    user = UserRepository.get_active_by_email(db, body.email.lower().strip())
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
@limiter.limit("10/minute")
def reset_password(request: Request, body: schemas.auth.ResetPasswordRequest, db: Session = Depends(get_db)):
    """VALIDA EL TOKEN Y ACTUALIZA LA CONTRASENA DEL USUARIO."""
    from jose import jwt, JWTError
    
    try:
        payload = jwt.decode(body.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        purpose: str = payload.get("purpose")
        
        if email is None or purpose != "recovery":
            raise HTTPException(status_code=400, detail="Token de recuperación inválido o mal formado.")
            
    except JWTError:
        raise HTTPException(status_code=400, detail="El enlace de recuperación ha expirado o es inválido.")
    
    user = UserRepository.get_active_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    # ACTUALIZAR CONTRASENA
    user.password_hash = get_password_hash(body.new_password)
    db.commit()
    
    return {"status": "ok", "message": "Tu contraseña ha sido actualizada exitosamente. Ya podés iniciar sesión."}

@router.post("/login")
@limiter.limit("15/minute")
def login(request: Request, form_data: schemas.UserLogin, db: Session = Depends(get_db)):
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
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        user_agent = request.headers.get("user-agent") or None
        ip_address = request.client.host if request.client else None
        since = now - datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # 1) SESION CON LA MISMA DEVICE_ID (CASO NORMAL: MISMO NAVEGADOR)
        session = SessionRepository.get_by_device(db, user.id, device_id)

        # 2) SI EL NAVEGADOR REGENERO EL DEVICE_ID (INCOGNITO, STORAGE BORRADO,
        #    OTRO ORIGEN localhost vs 127.0.0.1) PERO ES EL MISMO NAVEGADOR (MISMO USER-AGENT),
        #    ABSORBEMOS LA SESION RECIENTE.
        if not session and user_agent:
            session = SessionRepository.get_recent_by_user_agent(db, user.id, user_agent, since)
            if session:
                session.device_id = device_id

        is_new_device = (session is None)

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
        # SE IGNORAN SESIONES DEL MISMO NAVEGADOR (MISMO USER-AGENT) PARA EVITAR AVISOS FALSOS.
        other_active = SessionRepository.count_other_devices(db, user.id, device_id, since, user_agent)

        if is_new_device and other_active > 0:
            nuevo_dispositivo = True
            UserNotificationService.create_notification(
                db,
                user.id,
                tipo="NEW_DEVICE_LOGIN",
                titulo="Nuevo inicio de sesión",
                mensaje="Detectamos un inicio de sesión desde un nuevo dispositivo. Si no fuiste vos, te recomendamos cambiar tu contraseña.",
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

@router.post("/logout")
@limiter.limit("30/minute")
def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    body: dict = None,
):
    """CIERRA LA SESION DE UN DISPOSITIVO: REVOCA EL jti DEL TOKEN
    Y ELIMINA LA UserSession DEL DEVICE_ID INDICADO."""
    revoke_token(token)
    device_id = ((body or {}).get("device_id") or "").strip()
    if device_id:
        try:
            db.query(models.UserSession).filter(
                models.UserSession.user_id == current_user.id,
                models.UserSession.device_id == device_id,
            ).delete()
            db.commit()
        except Exception:
            db.rollback()
    return {"status": "ok"}

@router.get("/oauth/providers")
@limiter.limit("30/minute")
def oauth_providers(request: Request):
    """LISTA LOS PROVEEDORES DE LOGIN SOCIAL HABILITADOS (CON CREDENCIALES)."""
    return {"providers": oauth_service.enabled_providers()}

@router.get("/oauth/{provider}/authorize")
@limiter.limit("10/minute")
def oauth_authorize(request: Request, provider: str, redirect: str = None):
    """INICIA EL FLUJO OAUTH: REDIRIGE AL NAVEGADOR HACIA EL PROVEEDOR."""
    if not oauth_service.is_provider_configured(provider):
        raise HTTPException(status_code=503, detail="El login con este proveedor no está configurado.")
    state = oauth_service.sign_state(provider)
    auth_url = oauth_service.get_authorize_url(provider, state)
    return RedirectResponse(url=auth_url, status_code=302)

@router.get("/oauth/{provider}/callback")
@limiter.limit("10/minute")
def oauth_callback(
    request: Request,
    provider: str,
    db: Session = Depends(get_db),
    code: str = None,
    state: str = None,
    error: str = None,
):
    """RECIBE EL RETORNO DEL PROVEEDOR Y RESUELVE LOGIN O REGISTRO SOCIAL."""
    if error:
        return _oauth_redirect(oauth_error="denegado")

    if not oauth_service.verify_state(provider, state):
        return _oauth_redirect(oauth_error="state_invalido")

    if not code:
        return _oauth_redirect(oauth_error="sin_codigo")

    try:
        access_token = oauth_service.exchange_code(provider, code)
        info = oauth_service.fetch_user_info(provider, access_token)
    except HTTPException as e:
        return _oauth_redirect(oauth_error=e.detail)

    email = info["email"]
    user = UserRepository.get_active_by_email(db, email)

    if user:
        if user.is_blocked:
            return _oauth_redirect(oauth_error="bloqueado")
        payload = _login_payload(user)
        return _oauth_redirect(
            oauth_token=payload["access_token"],
            oauth_rol=payload["rol"],
            oauth_nombre=user.nombre,
            oauth_apellido=user.apellido,
        )

    signup_code = oauth_service.issue_oauth_signup_code(
        email, provider, info["nombre"], info["apellido"]
    )
    return _oauth_redirect(
        oauth_signup=signup_code,
        oauth_email=email,
        oauth_provider=provider,
        oauth_nombre=info["nombre"],
        oauth_apellido=info["apellido"],
    )

@router.post("/oauth/complete")
@limiter.limit("10/minute")
def oauth_complete(request: Request, body: schemas.auth.OAuthComplete, db: Session = Depends(get_db)):
    """COMPLETA EL REGISTRO SOCIAL: VALIDA DNI/TELEFONO Y LOGUEA AL USUARIO."""
    user = oauth_service.complete_oauth_signup(db, body.code, body.dni, body.telefono)
    return _login_payload(user)
