from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from core.config import settings
from core.logger import get_logger

logger = get_logger("Database")

def normalize_database_url(url: str) -> str:
    """NORMALIZA LA URL DE BASE DE DATOS PARA POSTGRESQL (PSYCOPG 3)."""
    if not url:
        return "sqlite:///./parking.db"
    if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
        return "postgresql+psycopg://" + url.split("://", 1)[1]
    return url

# --- CONFIGURACION DE BASE DE DATOS ---
SQLALCHEMY_DATABASE_URL = normalize_database_url(settings.DATABASE_URL)

# Motores soportados: PostgreSQL (produccion) y SQLite (desarrollo/pruebas).
# PostgreSQL usa pool de conexiones; SQLite trabaja en modo archivo sin pool explicito.
IS_SQLITE = SQLALCHEMY_DATABASE_URL.startswith("sqlite")
engine_args = {"check_same_thread": False} if IS_SQLITE else {}
pool_args = {"pool_size": 20, "max_overflow": 40, "pool_timeout": 60, "pool_pre_ping": True, "pool_recycle": 1800} if not IS_SQLITE else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=engine_args, **pool_args)

# FABRICA DE SESIONES
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# CLASE BASE PARA MODELOS ORM
Base = declarative_base()

def get_db():
    """DEPENDENCIA PARA INYECTAR LA SESION DE DB EN LOS ENDPOINTS DE FASTAPI.

    Si el endpoint termina con excepcion (p.ej. un IntegrityError que el handler
    global traduce a 409), se hace rollback explicito para devolver la sesion al
    pool en estado limpio en vez de dejarla con una transaccion abortada.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """SINCRONIZA Y CREA LAS TABLAS DEFINIDAS EN LOS MODELOS SI NO EXISTEN."""
    import models
    Base.metadata.create_all(bind=engine)


def sync_schema():
    """FLUJO UNICO DE ESQUEMA: create_all (modelos) + Alembic al head.

    Los modelos son la fuente de verdad del esquema (create_all). Alembic se
    mantiene en head para migraciones incrementales reales. Si la cadena de
    migraciones no es reproducible desde cero (esquema base ya materializado por
    los modelos), se sella la version en head con un warning explícito en vez de
    fallar en silencio.
    """
    init_db()

    try:
        from alembic.config import Config as AlembicConfig
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from alembic import command as AlembicCommand
        alembic_cfg = AlembicConfig("alembic.ini")
    except Exception as alembic_err:
        logger.warning(f"Alembic no disponible, se omite sync de version: {alembic_err}")
        return False

    heads = ScriptDirectory.from_config(alembic_cfg).get_heads()
    try:
        with engine.connect() as conn:
            current = MigrationContext.configure(conn).get_current_revision()
    except Exception as e:
        logger.warning(f"No se pudo leer alembic current: {e}")
        current = None

    if heads and current in heads:
        logger.debug(f"Esquema al head ({current}).")
        return True

    logger.info(f"Alembic current={current}, head={heads}. Sincronizando schema...")
    try:
        AlembicCommand.upgrade(alembic_cfg, "head")
        logger.info("Migraciones Alembic aplicadas hasta head.")
        return True
    except Exception as e:
        try:
            AlembicCommand.stamp(alembic_cfg, "head")
            logger.warning(
                "Migraciones no reproducibles desde cero (create_all materializó el esquema): "
                f"se selló alembic en head. Detalle: {e}"
            )
            return True
        except Exception as stamp_err:
            logger.error(f"Error al sellar alembic en head: {stamp_err}")
            raise
