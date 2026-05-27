from fastapi.testclient import TestClient
from main import app
import models
from core.database import SessionLocal
import uuid
import time
from datetime import datetime, timedelta

client = TestClient(app)

def get_admin_headers():
    # Login con el admin por defecto definido en init_db.py / HISTORIAL.md
    login_payload = {
        "email": "admin@autopass.com",
        "password": "admin123"
    }
    response = client.post("/v1/auth/login", json=login_payload)
    if response.status_code != 200:
        # Si no existe, lo creamos para el test (esto depende de si init_db.py ya corrió)
        # Pero para un entorno de test limpio, intentaremos registrarlo o usar uno existente
        pass
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_admin_staff_workflow():
    admin_headers = get_admin_headers()

    # 1. Admin lista usuarios
    response = client.get("/v1/admin/users", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # 2. Admin crea un Empleado (Staff)
    staff_email = f"staff_{uuid.uuid4().hex[:6]}@autopass.com"
    staff_payload = {
        "nombre": "Juan",
        "apellido": "Empleado",
        "dni": str(time.time_ns())[-8:],
        "telefono": "1199887766",
        "email": staff_email,
        "password": "StaffPassword123!"
    }
    response = client.post("/v1/admin/users?rol=staff", json=staff_payload, headers=admin_headers)
    assert response.status_code == 200
    assert "creado con rol staff" in response.json()["message"]

    # 3. Login como Empleado
    login_staff = {
        "email": staff_email,
        "password": "StaffPassword123!"
    }
    response = client.post("/v1/auth/login", json=login_staff)
    assert response.status_code == 200
    staff_token = response.json()["access_token"]
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # 4. Empleado accede a monitoreo (Salud del sistema)
    response = client.get("/v1/system/health", headers=staff_headers)
    assert response.status_code == 200
    assert "database" in response.json()

    # 5. Empleado crea una reserva manual para un cliente externo
    manual_res_payload = {
        "patente": "MAN123",
        "fecha_inicio": (datetime.now() + timedelta(hours=1)).isoformat(),
        "fecha_fin": (datetime.now() + timedelta(hours=3)).isoformat(),
        "tipo_estadia": "hora",
        "sucursal_nombre": "AUTOPASS Central",
        "cliente_nombre": "Cliente Externo"
    }
    response = client.post("/v1/admin/reservations", json=manual_res_payload, headers=staff_headers)
    assert response.status_code == 200
    res_id = response.json()["id"]

    # 6. Empleado confirma pago de esa reserva
    response = client.post(f"/v1/admin/reservations/{res_id}/confirm-payment", headers=staff_headers)
    assert response.status_code == 200

    # 7. Empleado registra ingreso manual
    unique_plate = f"MAN{uuid.uuid4().hex[:3]}".upper()
    response = client.post(f"/v1/admin/manual-entry?plate={unique_plate}", headers=staff_headers)
    if response.status_code != 200:
        print(f"\n[DEBUG] Error en ingreso manual para {unique_plate}: {response.json()}")
    assert response.status_code == 200
    
    # 8. Verificar que figura en el predio (Aforo)
    response = client.get("/v1/system/health", headers=staff_headers)
    # El aforo se maneja internamente, pero podemos verificar los reportes de acceso
    response = client.get(f"/v1/reports/access?patente={unique_plate}", headers=staff_headers)
    assert response.status_code == 200
    assert any(log["patente_detectada"].replace(" ", "") == unique_plate for log in response.json())

    # 9. Admin ve reportes financieros
    response = client.get("/v1/reports/financial-summary", headers=admin_headers)
    assert response.status_code == 200
    assert "total_recaudado" in response.json()

    # 10. Empleado intenta resetear el sistema (Debe fallar, solo Admin)
    response = client.post("/v1/system/reset", headers=staff_headers)
    assert response.status_code == 403 # Forbidden

    # 11. Admin bloquea al empleado
    # Obtener ID del empleado
    db = SessionLocal()
    staff_user = db.query(models.User).filter(models.User.email == staff_email).first()
    staff_id = staff_user.id
    db.close()

    response = client.post(f"/v1/admin/users/{staff_id}/toggle-block", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["is_blocked"] is True

    # 12. Empleado bloqueado intenta login (Debe fallar)
    response = client.post("/v1/auth/login", json=login_staff)
    assert response.status_code == 403
    assert "suspendida" in response.json()["detail"]

    print("\n[SUCCESS] Flujo de Admin y Staff verificado correctamente.")

if __name__ == "__main__":
    test_admin_staff_workflow()
