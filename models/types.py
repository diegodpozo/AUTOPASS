from datetime import date, datetime, time
from decimal import Decimal, ROUND_HALF_UP as _ROUND_HALF_UP

from sqlalchemy import DateTime, Numeric, TypeDecorator

_FORMATO = "%Y-%m-%d %H:%M:%S"
_MONEY = Decimal("0.01")
MONEY_ZERO = Decimal("0.00")


def _sin_timezone(valor):
    """CONSERVA LA HORA DE PARED: QUITA TZINFO SIN CONVERTIR A UTC NI A LOCAL."""
    return valor.replace(tzinfo=None) if valor.tzinfo is not None else valor


def parse_fecha(valor):
    """PARSEA UN STRING DE FECHA FLEXIBLE (ISO CON 'T', ESPACIO, CON/SIN SEGUNDOS O MICROSEGUNDOS) A DATETIME NAIVE."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return _sin_timezone(valor)
    if isinstance(valor, date):
        return datetime.combine(valor, time.min)
    texto = str(valor).strip().replace("/", "-").replace("T", " ")
    if texto.endswith("Z"):
        texto = texto[:-1] + "+00:00"
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue
    try:
        return _sin_timezone(datetime.fromisoformat(texto))
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
    if isinstance(valor, date) and not isinstance(valor, datetime):
        valor = datetime.combine(valor, time.min)
    return valor.strftime(_FORMATO)


def to_decimal(valor):
    """CONVIERTE INT/FLOAT/STR/DECIMAL A DECIMAL SIN ARRASTRAR EL ERROR BINARIO DEL FLOAT."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, bool):
        return Decimal(int(valor))
    if isinstance(valor, int):
        return Decimal(valor)
    if isinstance(valor, float):
        return Decimal(str(valor))
    return Decimal(str(valor).strip())


def to_money(valor, default=MONEY_ZERO):
    """DEVUELVE UN DECIMAL CON DOS DECIMALES (REDONDEO COMERCIAL); None USA EL VALOR POR DEFECTO."""
    numero = to_decimal(valor)
    if numero is None:
        return default
    return numero.quantize(_MONEY, rounding=_ROUND_HALF_UP)


def round_money(valor, default=MONEY_ZERO):
    return to_money(valor, default)


class AppDateTime(datetime):
    """DATETIME QUE SERIALIZA POR DEFECTO CON ESPACIO (CONTRATO DEL FRONT/EMAILS) Y ACEPTA STRINGS AL COMPARAR."""

    def isoformat(self, sep=" ", timespec="auto"):
        return super().isoformat(sep=sep, timespec=timespec)

    @staticmethod
    def _comparable(otro):
        if isinstance(otro, str):
            return parse_fecha(otro)
        if isinstance(otro, date) and not isinstance(otro, datetime):
            return datetime.combine(otro, time.min)
        return otro

    def __eq__(self, otro):
        otro = self._comparable(otro)
        if otro is None:
            return False
        return super().__eq__(otro)

    def __ne__(self, otro):
        return not self.__eq__(otro)

    def __lt__(self, otro):
        otro = self._comparable(otro)
        if otro is None:
            return NotImplemented
        return super().__lt__(otro)

    def __le__(self, otro):
        otro = self._comparable(otro)
        if otro is None:
            return NotImplemented
        return super().__le__(otro)

    def __gt__(self, otro):
        otro = self._comparable(otro)
        if otro is None:
            return NotImplemented
        return super().__gt__(otro)

    def __ge__(self, otro):
        otro = self._comparable(otro)
        if otro is None:
            return NotImplemented
        return super().__ge__(otro)

    def __hash__(self):
        return super().__hash__()


class DateTimeValue(TypeDecorator):
    """COLUMNA TIMESTAMP REAL EN BD QUE EN PYTHON DEVUELVE AppDateTime (NAIVE)."""
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return parse_fecha(value)

    def process_result_value(self, value, dialect):
        valor = parse_fecha(value)
        if valor is None:
            return None
        return AppDateTime(
            valor.year, valor.month, valor.day,
            valor.hour, valor.minute, valor.second, valor.microsecond,
        )


class MoneyValue(TypeDecorator):
    """COLUMNA NUMERIC(12,2) QUE EN PYTHON DEVUELVE Decimal."""
    impl = Numeric(12, 2)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else to_money(value)

    def process_result_value(self, value, dialect):
        return None if value is None else to_money(value)


DateTimeAsStr = DateTimeValue
