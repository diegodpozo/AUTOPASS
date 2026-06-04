import sqlite3
import models
from core.database import SessionLocal, engine
from core.seed import seed_initial_data

def create_tables():
    """Crea todas las tablas definidas en los modelos de SQLAlchemy."""
    models.Base.metadata.create_all(bind=engine)

def migrate_db():
    """Ejecuta migraciones manuales para SQLite (agregado de columnas)."""
    conn = sqlite3.connect("parking.db")
    cursor = conn.cursor()
    
    tables_to_check = {
        "users": [("is_blocked", "BOOLEAN DEFAULT 0"), ("sucursal", "VARCHAR"), ("direccion", "VARCHAR")],
        "access_logs": [("sucursal", "VARCHAR")],
        "settings": [("sucursal", "VARCHAR")],
        "parking_aforo": [("sucursal", "VARCHAR")],
        "reservations": [("sucursal_nombre", "VARCHAR"), ("sucursal_info", "VARCHAR"), ("dias_semana", "VARCHAR"), ("cliente_nombre", "VARCHAR")],
        "parking_branches": [("latitude", "FLOAT"), ("longitude", "FLOAT"), ("logo_url", "VARCHAR"), ("activa", "BOOLEAN DEFAULT 1")]
    }

    for table, columns in tables_to_check.items():
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            existing_cols = [col[1] for col in cursor.fetchall()]
            for col_name, col_type in columns:
                if col_name not in existing_cols:
                    print(f"[*] Migración: Agregando columna '{col_name}' a la tabla '{table}'...")
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
        except Exception as e:
            print(f"[!] Error migrando tabla {table}: {e}")

    conn.commit()
    conn.close()

def seed_data():
    """Llamada al orquestador de seeding modular."""
    db = SessionLocal()
    try:
        seed_initial_data(db)
    except Exception as e:
        print(f"[!] Error durante el seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("======================================================")
    print("   AUTOPASS - INICIALIZADOR DE BASE DE DATOS")
    print("======================================================")
    
    print("[*] Sincronizando tablas base...")
    create_tables()
    
    migrate_db()
    seed_data()
    
    print("\n[OK] El sistema está listo para operar.")
    print("======================================================")
