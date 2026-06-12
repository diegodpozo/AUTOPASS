import datetime
import random
import models
from core.database import SessionLocal

def simulate_finance_data():
    db = SessionLocal()
    print("[*] Iniciando simulación de datos financieros MASIVA multi-sucursal...")

    branches = db.query(models.ParkingBranch).all()
    user = db.query(models.User).filter(models.User.rol == "user").first()
    
    if not user:
        user = models.User(
            nombre="Juan", apellido="Perez", email="juan@test.com",
            password_hash="...", rol="user", dni="12345678", sucursal=None
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    now = datetime.datetime.now()

    for br in branches:
        sucursal = br.nombre
        print(f" >>> Inyectando datos en: {sucursal}")
        
        # 1. Estadías Pagadas (ALPR) - 60 registros
        for i in range(60):
            # 5 registros para hoy, el resto disperso en el mes
            dias_atras = 0 if i < 5 else random.randint(1, 30)
            fecha = now - datetime.timedelta(days=dias_atras, hours=random.randint(0, 23))
            monto = random.choice([1500, 3000, 4500, 6000, 10000])
            
            log = models.AccessLog(
                patente_detectada=f"ALPR{random.randint(100, 999)}",
                tipo_evento="SALIDA",
                fecha_hora=(fecha - datetime.timedelta(hours=2)).isoformat(),
                fecha_pago=fecha.isoformat(),
                sucursal=sucursal,
                costo_estadia=float(monto),
                pago_confirmado=True
            )
            db.add(log)

        # 2. Reservas Pagadas (WEB) - 40 registros
        for i in range(40):
            dias_atras = 0 if i < 3 else random.randint(1, 45)
            fecha = now - datetime.timedelta(days=dias_atras)
            monto = random.choice([15000, 70000, 120000, 200000])
            tipo = random.choice(["dia", "semana", "quincena", "mes"])
            
            res = models.Reservation(
                user_id=user.id,
                patente=f"WEB{random.randint(100, 999)}",
                fecha_inicio=fecha.isoformat(),
                fecha_fin=(fecha + datetime.timedelta(days=1)).isoformat(),
                sucursal_nombre=sucursal,
                tipo_estadia=tipo,
                monto_total=float(monto),
                estado_pago="Pagado",
                estado_reserva="Completada"
            )
            db.add(res)

        # 3. Reembolsos (Net Revenue impact) - 15 registros
        for i in range(15):
            dias_atras = random.randint(0, 20)
            fecha = now - datetime.timedelta(days=dias_atras)
            monto_total = float(random.randint(20000, 50000))
            monto_ref = float(random.randint(5000, 15000))
            res_ref = models.Reservation(
                user_id=user.id,
                patente=f"REF{random.randint(100, 999)}",
                fecha_inicio=fecha.isoformat(),
                fecha_fin=fecha.isoformat(),
                sucursal_nombre=sucursal,
                tipo_estadia="dia",
                monto_total=monto_total,
                monto_reembolsado=monto_ref, # Ahora guardamos cuánto se devolvió
                estado_pago="Reembolsado",
                estado_reserva="Cancelada"
            )
            db.add(res_ref)

        # 4. Incumplimiento de Reservas (Cancellations) - 20 registros
        for i in range(20):
            dias_atras = random.randint(0, 30)
            fecha = now - datetime.timedelta(days=dias_atras)
            res_can = models.Reservation(
                user_id=user.id,
                patente=f"CAN{random.randint(100, 999)}",
                fecha_inicio=fecha.isoformat(),
                fecha_fin=fecha.isoformat(),
                sucursal_nombre=sucursal,
                tipo_estadia="hora",
                monto_total=1500.0,
                estado_pago="Cancelado",
                estado_reserva="Cancelada"
            )
            db.add(res_can)

        # 5. Vehículos en el predio (Projected Income) - 5 registros
        patentes_dentro = [f"NOW{i}XY" for i in range(5)]
        for p in patentes_dentro:
            entrada = models.AccessLog(
                patente_detectada=p,
                tipo_evento="ENTRADA",
                fecha_hora=(now - datetime.timedelta(hours=random.randint(1, 10))).isoformat(),
                sucursal=sucursal,
                pago_confirmado=False
            )
            db.add(entrada)

    db.commit()
    db.close()
    print("[OK] Simulación MASIVA finalizada con éxito.")

    db.commit()
    db.close()
    print("[OK] Simulación finalizada con éxito.")

if __name__ == "__main__":
    simulate_finance_data()
