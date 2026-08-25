import logging
import sys
import warnings

LOG_FORMAT = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(level=logging.INFO):
    """CONFIGURA EL SISTEMA DE LOGGING GLOBAL DE LA APLICACION."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=UserWarning)

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True
    )
    # REDUCIR RUIDO DE LIBRERIAS EXTERNAS Y MIGRACIONES DE CADA INICIO
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.WARNING)
    logging.getLogger("alembic.runtime.migration").setLevel(logging.WARNING)
    logging.getLogger("paho.mqtt").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """RETORNA UN LOGGER CON EL NOMBRE DEL MODULO."""
    return logging.getLogger(name)

