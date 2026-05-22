import datetime
import sqlite3
import os
from sqlalchemy import text
from core.database import SessionLocal, engine, init_db as create_tables
from core.security import get_password_hash
import models

def migrate_db():
    """Aplica parches de esquema de forma segura para SQLite."""
    db_path = 'parking.db'
    if not os.path.exists(db_path):
        return

    print("[*] Verificando integridad del esquema...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Mapeo de tablas y columnas que deberían existir
    migrations = {
        "users": [
            ("patente", "TEXT"),
            ("sucursal", "TEXT"),
            ("is_blocked", "BOOLEAN DEFAULT 0")
        ],
        "access_logs": [
            ("fecha_pago", "TEXT"),
            ("pago_confirmado", "BOOLEAN DEFAULT 0"),
            ("costo_estadia", "FLOAT DEFAULT 0.0"),
            ("sucursal", "TEXT")
        ],
        "reservations": [
            ("sucursal_nombre", "TEXT"),
            ("sucursal_info", "TEXT"),
            ("cliente_nombre", "TEXT")
        ],
        "promotions": [
            ("activa", "BOOLEAN DEFAULT 1"),
            ("sucursal", "TEXT")
        ],
        "settings": [
            ("sucursal", "TEXT")
        ],
        "parking_aforo": [
            ("sucursal", "TEXT")
        ]
    }

    for table, columns in migrations.items():
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            existing_cols = [c[1] for c in cursor.fetchall()]
            for col_name, col_type in columns:
                if col_name not in existing_cols:
                    print(f"[*] Migración: Agregando columna '{col_name}' a la tabla '{table}'...")
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
        except Exception as e:
            print(f"[!] Error migrando tabla {table}: {e}")

    conn.commit()
    conn.close()

def seed_data():
    """Inserta datos iniciales críticos si no existen."""
    db = SessionLocal()
    try:
        # 1. Usuario Administrador Global
        admin = db.query(models.User).filter(models.User.email == "admin@autopass.com").first()
        if not admin:
            print("[*] Creando usuario Administrador Global...")
            db.add(models.User(
                nombre="Admin",
                apellido="Global",
                email="admin@autopass.com",
                password_hash=get_password_hash("admin123"),
                rol="admin",
                dni="00000000",
                telefono="1100000000",
                puntos_acumulados=0,
                saldo=0.0
            ))
        
        # 2. Configuración de Aforo Inicial (Global)
        aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == None).first()
        if not aforo:
            print("[*] Inicializando capacidad del sistema...")
            db.add(models.ParkingAforo(
                capacidad_total=20,
                ocupacion_actual=0,
                ultima_actualizacion=datetime.datetime.now().isoformat(),
                sucursal=None
            ))

        # 3. Tarifas por defecto (Global)
        default_prices = {
            "precio_hora": 1000.0,
            "precio_dia": 8000.0,
            "precio_semana": 45000.0,
            "precio_quincena": 75000.0,
            "precio_mes": 120000.0
        }
        for clave, valor in default_prices.items():
            exists = db.query(models.Settings).filter(models.Settings.clave == clave, models.Settings.sucursal == None).first()
            if not exists:
                db.add(models.Settings(clave=clave, valor=valor, sucursal=None))

        # 4. Promociones iniciales
        if db.query(models.Promotion).count() == 0:
            print("[*] Cargando catálogo de beneficios...")
            promos = [
                models.Promotion(titulo='Día Libre', descripcion='24hs de estacionamiento bonificado.', costo_puntos=500, icono='fas fa-calendar-star', categoria='Estadía'),
                models.Promotion(titulo='Lavado Premium', descripcion='Lavado completo y encerado.', costo_puntos=300, icono='fas fa-soap', categoria='Servicio'),
                models.Promotion(titulo='Café Express', descripcion='Combo café y snack en sucursal.', costo_puntos=100, icono='fas fa-coffee', categoria='Gastronomía')
            ]
            db.add_all(promos)

        db.commit()
        print("[OK] Datos maestros inicializados.")
    except Exception as e:
        print(f"[!] Error en seeding: {e}")
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
