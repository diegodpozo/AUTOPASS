from pydantic import BaseModel
from typing import Optional

class SupportTicketCreate(BaseModel):
    categoria: str
    sucursal: Optional[str] = "General"
    asunto: str
    mensaje: str

class SupportTicketUpdate(BaseModel):
    estado: str
    respuesta: Optional[str] = None
