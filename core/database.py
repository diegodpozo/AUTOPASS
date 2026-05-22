import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# --- CONFIGURACIÓN DE BASE DE DATOS ---
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Creación del motor de base de datos
engine_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=engine_args)

# Fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para modelos ORM
Base = declarative_base()

def get_db():
    """Dependencia para inyectar la sesión de DB en los endpoints de FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Sincroniza y crea las tablas definidas en los modelos si no existen."""
    import models
    Base.metadata.create_all(bind=engine)
