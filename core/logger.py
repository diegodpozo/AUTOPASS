import logging
import sys

LOG_FORMAT = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(level=logging.INFO):
    """CONFIGURA EL SISTEMA DE LOGGING GLOBAL DE LA APLICACION."""
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True
    )
    # REDUCIR RUIDO DE LIBRERIAS EXTERNAS
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """RETORNA UN LOGGER CON EL NOMBRE DEL MODULO."""
    return logging.getLogger(name)
