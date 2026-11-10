'''Protege los endpoints de nodos ALPR: valida origen local/privado y el secreto compartido del nodo'''


import ipaddress							# Importa `ipaddress` para clasificar direcciones
									# IP como loopback o rango privado
import secrets as _secrets						# Importa `secrets` como `_secrets` para comparar
									# el secreto del nodo en tiempo constante con
									# `compare_digest`
from typing import Optional						# Importa `Optional` para tipar que
									# `require_alpr_node_org` puede devolver un entero
									# o None

from fastapi import HTTPException, Request				# Importa de FastAPI `HTTPException` (para
									# responder 403) y `Request` (para leer cabeceras,
									# query y host del cliente)
from core.config import settings					# Importa `settings`, que contiene la configuracion
									# con `ALPR_NODE_SECRET` y `ALPR_NODE_ORG_ID`


def is_local_or_private(host: str) -> bool:				# Define `is_local_or_private(host)`, que decide si
									# un host es loopback o de red privada
    """True si el host es loopback o red privada (nodo ALPR de confianza)."""
    try:								# Abre un `try` porque un host que no sea una IP
									# valida lanzara `ValueError`
        addr = ipaddress.ip_address(host)				# Convierte el texto `host` en un objeto de
									# direccion IP con `ipaddress.ip_address`
        return addr.is_loopback or addr.is_private			# Devuelve True si la IP es loopback (127.x/::1) o
									# pertenece a un rango privado (10.x, 172.16-31.x,
									# 192.168.x)
    except ValueError:							# Captura el `ValueError` que ocurre cuando el host
									# no es una IP parseable
        return False							# Devuelve False para hosts que no son IPs validas
									# (por ejemplo un nombre de dominio)


def is_trusted_alpr_node(host: str, node_secret: str) -> bool:		# Define `is_trusted_alpr_node(host, node_secret)`,
									# que valida si el nodo ALPR esta autorizado
    """Valida un nodo ALPR: secreto configurado (comparado en tiempo constante) o red local/privada."""
    if settings.ALPR_NODE_SECRET:					# Comprueba si hay un `ALPR_NODE_SECRET` definido:
									# si existe, se exige el secreto en vez de confiar
									# solo en la red
        return bool(node_secret) and _secrets.compare_digest(node_secret, settings.ALPR_NODE_SECRET)
									# Exige que el `node_secret` no este vacio y que
									# coincida con el configurado usando
									# `compare_digest`, que evita ataques de
									# temporizacion
    return is_local_or_private(host)					# Si no hay secreto configurado, cae al criterio de
									# red: confia en hosts locales o privados


def require_alpr_node(request: Request) -> None:			# Define `require_alpr_node(request)`, la
									# dependencia de FastAPI que protege los endpoints
									# de acceso
    """Dependencia: solo nodos ALPR autorizados pueden invocar endpoints de acceso por patente/QR."""
    node_secret = request.headers.get("x-node-secret") or request.query_params.get("node_secret") or ""
									# Extrae el secreto del nodo desde la cabecera
									# `x-node-secret` o, como alternativa, desde el
									# parametro de query `node_secret`
    host = request.client.host if request.client else ""		# Obtiene la IP del cliente desde
									# `request.client.host` (cadena vacia si no hay
									# cliente), para el control por red
    if not is_trusted_alpr_node(host, node_secret):			# Evalua `is_trusted_alpr_node`; si el nodo no pasa
									# el control, corta la peticion
        raise HTTPException(status_code=403, detail="Nodo ALPR no autorizado")
									# Lanza `HTTPException 403` con el detalle 'Nodo
									# ALPR no autorizado', bloqueando el evento antes
									# de procesarlo


def require_alpr_node_org(request: Request) -> Optional[int]:		# Define `require_alpr_node_org(request)` como
									# dependencia que ademas de validar devuelve la
									# organizacion del nodo
    """Dependencia: valida el nodo ALPR y devuelve la ORGANIZACION A LA QUE ESTA LIGADO.

    `ALPR_NODE_ORG_ID` bindea el nodo con una empresa (0 = sin binding): los flujos
    de acceso usan ese valor para acotar gate -> sede -> empresa y rechazar gates
    que no pertenezcan a la organizacion del nodo."""
    require_alpr_node(request)						# Reutiliza `require_alpr_node(request)` para
									# aplicar el control de autorizacion del nodo
									# (delega, no duplica la validacion)
    return settings.ALPR_NODE_ORG_ID or None				# Devuelve `ALPR_NODE_ORG_ID` o None si es 0,
									# bindeando el evento con su organizacion para el
									# aislamiento multiempresa