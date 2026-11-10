import time
from typing import Any, Optional, Dict, Tuple
from core.logger import get_logger

logger = get_logger("Cache")

class SimpleTTLCache:
    """CACHE EN MEMORIA LIGERO CON TTL E INVALIDACION EXPLICITA PARA ALTA CONCURRENCIA."""
    def __init__(self, default_ttl: float = 5.0):
        """CREA EL CACHE CON UN TTL POR DEFECTO (EN SEGUNDOS) PARA LAS ENTRADAS SIN TTL PROPIO.

        El almacenamiento es un dict en memoria del proceso: no se comparte entre
        workers ni sobrevive a un reinicio.
        """
        self.default_ttl = default_ttl
        self._store: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """DEVUELVE EL VALOR CACHEADO SI SIGUE VIGENTE (O `None` SI EXPIRO O NO EXISTE).

        Si la entrada existe pero su TTL ya vencio, la borra en el acto y devuelve `None`.
        """
        if key in self._store:
            val, expire_time = self._store[key]
            if time.time() < expire_time:
                return val
            del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """GUARDA UN VALOR BAJO UNA CLAVE CON UN TTL EN SEGUNDOS.

        Si no se pasa `ttl` usa el `default_ttl` de la instancia; una entrada existente
        con la misma clave se pisa (y se le renueva el vencimiento).
        """
        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        self._store[key] = (value, expiry)

    def invalidate(self, key_prefix: Optional[str] = None) -> None:
        """BORRA ENTRADAS DEL CACHE, POR PREFIJO DE CLAVE O TODO SI NO SE PASA PREFIJO.

        Con `key_prefix` elimina solo las claves que empiezan con ese texto (p.ej.
        ``"occupancy_"``); sin prefijo vacia el cache completo.
        """
        if not key_prefix:
            self._store.clear()
        else:
            keys_to_del = [k for k in self._store if k.startswith(key_prefix)]
            for k in keys_to_del:
                self._store.pop(k, None)

ttl_cache = SimpleTTLCache(default_ttl=5.0)
