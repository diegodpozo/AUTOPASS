import pytest
from fastapi.testclient import TestClient
from main import app
from core.database import get_db, engine, init_db
from core.limiter import limiter
from sqlalchemy.orm import sessionmaker

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    limiter.reset()
    yield
    limiter.reset()

def test_login_rate_limiting():
    """VERIFICA QUE EL RATE LIMITER BLOQUEE CON HTTP 429 AL SUPERAR 15 PETICIONES EN LOGIN."""
    client = TestClient(app)
    payload = {
        "email": "invalid_attempt@autopass.com.ar",
        "password": "WrongPassword123!"
    }
    
    responses = []
    for _ in range(16):
        res = client.post("/v1/auth/login", json=payload)
        responses.append(res.status_code)
    
    # Al menos la última petición o peticiones posteriores a 15 deben retornar 429
    assert 429 in responses
