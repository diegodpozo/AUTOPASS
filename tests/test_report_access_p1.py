"""P1 A5 (regresión 2026-09-27): límite server-side de /reports/access y batch de
get_reserva_ids_with_entry que reemplaza el N+1 de get_entry_for_reserva en
cleanups de reservas vencidas."""
import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base
from models import AccessLog, Reservation, User
from models.enums import AccessEventType, PaymentStatus, ReservationStatus
from repositories.access_log_repository import AccessRepository
from repositories.report_repository import ReportRepository
from services.report_service import ReportService

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    admin = User(nombre="Admin", apellido="Global", dni="99999999", email="admin@autopass.com",
                 password_hash="x", rol="admin", sucursal=None)
    db.add(admin)
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def _admin(db):
    return db.query(User).filter_by(rol="admin").first()


# ---------------------------------------------------------------------------
# get_reserva_ids_with_entry (reemplazo batch del N+1)
# ---------------------------------------------------------------------------

def test_get_reserva_ids_with_entry_devuelve_solo_con_entrada(db):
    """Batch devuelve el set de ids de reservas que tienen al menos un ENTRADA."""
    for i, (tipo, tiene_reserva) in enumerate([("ENTRADA", True), ("SALIDA", True), ("ENTRADA", False)]):
        db.add(AccessLog(
            id=i + 1, patente_detectada=f"P{i}AB", tipo_evento=tipo,
            reserva_id=(100 + i) if tiene_reserva else None,
            fecha_hora=datetime.datetime.now().isoformat(),
        ))
    db.commit()

    ids = AccessRepository.get_reserva_ids_with_entry(db, [100, 101, 102])
    assert ids == {100}


def test_get_reserva_ids_with_entry_vacio_sin_queries(db):
    """Lista vacia no ejecuta ninguna query (proteccion del IN)."""
    assert AccessRepository.get_reserva_ids_with_entry(db, []) == set()


# ---------------------------------------------------------------------------
# Límite server-side de /reports/access
# ---------------------------------------------------------------------------

def test_access_logs_history_limite_devuelve_solo_limit(db):
    """access_logs_history respeta el límite server-side (A5: evita IN gigante)."""
    for i in range(10):
        db.add(AccessLog(
            patente_detectada=f"P{i}AB", tipo_evento=AccessEventType.ENTRADA,
            fecha_hora=datetime.datetime.now().isoformat(),
        ))
    db.commit()

    logs = ReportRepository.access_logs_history(db, limit=4)
    assert len(logs) == 4
    # Orden descendente: los mas recientes primero
    assert [l.id for l in logs] == list(range(10, 6, -1))


def test_get_access_logs_deduplica_patentes_en_IN(db):
    """La resolucion de usuarios por patente deduplica (dict.fromkeys) el IN."""
    for i in range(6):
        db.add(AccessLog(
            patente_detectada="REPE" if i % 3 == 0 else f"P{i}AB",
            tipo_evento=AccessEventType.ENTRADA,
            fecha_hora=datetime.datetime.now().isoformat(),
        ))
    db.commit()

    logs = ReportService.get_access_logs(db=db, staff=_admin(db), limit=10)
    # Solo patentes unicas pasan al IN de vehicles; no crashea y entrega los logs
    assert len(logs) == 6
    patentes = {l["patente_detectada"] for l in logs}
    assert "REPE" in patentes and "P1AB" in patentes


def test_get_reserva_ids_with_entry_equivale_a_entrada_por_reserva(db):
    """Semantica: reserva protegida (con ingreso) NO queda en la cancelacion."""
    user = User(nombre="U", apellido="T", dni="11111111", email="u@test.com",
                password_hash="x", rol="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    now = datetime.datetime.now()
    res1 = Reservation(user_id=user.id, patente="AA111BB",
                       fecha_inicio=(now - datetime.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
                       fecha_fin=(now + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
                       monto_total=1000.0, estado_pago=PaymentStatus.PENDIENTE,
                       estado_reserva=ReservationStatus.PENDIENTE, tipo_estadia="hora")
    res2 = Reservation(user_id=user.id, patente="CC222DD",
                       fecha_inicio=(now - datetime.timedelta(hours=4)).strftime("%Y-%m-%d %H:%M"),
                       fecha_fin=(now + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
                       monto_total=1000.0, estado_pago=PaymentStatus.PENDIENTE,
                       estado_reserva=ReservationStatus.PENDIENTE, tipo_estadia="hora")
    db.add_all([res1, res2])
    db.commit()
    db.refresh(res1)
    db.refresh(res2)
    # res1 ya ingreso, res2 no
    db.add(AccessLog(patente_detectada="AA111BB", tipo_evento=AccessEventType.ENTRADA,
                     reserva_id=res1.id, fecha_hora=datetime.datetime.now().isoformat()))
    db.commit()

    ingresaron = AccessRepository.get_reserva_ids_with_entry(db, [res1.id, res2.id])
    assert ingresaron == {res1.id}

    from services.reservation_service import ReservationService
    ReservationService.cleanup_overdue_reservations(db)
    db.refresh(res1)
    db.refresh(res2)
    assert res1.estado_reserva == ReservationStatus.PENDIENTE  # protegida
    assert res2.estado_reserva == ReservationStatus.CANCELADA  # impaga sin ingreso