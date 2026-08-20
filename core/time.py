import datetime

def utcnow():
    """RETORNA LA FECHA Y HORA ACTUAL EN UTC COMO DATETIME NAIVE."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
