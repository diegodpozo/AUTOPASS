import datetime
import hashlib
import hmac
import secrets
import time
from urllib.parse import urlencode

import requests
from fastapi import HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import models
from models.enums import UserRole
from core.config import settings
from core.logger import get_logger
from core.normalize import normalize_dni, normalize_user_name
from core.security import create_access_token, get_password_hash
from repositories.user_repository import UserRepository

logger = get_logger("OAuth")

# LEE LOS VALORES EN CADA LLAMADA PARA PERMITIR MONKEYPATCH EN TESTS.
_PROVIDERS = {
    "google": {
        "label": "Google",
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid email profile",
        "client_id": lambda: settings.GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": lambda: settings.GOOGLE_OAUTH_CLIENT_SECRET,
        "token_in_header": True,
    },
    "facebook": {
        "label": "Facebook",
        "authorize_url": "https://www.facebook.com/v19.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v19.0/oauth/access_token",
        "userinfo_url": "https://graph.facebook.com/v19.0/me",
        "userinfo_params": {"fields": "id,first_name,last_name,email"},
        "scope": "email",
        "client_id": lambda: settings.FACEBOOK_OAUTH_CLIENT_ID,
        "client_secret": lambda: settings.FACEBOOK_OAUTH_CLIENT_SECRET,
        "token_in_header": False,
    },
}


def _provider(name: str) -> dict:
    """DEVUELVE LA CONFIGURACION DEL PROVEEDOR O LANZA 404 SI NO ES SOPORTADO."""
    p = _PROVIDERS.get(name)
    if not p:
        raise HTTPException(status_code=404, detail=f"Proveedor de login social '{name}' no soportado.")
    return p


def is_provider_configured(name: str) -> bool:
    """TRUE SI EL PROVEEDOR TIENE CLIENT_ID Y CLIENT_SECRET CONFIGURADOS."""
    p = _provider(name)
    return bool((p["client_id"]() or "").strip() and (p["client_secret"]() or "").strip())


def enabled_providers() -> list:
    """LISTA DE PROVEEDORES HABILITADOS (CON CREDENCIALES) PARA EL FRONTEND."""
    result = []
    for name in ("google", "facebook"):
        try:
            if is_provider_configured(name):
                result.append({"id": name, "label": _provider(name)["label"]})
        except HTTPException:
            continue
    return result


def get_redirect_uri(name: str) -> str:
    return f"{settings.BASE_URL.rstrip('/')}/v1/auth/oauth/{name}/callback"


def get_authorize_url(name: str, state: str) -> str:
    """CONSTRUYE LA URL DE AUTHORIZACION DEL PROVEEDOR (REDIRECCION DEL NAVEGADOR)."""
    if not is_provider_configured(name):
        raise HTTPException(status_code=503, detail="El login con este proveedor no está configurado.")
    p = _provider(name)
    params = {
        "client_id": p["client_id"](),
        "redirect_uri": get_redirect_uri(name),
        "response_type": "code",
        "scope": p["scope"],
        "state": state,
    }
    if name == "google":
        params["prompt"] = "select_account"
    return f"{p['authorize_url']}?{urlencode(params)}"


# --- STATE FIRMADO (CSRF) ---

