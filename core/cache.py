import time
from typing import Any, Optional, Dict, Tuple
from core.logger import get_logger

logger = get_logger("Cache")

class SimpleTTLCache:
    """CACHE EN MEMORIA LIGERO CON TTL E INVALIDACION EXPLICITA PARA ALTA CONCURRENCIA."""
    def __init__(self, default_ttl: float = 5.0):
        self.default_ttl = default_ttl
        self._store: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            val, expire_time = self._store[key]
            if time.time() < expire_time:
                return val
            del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        self._store[key] = (value, expiry)

    def invalidate(self, key_prefix: Optional[str] = None) -> None:
        if not key_prefix:
            self._store.clear()
        else:
            keys_to_del = [k for k in self._store if k.startswith(key_prefix)]
            for k in keys_to_del:
                self._store.pop(k, None)

ttl_cache = SimpleTTLCache(default_ttl=5.0)
