from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from core.database import Base
from core.time import localnow

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    categoria   = Column(String, nullable=False)
    sucursal    = Column(String, default="General", index=True)
    asunto      = Column(String, nullable=False)
    mensaje     = Column(Text, nullable=False)
    estado      = Column(String, default="Pendiente", index=True)
    created_at     = Column(DateTime, default=localnow)
    updated_at  = Column(DateTime, default=localnow, onupdate=localnow)

    user        = relationship("User", backref="tickets")


class SupportTicketMessage(Base):
    __tablename__ = "support_ticket_messages"

    id          = Column(Integer, primary_key=True)
    ticket_id   = Column(Integer, ForeignKey("support_tickets.id"), nullable=False, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    mensaje     = Column(Text, nullable=False)
    adjunto_url     = Column(String, nullable=True)    # URL DEL ARCHIVO ADJUNTADO (imagen o PDF)
    adjunto_nombre  = Column(String, nullable=True)    # NOMBRE ORIGINAL DEL ARCHIVO
    created_at  = Column(DateTime, default=localnow)

    ticket      = relationship("SupportTicket", backref="messages")
    user        = relationship("User")
