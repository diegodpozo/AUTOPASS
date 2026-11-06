from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from core.database import Base
from schemas import UserReservationResponse


def test_reservation_uses_decimal_and_datetime_and_keeps_json_date_format():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        reservation = models.Reservation(
            patente="ABC123",
            fecha_inicio="2026-06-29T21:59:00",
            fecha_fin="2026-06-29T22:59:00",
            monto_total=Decimal("12.345"),
        )
        session.add(reservation)
        session.commit()
        session.refresh(reservation)

        assert isinstance(reservation.fecha_inicio, datetime)
        assert reservation.fecha_inicio == datetime(2026, 6, 29, 21, 59)
        assert isinstance(reservation.monto_total, Decimal)
        assert reservation.monto_total == Decimal("12.35")

        response = UserReservationResponse.model_validate(reservation)
        payload = response.model_dump(mode="json")
        assert payload["fecha_inicio"] == "2026-06-29 21:59:00"
        assert payload["monto_total"] == 12.35
    finally:
        session.close()
        engine.dispose()
