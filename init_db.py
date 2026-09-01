import sqlite3
import models
from core.database import SessionLocal, engine
from core.seed import seed_initial_data

from core.config import settings

def create_tables():
    """CREA TODAS LAS TABLAS DEFINIDAS EN LOS MODELOS DE SQLALCHEMY."""
    models.Base.metadata.create_all(bind=engine)

def migrate_db():
    """EJECUTA MIGRACIONES MANUALES PARA SQLITE (AGREGADO DE COLUMNAS)."""
    db_url = settings.DATABASE_URL
    if not db_url.startswith("sqlite"):
        print("[*] Base de datos no es SQLite, saltando migraciones manuales (usa Alembic).")
        return
    db_file = db_url.replace("sqlite:///./", "").replace("sqlite:///", "")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    tables_to_check = {
        "users": [("is_blocked", "BOOLEAN DEFAULT 0"), ("sucursal", "VARCHAR"), ("direccion", "VARCHAR")],
        "access_logs": [("sucursal", "VARCHAR"), ("tipo_vehiculo", "VARCHAR DEFAULT 'Auto'"), ("floor_id", "INTEGER"), ("metodo_pago", "VARCHAR"), ("fecha_pago", "VARCHAR")],
        "settings": [("sucursal", "VARCHAR"), ("valor_str", "VARCHAR")],
        "parking_aforo": [("sucursal", "VARCHAR"), ("capacidad_motos", "INTEGER DEFAULT 10"), ("ocupacion_motos", "INTEGER DEFAULT 0")],
        "parking_floors": [("branch_id", "INTEGER"), ("nombre", "VARCHAR"), ("capacidad_total", "INTEGER"), ("ocupacion_actual", "INTEGER"), ("capacidad_motos", "INTEGER"), ("ocupacion_motos", "INTEGER")],
        "vehicles": [("tipo", "VARCHAR DEFAULT 'Auto'"), ("is_favorite", "BOOLEAN DEFAULT 0")],
        "reservations": [("sucursal_nombre", "VARCHAR"), ("sucursal_info", "VARCHAR"), ("dias_semana", "VARCHAR"), ("cliente_nombre", "VARCHAR"), ("monto_reembolsado", "FLOAT DEFAULT 0.0"), ("fecha_pago", "VARCHAR")],
        "parking_branches": [("latitude", "FLOAT"), ("longitude", "FLOAT"), ("logo_url", "VARCHAR"), ("activa", "BOOLEAN DEFAULT 1")],
        "support_ticket_messages": [("adjunto_url", "VARCHAR"), ("adjunto_nombre", "VARCHAR")]
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
    """LLAMADA AL ORQUESTADOR DE SEEDING MODULAR."""
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
