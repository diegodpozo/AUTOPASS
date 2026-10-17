from datetime import datetime
from sqlalchemy import DateTime, TypeDecorator

_FORMATO = "%Y-%m-%d %H:%M:%S"


def parse_fecha(valor):
    """PARSEA UN STRING DE FECHA FLEXIBLE (ISO CON 'T', ESPACIO, CON/ SIN SEGUNDOS O MICROSEGUNDOS) A DATETIME."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor
    texto = str(valor).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(texto)
    except ValueError:
        raise ValueError(f"Fecha invalida: {valor!r}")


def formatear_fecha(valor):
    """CONVIERTE UN DATETIME (O STRING/None) AL FORMATO CANONICO 'YYYY-MM-DD HH:MM:SS' (SPACE CON SEGUNDOS)."""
    if not valor:
        return None
    if isinstance(valor, str):
        valor = parse_fecha(valor)
    if valor is None:
        return None
    return valor.strftime(_FORMATO)


class DateTimeAsStr(TypeDecorator):
    """COLUMNA TIMESTAMP EN LA BD QUE EN PYTHON SE COMPORTA COMO STRING 'YYYY-MM-DD HH:MM:SS'.
    MANTIENE COMPATIBILIDAD BACK/FRONT (LOS JAVASCRIPTS ESPACIAN FECHAS) SIN PERDER EL TIPO REAL EN BD."""
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return parse_fecha(value)

    def process_result_value(self, value, dialect):
        # El valor puede volver como datetime (columnas TIMESTAMP) o como string
        # (columnas VARCHAR que igual guardan fecha canonica); formatear_fecha cubre ambos.
        return formatear_fecha(value)