def _hmac(msg: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()


def sign_state(name: str) -> str:
    """FIRMA UN STATE PARA EL FLUJO OAUTH (STATELESS, SIN COOKIES EN EL SERVIDOR)."""
    nonce = secrets.token_urlsafe(12)
    exp = int(time.time()) + max(1, settings.OAUTH_STATE_TTL_SECONDS)
    body = f"{name}.{nonce}.{exp}"
    return f"{body}.{_hmac(body)}"


def verify_state(name: str, state: str) -> bool:
    """VALIDA INTEGRIDAD, EXPIRACION Y PROVEEDOR DEL STATE."""
    if not state:
        return False
    parts = state.split(".")
    if len(parts) != 4:
        return False
    body = ".".join(parts[:3])
    sig = parts[3]
    if not hmac.compare_digest(_hmac(body), sig):
        return False
    try:
        if int(parts[2]) < int(time.time()):
            return False
    except ValueError:
        return False
    return parts[0] == name


# --- INTERCAMBIO DE CODE POR TOKEN Y USERINFO ---

def exchange_code(name: str, code: str) -> str:
    """INTERCAMBIA EL CODIGO DE AUTORIZACION POR UN ACCESS TOKEN."""
    p = _provider(name)
    data = {
        "client_id": p["client_id"](),
        "client_secret": p["client_secret"](),
        "code": code,
        "redirect_uri": get_redirect_uri(name),
        "grant_type": "authorization_code",
    }
    try:
        resp = requests.post(p["token_url"], data=data, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth {name}: intercambio de token falló: {e}")
        raise HTTPException(status_code=502, detail="No se pudo obtener el token del proveedor social.")

    token = payload.get("access_token")
    if not token:
        raise HTTPException(status_code=502, detail="El proveedor no devolvió un token de acceso.")
    return token


def fetch_user_info(name: str, access_token: str) -> dict:
    """OBTIENE Y NORMALIZA LOS DATOS DEL USUARIO DESDE EL PROVEEDOR."""
    p = _provider(name)
    headers = {"Authorization": f"Bearer {access_token}"} if p.get("token_in_header") else None
    params = None
    if not p.get("token_in_header"):
        params = dict(p.get("userinfo_params") or {})
        params["access_token"] = access_token

    try:
        resp = requests.get(p["userinfo_url"], headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        raw = resp.json()
    except Exception as e:
        logger.error(f"OAuth {name}: falló la consulta de perfil: {e}")
        raise HTTPException(status_code=502, detail="No se pudo obtener el perfil del proveedor social.")

    if name == "google":
        email = (raw.get("email") or "").strip().lower()
        full_name = (raw.get("name") or "").strip().split()
        nombre = raw.get("given_name") or (full_name[0] if full_name else "")
        apellido = raw.get("family_name") or (full_name[-1] if len(full_name) > 1 else "")
    else:  # FACEBOOK
        email = (raw.get("email") or "").strip().lower()
        nombre = raw.get("first_name") or ""
        apellido = raw.get("last_name") or ""

    if not email:
        raise HTTPException(status_code=502, detail="El proveedor no devolvió el correo electrónico.")

    return {
        "provider_id": str(raw.get("id") or ""),
        "email": email,
        "nombre": normalize_user_name(nombre or ""),
        "apellido": normalize_user_name(apellido or ""),
    }


# --- REGISTRO POR OAUTH (CODIGO DE UN SOLO USO) ---

def issue_oauth_signup_code(email: str, provider: str, nombre: str, apellido: str) -> str:
    """EMITE UN JWT DE UN SOLO USO PARA COMPLETAR EL REGISTRO (DNI + TELEFONO)."""
    return create_access_token(
        data={
            "sub": email.lower().strip(),
            "purpose": "oauth_signup",
            "provider": provider,
            "nombre": nombre,
            "apellido": apellido,
        },
        expires_delta=datetime.timedelta(minutes=max(1, settings.OAUTH_SIGNUP_EXPIRE_MINUTES)),
    )


def decode_oauth_signup_code(code: str):
    """DECODIFICA Y VALIDA EL CODIGO DE REGISTRO (EXPIRADO O CON OTRO PROPOSITO -> None)."""
    try:
        payload = jwt.decode(code, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    if payload.get("purpose") != "oauth_signup":
        return None
    return payload


def complete_oauth_signup(db: Session, code: str, dni: str, telefono: str) -> models.User:
    """CREA UN USUARIO FINALIZANDO EL REGISTRO SOCIAL CON DNI + TELEFONO."""
    payload = decode_oauth_signup_code(code)
    if not payload:
        raise HTTPException(
            status_code=400,
            detail="El enlace de registro ha expirado o es inválido. Volvé a intentarlo desde el inicio.",
        )

    email = (payload.get("sub") or "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Datos de registro inválidos.")

    existing = UserRepository.get_active_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una cuenta con ese correo. Iniciá sesión.")

    dni_normalized = normalize_dni(dni or "")
    existing_dni = UserRepository.get_active_by_dni(db, dni_normalized)
    if existing_dni:
        raise HTTPException(status_code=400, detail="El DNI ya está registrado por otro usuario.")

    # CONTRASENA ALEATORIA: EL ACCESO ES VIA RED SOCIAL (RECUPERACION PUEDE RE-ESTABLECERLA).
    random_secret = f"oauth:{secrets.token_urlsafe(24)}"
    user = models.User(
        nombre=normalize_user_name(payload.get("nombre") or ""),
        apellido=normalize_user_name(payload.get("apellido") or ""),
        dni=dni_normalized,
        telefono=(telefono or "").strip(),
        email=email,
        password_hash=get_password_hash(random_secret),
        rol=UserRole.USER,
        sucursal=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user