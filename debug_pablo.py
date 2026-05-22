from database import SessionLocal
import models

def debug_pablo():
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.nombre.ilike('%pablo%')).first()
    if not user:
        print("Usuario 'pablo' no encontrado.")
        return
    
    print(f"DEBUG PABLO: ID={user.id}, Email={user.email}, Nombre={user.nombre}")
    
    reservations = db.query(models.Reservation).filter(models.Reservation.user_id == user.id).all()
    print(f"Cantidad de reservas en DB: {len(reservations)}")
    
    for r in reservations:
        print(f"- ID: {r.id}, Patente: {r.patente}, Estado: {r.estado_reserva}, Pago: {r.estado_pago}, Inicio: {r.fecha_inicio}")

    db.close()

if __name__ == "__main__":
    debug_pablo()
