import ipaddress
import secrets as _secrets
from fastapi import HTTPException, Request
from core.config import settings


def is_local_or_private(host: str) -> bool:
    """True si el host es loopback o red privada (nodo ALPR de confianza)."""
    try:
        addr = ipaddress.ip_address(host)
        return addr.is_loopback or addr.is_private
    except ValueError:
        return False


def is_trusted_alpr_node(host: str, node_secret: str) -> bool:
    """Valida un nodo ALPR: secreto configurado (comparado en tiempo constante) o red local/privada."""
    if settings.ALPR_NODE_SECRET:
        return bool(node_secret) and _secrets.compare_digest(node_secret, settings.ALPR_NODE_SECRET)
    return is_local_or_private(host)


def require_alpr_node(request: Request) -> None:
    """Dependencia: solo nodos ALPR autorizados pueden invocar endpoints de acceso por patente/QR."""
    node_secret = request.headers.get("x-node-secret") or request.query_params.get("node_secret") or ""
    host = request.client.host if request.client else ""
    if not is_trusted_alpr_node(host, node_secret):
        raise HTTPException(status_code=403, detail="Nodo ALPR no autorizado")