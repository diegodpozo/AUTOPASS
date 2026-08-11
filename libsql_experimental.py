"""Shim de compatibilidad: expone la API de libsql_experimental usando el driver `libsql`.

sqlalchemy-libsql 0.2.0 importa `libsql_experimental`, pero ese paquete no
compila en Windows. El driver oficial nuevo se llama `libsql` y es DBAPI-compatible.
"""

import libsql as _libsql

Connection = _libsql.Connection
Error = _libsql.Error
Cursor = _libsql.Cursor
paramstyle = _libsql.paramstyle
sqlite_version_info = _libsql.sqlite_version_info

_SUPPORTED_KWARGS = {
    "timeout",
    "isolation_level",
    "auth_token",
    "encryption_key",
    "sync_url",
    "sync_interval",
    "offline",
    "autocommit",
}


def connect(database, timeout=5.0, isolation_level=None, check_same_thread=True, uri=False, **kwargs):
    """Traduce kwargs del dialecto pysqlite a la firma del driver `libsql`."""
    filtered = {k: v for k, v in kwargs.items() if k in _SUPPORTED_KWARGS}
    return _libsql.connect(
        database,
        timeout=timeout,
        isolation_level=isolation_level,
        _check_same_thread=check_same_thread,
        _uri=uri,
        **filtered,
    )
