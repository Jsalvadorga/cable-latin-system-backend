# app/schemas/payment.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PaymentCreate(BaseModel):
    invoice_id: int
    amount_paid: float
    payment_method: Optional[str] = "Efectivo"
    notes: Optional[str] = None

class PaymentOut(BaseModel):
    id: int
    invoice_id: int
    amount_paid: float
    payment_date: datetime
    payment_method: str
    notes: Optional[str]

    class Config:
        orm_mode = True
