import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings
from core.logger import get_logger

logger = get_logger("Database")

# --- CONFIGURACION DE BASE DE DATOS ---
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# POSTGRES: si la URL viene sin driver (postgresql://...), usar psycopg 3
if SQLALCHEMY_DATABASE_URL.startswith("postgresql://") and "+" not in SQLALCHEMY_DATABASE_URL.split("://", 1)[0]:
    SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://" + SQLALCHEMY_DATABASE_URL.split("://", 1)[1]

# LIBSQL/TURSO: el driver real es `libsql`; el dialecto se registra como sqlite+libsql
IS_LIBSQL = SQLALCHEMY_DATABASE_URL.startswith(("libsql://", "sqlite+libsql://"))

if IS_LIBSQL:
    if not SQLALCHEMY_DATABASE_URL.startswith("sqlite+"):
        SQLALCHEMY_DATABASE_URL = "sqlite+" + SQLALCHEMY_DATABASE_URL
    from sqlalchemy.pool import QueuePool
    connect_args = {"auth_token": settings.TURSO_AUTH_TOKEN}
    pool_args = {"pool_size": 10, "max_overflow": 20, "pool_timeout": 60, "poolclass": QueuePool}
    engine_args = {}
else:
    engine_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
    pool_args = {"pool_size": 10, "max_overflow": 20, "pool_timeout": 60} if not SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
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
