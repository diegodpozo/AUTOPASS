from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

# Limiter centralizado con callback por dirección IP remota
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["300/minute"]
)

@limiter.limit("30/minute")
def admin_rate_limit(request: Request):
    """LIMITE COMPARTIDO PARA MUTACIONES DEL PANEL ADMIN (30/min por IP).
    Se usa como dependency: dependencies=[Depends(admin_rate_limit)] para no
    exigir request en la firma del endpoint (los tests llaman las funciones directo)."""
    return None
