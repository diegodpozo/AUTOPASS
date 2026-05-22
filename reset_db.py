import os
from core.database import SessionLocal, engine
from core.config import settings
import models

def reset_db():
    print("[*] Reseteando base de datos...")
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    
    # Limpiar imágenes
    if os.path.exists(settings.IMAGE_DIR):
        for f in os.listdir(settings.IMAGE_DIR):
            if f.endswith(".jpg"):
                try: os.unlink(os.path.join(settings.IMAGE_DIR, f))
                except: pass
    print("[OK] Sistema reseteado.")

if __name__ == "__main__":
    reset_db()
