from core.database import SessionLocal
import models
from routes.parking.status import current_occupancy

class MockUser:
    def __init__(self, rol, sucursal):
        self.rol = rol
        self.sucursal = sucursal

db = SessionLocal()
user = MockUser("local_admin", "AUTOPASS Castelar")

res = current_occupancy(db, user)
print(f"Total results from API: {len(res)}")
for r in res:
    print(r)

db.close()
