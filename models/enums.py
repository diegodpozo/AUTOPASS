from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    LOCAL_ADMIN = "local_admin"
    STAFF = "staff"
    USER = "user"

class VehicleType(str, Enum):
    AUTO = "Auto"
    MOTO = "Moto"
    CAMIONETA = "Camioneta"

class AccessEventType(str, Enum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"

class ReservationStatus(str, Enum):
    PENDIENTE = "Pendiente"
    ACTIVA = "Activa"
    COMPLETADA = "Completada"
    CANCELADA = "Cancelada"

class PaymentStatus(str, Enum):
    PENDIENTE = "Pendiente"
    PAGADO = "Pagado"
    FALLIDO = "Fallido"
    REEMBOLSADO = "Reembolsado"
    CANCELADO = "Cancelado"
