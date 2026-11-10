import datetime

from sqlalchemy import Boolean, Column, Integer, String

from core.database import Base
from models.types import DateTimeValue


class Organization(Base):
    """ORGANIZACION (EMPRESA) PROPIETARIA DE SUCURSALES Y USUARIOS.

    Cada Admin General administra UNA organizacion de forma aislada: ve solo sus
    sucursales, su personal y sus clientes. La organizacion marcada como
    `es_principal` es la unica que se muestra en el sitio publico (landing) y a
    la que pertenecen los registros de clientes hechos desde la web.
    """
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, index=True)
    es_principal = Column(Boolean, default=False)
    activa = Column(Boolean, default=True)
    created_at = Column(DateTimeValue, default=datetime.datetime.now)
