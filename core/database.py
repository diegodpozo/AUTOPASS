import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

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

    # MIGRACION: AGREGAR COLUMNA IS_DELETED A USERS
    try:
        with engine.connect() as conn:
            if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
                from sqlalchemy import text
                result = conn.execute(text("PRAGMA table_info(users)")).fetchall()
                cols = [r[1] for r in result]
                if 'is_deleted' not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
                    print("[MIGRACION] Columna is_deleted agregada a users")
                    conn.commit()
            else:
                from sqlalchemy import text
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE"))
                    conn.commit()
                except Exception:
                    pass
    except Exception as e:
        print(f"[MIGRACION WARN] No se pudo agregar is_deleted a users: {e}")
