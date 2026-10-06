#!/usr/bin/env python3
from core.database import SessionLocal
from models import ParkingBranch, Vehicle, Reservation, AccessLog
from models.user import User
from faker import Faker
from core.security import get_password_hash
import random
from datetime import datetime, timedelta

def main():
    db = SessionLocal()
    f = Faker('es_AR')
    existentes = set(e[0] for e in db.query(User.email).filter(User.email.like('%@pruebaoc.com')).all())
    creados = []
    for i in range(20):
        nombre = f.first_name()
        apellido = f.last_name()
        base = f"{nombre.lower()}.{apellido.lower()}".replace(' ', '').replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('ñ','n').replace('ü','u')
        email = f"{base}@pruebaoc.com"
        if email in existentes:
            email = f"{base}{random.randint(1,99)}@pruebaoc.com"
        existentes.add(email)
        u = User(nombre=nombre, apellido=apellido, email=email, password_hash=get_password_hash('Demo1234!'), rol='user', sucursal=None, puntos_acumulados=random.randint(0,500), saldo=0.0, is_blocked=False, is_deleted=False, dni=str(random.randint(20000000,45000000)), telefono=f"11{random.randint(30000000,69999999)}", direccion=f"{f.street_name()} {random.randint(100,9999)}, {f.city()}")
        db.add(u)
        creados.append(u)
    db.commit()
    for u in creados:
        db.refresh(u)
        v = Vehicle(user_id=u.id, patente=f"AA{random.randint(100,999)}{f.lexify(text='??').upper()}", marca_modelo=f"{f.company()} {random.randint(2015,2025)}", tipo=random.choice(['AUTO','MOTO','CAMIONETA']), is_favorite=True)
        db.add(v)
    db.commit()
    branches = db.query(ParkingBranch).all()
    for u in creados:
        v = db.query(Vehicle).filter(Vehicle.user_id==u.id).first()
        if not v or not branches: continue
        b = random.choice(branches)
        for _ in range(random.randint(1,2)):
            inicio_dt = datetime.utcnow() - timedelta(days=random.randint(0,14), hours=random.randint(0,6))
            fin_dt = inicio_dt + timedelta(hours=random.randint(2,8))
            r = Reservation(user_id=u.id, patente=v.patente, fecha_inicio=inicio_dt.isoformat(), fecha_fin=fin_dt.isoformat(), monto_total=round(random.uniform(500,5000),2), monto_reembolsado=0.0, estado_pago='Pagado', estado_reserva=random.choice(['Completada','Activa']), sucursal_nombre=b.nombre, tipo_estadia='hora', cliente_nombre=u.nombre, tipo_vehiculo=v.tipo, origen='cliente', metodo_pago='SALDO')
            db.add(r)
            db.flush()
            db.add(AccessLog(patente_detectada=v.patente, normalized_patente=v.patente.replace('-','').upper(), tipo_evento='ENTRADA', tipo_vehiculo=v.tipo, reserva_id=r.id, fecha_hora=inicio_dt.isoformat()))
            db.add(AccessLog(patente_detectada=v.patente, normalized_patente=v.patente.replace('-','').upper(), tipo_evento='SALIDA', tipo_vehiculo=v.tipo, reserva_id=r.id, fecha_hora=fin_dt.isoformat()))
            u.saldo = float(u.saldo or 0) + float(r.monto_total)
    db.commit()
    db.close()
    print('OK')

if __name__ == '__main__':
    main()
