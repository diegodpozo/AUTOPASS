import datetime
import models
from core.security import get_password_hash
from sqlalchemy.orm import Session

# --- DATOS DE USUARIOS INICIALES ---
INITIAL_USERS = [
    {
        "email": "admin@autopass.com",
        "nombre": "Admin", "apellido": "Global",
        "rol": "admin", "password": "admin123",
        "dni": "00000001", "sucursal": None
    },
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
    }
]

# --- TARIFAS POR DEFECTO ---
DEFAULT_PRICES = {
    "precio_hora": 1500.0,
    "precio_dia": 15000.0,
    "precio_semana": 70000.0,
    "precio_quincena": 120000.0,
    "precio_mes": 200000.0,
    
    "precio_hora_moto": 800.0,
    "precio_dia_moto": 8000.0,
    "precio_semana_moto": 35000.0,
    "precio_quincena_moto": 60000.0,
    "precio_mes_moto": 100000.0,

    "precio_hora_camioneta": 2000.0,
    "precio_dia_camioneta": 20000.0,
    "precio_semana_camioneta": 90000.0,
    "precio_quincena_camioneta": 150000.0,
    "precio_mes_camioneta": 250000.0
}

# --- PROMOCIONES INICIALES ---
INITIAL_PROMOS = [
    {"titulo": 'Día Libre', "descripcion": '24hs de estacionamiento bonificado.', "costo_puntos": 500, "icono": 'fas fa-calendar-star', "categoria": 'Estadía'},
    {"titulo": 'Lavado Premium', "descripcion": 'Lavado completo y encerado.', "costo_puntos": 300, "icono": 'fas fa-soap', "categoria": 'Servicio'},
    {"titulo": 'Café Express', "descripcion": 'Combo café y snack en sucursal.', "costo_puntos": 100, "icono": 'fas fa-coffee', "categoria": 'Gastronomía'}
]

def seed_initial_data(db: Session):
    """Orquestador de seeding para datos maestros."""
    print("[*] Iniciando proceso de Seeding...")
    
    # 1. Usuarios
    for u_data in INITIAL_USERS:
        exists = db.query(models.User).filter(models.User.email == u_data["email"]).first()
        if not exists:
            print(f"    - Creando {u_data['rol'].upper()}: {u_data['email']}")
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
            if "." in (exists.dni or ""):
                exists.dni = exists.dni.replace(".", "")
                print(f"    - Normalizando DNI: {exists.email}")

    # 2. Aforo Global
    aforo = db.query(models.ParkingAforo).filter(models.ParkingAforo.sucursal == None).first()
    if not aforo:
        print("    - Inicializando capacidad global")
        db.add(models.ParkingAforo(
            capacidad_total=20,
            ocupacion_actual=0,
            capacidad_motos=10,
            ocupacion_motos=0,
            ultima_actualizacion=datetime.datetime.now().isoformat(),
            sucursal=None
        ))
    else:
        # Parche para bases existentes sin columnas de motos
        if aforo.capacidad_motos is None:
            aforo.capacidad_motos = 10
            aforo.ocupacion_motos = 0

    # 3. Tarifas Globales
    for clave, valor in DEFAULT_PRICES.items():
        exists = db.query(models.Settings).filter(models.Settings.clave == clave, models.Settings.sucursal == None).first()
        if not exists:
            db.add(models.Settings(clave=clave, valor=valor, sucursal=None))

    # 4. Promociones
    if db.query(models.Promotion).count() == 0:
        print("    - Cargando catálogo de beneficios")
        for p in INITIAL_PROMOS:
            db.add(models.Promotion(**p))

    # 5. Sucursales (Red Inicial)
    if db.query(models.ParkingBranch).count() == 0:
        red_inicial = [
            {"nombre": "AUTOPASS Central", "direccion": "Av. del Libertador 1200, CABA", "telefono": "11 4567-8900", "horario": "24hs", "is_24h": True, "latitude": -34.5888, "longitude": -58.3900},
            {"nombre": "AUTOPASS Ituzaingó", "direccion": "Mariano Acosta 50, Ituzaingó", "telefono": "11 4567-8901", "horario": "07:00 a 23:00", "is_24h": False, "latitude": -34.6585, "longitude": -58.6685},
            {"nombre": "AUTOPASS Castelar", "direccion": "Montes de Oca 1220, Castelar", "telefono": "11 4567-8902", "horario": "24hs", "is_24h": True, "latitude": -34.6485, "longitude": -58.6350},
            {"nombre": "AUTOPASS Morón", "direccion": "Av. J. M. de Rosas 658, Morón", "telefono": "11 4567-8903", "horario": "07:00 a 00:00", "is_24h": False, "latitude": -34.6508, "longitude": -58.6228}
        ]
        for s in red_inicial:
            print(f"    - Agregando sucursal: {s['nombre']}")
            db.add(models.ParkingBranch(**s, logo_url="/static/images/logo.png"))
    else:
        # Parches para datos existentes
        db.query(models.ParkingBranch).filter(models.ParkingBranch.logo_url == None).update({models.ParkingBranch.logo_url: "/static/images/logo.png"})
        coords_patch = {
            'AUTOPASS Central': (-34.5888, -58.3900),
            'AUTOPASS Ituzaingó': (-34.6585, -58.6685),
            'AUTOPASS Castelar': (-34.6485, -58.6350),
            'AUTOPASS Morón': (-34.6508, -58.6228)
        }
        for nombre, (lat, lng) in coords_patch.items():
            db.query(models.ParkingBranch).filter(models.ParkingBranch.nombre == nombre, models.ParkingBranch.latitude == None).update({models.ParkingBranch.latitude: lat, models.ParkingBranch.longitude: lng})

    db.commit()
    print("[OK] Seeding completado.\n")
