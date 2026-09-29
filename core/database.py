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

# LIBSQL/TURSO: el driver real es `libsql`; el dialecto se registra como sqlite+libsql
IS_LIBSQL = SQLALCHEMY_DATABASE_URL.startswith(("libsql://", "sqlite+libsql://"))

if IS_LIBSQL:
    if not SQLALCHEMY_DATABASE_URL.startswith("sqlite+"):
        SQLALCHEMY_DATABASE_URL = "sqlite+" + SQLALCHEMY_DATABASE_URL
    from sqlalchemy.pool import QueuePool
    connect_args = {"auth_token": settings.TURSO_AUTH_TOKEN}
    pool_args = {"pool_size": 20, "max_overflow": 40, "pool_timeout": 60, "pool_pre_ping": True, "pool_recycle": 1800, "poolclass": QueuePool}
    engine_args = {}
else:
    engine_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
    pool_args = {"pool_size": 20, "max_overflow": 40, "pool_timeout": 60, "pool_pre_ping": True, "pool_recycle": 1800} if not SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
    connect_args = {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={**connect_args, **engine_args}, **pool_args)

# FABRICA DE SESIONES
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# CLASE BASE PARA MODELOS ORM
Base = declarative_base()

def get_db():
    """DEPENDENCIA PARA INYECTAR LA SESION DE DB EN LOS ENDPOINTS DE FASTAPI."""
    db = SessionLocal()
    try:
        yield db
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
