# app/schemas/invoice.py
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class InvoiceBase(BaseModel):
    client_id: int
    amount: float
    due_date: Optional[date]

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseModel):
    status: Optional[str]
    due_date: Optional[date]
    amount: Optional[float]

class InvoiceOut(BaseModel):
    id: int
    client_id: int
    amount: float
    status: str
    issue_date: date
    due_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
