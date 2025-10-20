from pydantic import BaseModel
from typing import Optional
from datetime import date

class ClientBase(BaseModel):
    full_name: str
    document: str
    email: str
    phone_number: str
    service_address: str
    billing_address: str
    client_type: str
    plan_type: str

class ClientCreate(ClientBase):
    pass

class Client(ClientBase):
    id: int
    activo: bool
    deuda: float
    vencimiento: Optional[date] = None

    class Config:
        orm_mode = True
