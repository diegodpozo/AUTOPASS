import datetime

def utcnow():
    """RETORNA LA FECHA Y HORA ACTUAL EN UTC COMO DATETIME NAIVE.
    USO EXCLUSIVO PARA EXPIracion DE TOKENS JWT (python-jose valida exp contra UTC)."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

def localnow():
    """RETORNA LA FECHA Y HORA LOCAL VIRTUAL DE AUTOPASS COMO DATETIME NAIVE.
    SE BASA EN EL RELOJ VIRTUAL (TimeService.now: hora real + offset), de modo que
    sigue siendo manipulable para pruebas. USAR para timestamps de DATOS DE NEGOCIO
    (tickets, mensajes, notificaciones, sesiones) para que coincidan con la hora
    local (ART) que muestra el frontend."""
    from services.time_service import TimeService
    return TimeService.now()
