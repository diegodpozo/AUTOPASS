import models
from core.database import SessionLocal, sync_schema
from core.seed import seed_initial_data

def create_tables():
    """CREA TODAS LAS TABLAS DEFINIDAS EN LOS MODELOS DE SQLALCHEMY y
    sincroniza Alembic al head (flujo único de esquema)."""
    sync_schema()

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
    
    seed_data()
    
    print("\n[OK] El sistema está listo para operar.")
    print("======================================================")
