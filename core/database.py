import os
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
