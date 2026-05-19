import pytest
from fastapi.testclient import TestClient
from main import app
import models, database
import uuid
import time
from datetime import datetime, timedelta

client = TestClient(app)

def get_token(email, password):
    response = client.post("/v1/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]

def test_multi_branch_isolation():
    # 1. Setup: Crear Admin Global, Local Admin A, Local Admin B
    admin_headers = {"Authorization": f"Bearer {get_token('admin@autopass.com', 'admin123')}"}
    
    unique_suffix = uuid.uuid4().hex[:4]
    sede_a = f"Sede A {unique_suffix}"
    sede_b = f"Sede B {unique_suffix}"

    # Crear Local Admin Sede A
    email_a = f"admin_a_{unique_suffix}@test.com"
    client.post("/v1/admin/users?rol=local_admin", headers=admin_headers, json={
        "nombre": "Admin", "apellido": "Sede A", "dni": str(time.time_ns())[-8:],
        "telefono": "1122334455", "email": email_a, "password": "Password123!",
        "sucursal": sede_a
    })
    
    # Crear Local Admin Sede B
    email_b = f"admin_b_{unique_suffix}@test.com"
    client.post("/v1/admin/users?rol=local_admin", headers=admin_headers, json={
        "nombre": "Admin", "apellido": "Sede B", "dni": str(time.time_ns())[-8:],
        "telefono": "1122334455", "email": email_b, "password": "Password123!",
        "sucursal": sede_b
    })

    token_a = get_token(email_a, "Password123!")
    token_b = get_token(email_b, "Password123!")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 2. Test: Precios Independientes
    # Sede A pone precio hora 2000
    client.post("/v1/settings/prices?clave=precio_hora&valor=2000", headers=headers_a)
    # Sede B pone precio hora 3000
    client.post("/v1/settings/prices?clave=precio_hora&valor=3000", headers=headers_b)

    # Verificar Sede A
    res_a = client.get("/v1/admin/settings", headers=headers_a)
    assert res_a.json()["precio_hora"] == 2000.0
    
    # Verificar Sede B
    res_b = client.get("/v1/admin/settings", headers=headers_b)
    assert res_b.json()["precio_hora"] == 3000.0

    # 3. Test: Aislamiento de Usuarios
    # Admin A crea un usuario para su sede
    user_a_email = f"user_a_{unique_suffix}@test.com"
    client.post("/v1/admin/users?rol=user", headers=headers_a, json={
        "nombre": "Cliente", "apellido": "A", "dni": str(time.time_ns())[-8:],
        "telefono": "1122334455", "email": user_a_email, "password": "Password123!",
        "sucursal": sede_a
    })

    # Admin B NO debería ver al usuario de Sede A
    res_users_b = client.get("/v1/admin/users", headers=headers_b)
    assert not any(u["email"] == user_a_email for u in res_users_b.json())

    # Admin A SÍ debería verlo
    res_users_a = client.get("/v1/admin/users", headers=headers_a)
    assert any(u["email"] == user_a_email for u in res_users_a.json())

    # 4. Test: Aislamiento de Reservas
    # Admin A crea reserva para su sede
    client.post("/v1/admin/reservations", headers=headers_a, json={
        "patente": "AAA111", "cliente_nombre": "Test A",
        "fecha_inicio": (datetime.now() + timedelta(hours=2)).isoformat(),
        "fecha_fin": (datetime.now() + timedelta(hours=4)).isoformat(),
        "sucursal_nombre": sede_a
    })

    # Admin B NO debería ver la reserva de Sede A
    res_reservations_b = client.get("/v1/admin/reservations", headers=headers_b)
    assert len(res_reservations_b.json()) == 0

    # Admin A SÍ debería verla
    res_reservations_a = client.get("/v1/admin/reservations", headers=headers_a)
    assert len(res_reservations_a.json()) == 1
    assert res_reservations_a.json()[0]["sucursal_nombre"] == sede_a

    # 5. Test: Super Admin ve TODO
    res_all_users = client.get("/v1/admin/users", headers=admin_headers)
    # Debería ver al menos admin_a, admin_b y user_a
    emails = [u["email"] for u in res_all_users.json()]
    assert email_a in emails
    assert email_b in emails
    assert user_a_email in emails

    # 6. Test: Deuda basada en precios de sede
    # Simular entrada en Sede B (Precio hora 3000)
    db = database.SessionLocal()
    # Usar 45 min para asegurar que sea 1 bloque (ceil de 0.75 es 1)
    # Si usamos 1 hora exacta, por milisegundos puede pasar a 2 bloques
    entrada_b = models.AccessLog(
        patente_detectada="BBB222", tipo_evento="ENTRADA",
        fecha_hora=(datetime.now() - timedelta(minutes=45)).isoformat(),
        sucursal=sede_b, pago_confirmado=False
    )
    db.add(entrada_b)
    db.commit()
    entry_time = entrada_b.fecha_hora # Capturar antes de cerrar
    db.close()

    from services.billing_service import BillingService
    db = database.SessionLocal()
    deuda = BillingService.calculate_debt(entry_time, db, sucursal=sede_b)
    # 1 hora * 3000 = 3000
    assert deuda == 3000.0
    
    deuda_global = BillingService.calculate_debt(entry_time, db, sucursal=None)
    # 1 hora * 1500 (default global) = 1500
    assert deuda_global == 1500.0
    db.close()

    print("\n[SUCCESS] Test de aislamiento multi-sede completado exitosamente.")

if __name__ == "__main__":
    test_multi_branch_isolation()
