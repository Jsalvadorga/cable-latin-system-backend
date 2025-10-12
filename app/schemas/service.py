from pydantic import BaseModel
from typing import Optional

class ServiceBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None

class ServiceInDB(ServiceBase):
    id: int

    class Config:
        from_attributes = True
