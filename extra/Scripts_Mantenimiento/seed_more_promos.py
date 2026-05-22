import sqlite3
import os

# --- SCRIPT DE CARGA: CATÁLOGO DE BENEFICIOS ---

def seed_more_promos():
    """Inserta promociones adicionales de alta gama en la base de datos."""
    db_path = 'parking.db'
    if not os.path.exists(db_path): return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listado de nuevos beneficios premium
        promos = [
            ('1 Hora Gratis (Morón)', 'Válido solo en sede Morón.', 500, 'fas fa-clock', 'Beneficio', 'AUTOPASS Morón'),
            ('Lavado Eco (Castelar)', 'Lavado ecológico en sede Castelar.', 1500, 'fas fa-car-wash', 'Servicio', 'AUTOPASS Castelar'),
            ('Café de Bienvenida (Ituzaingó)', 'Café gratis al ingresar en Ituzaingó.', 100, 'fas fa-coffee', 'Cortesia', 'AUTOPASS Ituzaingó'),
            ('Abono Semanal Premium', '7 días de estacionamiento sin límites (Global).', 1200, 'fas fa-calendar-check', 'Abonos', None),
            ('Prioridad VIP', 'Acceso a lugares exclusivos.', 800, 'fas fa-crown', 'VIP', None)
        ]
        
        cursor.executemany("INSERT INTO promotions (titulo, descripcion, costo_puntos, icono, categoria, sucursal) VALUES (?, ?, ?, ?, ?, ?)", promos)
        conn.commit()
        conn.close()
        print(f"[OK] {len(promos)} promociones adicionales insertadas en el catálogo.")
    except Exception as e:
        print(f"❌ [ERROR]: {e}")

if __name__ == "__main__":
    seed_more_promos()
