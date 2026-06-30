import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# --- CONFIGURACION DE BASE DE DATOS ---
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# CREACION DEL MOTOR DE BASE DE DATOS
engine_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=engine_args)

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

    # MIGRACION: AGREGAR COLUMNAS DE CAMIONETAS SI NO EXISTEN
    try:
        with engine.connect() as conn:
            if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
                # SQLITE: NO SOPORTA ALTER TABLE ADD COLUMN CON IF NOT EXISTS
                from sqlalchemy import text
                # VERIFICAR SI LA COLUMNA YA EXISTE
                result = conn.execute(text("PRAGMA table_info(parking_aforo)")).fetchall()
                cols = [r[1] for r in result]
                if 'capacidad_camionetas' not in cols:
                    conn.execute(text("ALTER TABLE parking_aforo ADD COLUMN capacidad_camionetas INTEGER DEFAULT 5"))
                    conn.execute(text("ALTER TABLE parking_aforo ADD COLUMN ocupacion_camionetas INTEGER DEFAULT 0"))
                    print("[MIGRACION] Columnas de camionetas agregadas a parking_aforo")
                result = conn.execute(text("PRAGMA table_info(parking_floors)")).fetchall()
                cols = [r[1] for r in result]
                if 'capacidad_camionetas' not in cols:
                    conn.execute(text("ALTER TABLE parking_floors ADD COLUMN capacidad_camionetas INTEGER DEFAULT 5"))
                    conn.execute(text("ALTER TABLE parking_floors ADD COLUMN ocupacion_camionetas INTEGER DEFAULT 0"))
                    print("[MIGRACION] Columnas de camionetas agregadas a parking_floors")
                conn.commit()
            else:
                from sqlalchemy import text
                # POSTGRES/MYSQL/MARIADB
                try:
                    conn.execute(text("ALTER TABLE parking_aforo ADD COLUMN IF NOT EXISTS capacidad_camionetas INTEGER DEFAULT 5"))
                    conn.execute(text("ALTER TABLE parking_aforo ADD COLUMN IF NOT EXISTS ocupacion_camionetas INTEGER DEFAULT 0"))
                except Exception:
                    pass
                try:
                    conn.execute(text("ALTER TABLE parking_floors ADD COLUMN IF NOT EXISTS capacidad_camionetas INTEGER DEFAULT 5"))
                    conn.execute(text("ALTER TABLE parking_floors ADD COLUMN IF NOT EXISTS ocupacion_camionetas INTEGER DEFAULT 0"))
                except Exception:
                    pass
                conn.commit()
    except Exception as e:
        print(f"[MIGRACION WARN] No se pudieron agregar columnas de camionetas: {e}")
