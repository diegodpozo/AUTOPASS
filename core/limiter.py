from slowapi import Limiter
from slowapi.util import get_remote_address

# Limiter centralizado con callback por dirección IP remota
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["300/minute"]
)
