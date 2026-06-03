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
        ],
        "parking_branches": [
            ("logo_url", "TEXT"),
            ("activa", "BOOLEAN DEFAULT 1"),
            ("latitude", "FLOAT"),
            ("longitude", "FLOAT")
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
        # 1. Usuarios Administrativos
        users = [
            # ADM CENTRAL / GLOBAL
            {
                "email": "admin@autopass.com",
                "nombre": "Admin", "apellido": "Global",
                "rol": "admin", "password": "admin123",
                "dni": "00000001", "sucursal": None
            },
            # ADM SUCURSALES
            {
                "email": "admcastelar@autopass.com",
                "nombre": "Pablo", "apellido": "Valente",
                "rol": "local_admin", "password": "admin123",
                "dni": "11232444", "sucursal": "AUTOPASS Castelar"
            },
            {
                "email": "admituzaingo@autopass.com",
                "nombre": "Luis", "apellido": "Lopez",
                "rol": "local_admin", "password": "admin123",
                "dni": "33202942", "sucursal": "AUTOPASS Ituzaingó"
            },
            {
                "email": "admmoron@autopass.com",
                "nombre": "Hector", "apellido": "Marquez",
                "rol": "local_admin", "password": "admin123",
                "dni": "31222124", "sucursal": "AUTOPASS Morón"
            },
            # STAFF SUCURSALES
            {
                "email": "empcastelar@autopass.com",
                "nombre": "Florencia", "apellido": "Crespo",
                "rol": "staff", "password": "admin123",
                "dni": "11221242", "sucursal": "AUTOPASS Castelar"
            },
            {
                "email": "empituzaingo@autopass.com",
                "nombre": "Rodrigo", "apellido": "Vera",
                "rol": "staff", "password": "admin123",
                "dni": "24221521", "sucursal": "AUTOPASS Ituzaingó"
            }
        ]

        for u_data in users:
            exists = db.query(models.User).filter(models.User.email == u_data["email"]).first()
            if not exists:
                print(f"[*] Creando usuario {u_data['rol'].upper()}: {u_data['email']}...")
                db.add(models.User(
                    nombre=u_data["nombre"],
                    apellido=u_data["apellido"],
                    email=u_data["email"],
                    password_hash=get_password_hash(u_data["password"]),
                    rol=u_data["rol"],
                    dni=u_data["dni"],
                    telefono="1100000000",
                    puntos_acumulados=0,
                    saldo=0.0,
                    sucursal=u_data["sucursal"]
                ))
            else:
                # Actualizar DNI si tiene puntos para cumplir con validación
                if "." in (exists.dni or ""):
                    exists.dni = exists.dni.replace(".", "")
                    print(f"[*] Normalizando DNI de {exists.email}")
        
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

        # 5. Sucursales iniciales
        if db.query(models.ParkingBranch).count() == 0:
            print("[*] Cargando red de sucursales...")
            branches = [
                models.ParkingBranch(nombre='AUTOPASS Central', direccion='Av. del Libertador 1200, CABA', telefono='11 4567-8900', horario='24hs', is_24h=True, logo_url='/static/images/logo.png', latitude=-34.5888, longitude=-58.3900),
                models.ParkingBranch(nombre='AUTOPASS Ituzaingó', direccion='Mariano Acosta 50, Ituzaingó', telefono='11 4567-8901', horario='07:00 a 23:00', is_24h=False, logo_url='/static/images/logo.png', latitude=-34.6585, longitude=-58.6685),
                models.ParkingBranch(nombre='AUTOPASS Castelar', direccion='Montes de Oca 1220, Castelar', telefono='11 4567-8902', horario='24hs', is_24h=True, logo_url='/static/images/logo.png', latitude=-34.6485, longitude=-58.6350),
                models.ParkingBranch(nombre='AUTOPASS Morón', direccion='Av. J. M. de Rosas 658, Morón', telefono='11 4567-8903', horario='07:00 a 00:00', is_24h=False, logo_url='/static/images/logo.png', latitude=-34.6508, longitude=-58.6228)
            ]
            db.add_all(branches)
        else:
            # Actualizar logos y coordenadas si existen pero están vacíos (por migración)
            db.query(models.ParkingBranch).filter(models.ParkingBranch.logo_url == None).update({models.ParkingBranch.logo_url: "/static/images/logo.png"})
            
            # Parche de coordenadas para sucursales conocidas
            coords_patch = {
                'AUTOPASS Central': (-34.5888, -58.3900),
                'AUTOPASS Ituzaingó': (-34.6585, -58.6685),
                'AUTOPASS Castelar': (-34.6485, -58.6350),
                'AUTOPASS Morón': (-34.6508, -58.6228)
            }
            for nombre, (lat, lng) in coords_patch.items():
                db.query(models.ParkingBranch).filter(
                    models.ParkingBranch.nombre == nombre,
                    models.ParkingBranch.latitude == None
                ).update({
                    models.ParkingBranch.latitude: lat,
                    models.ParkingBranch.longitude: lng
                })

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
