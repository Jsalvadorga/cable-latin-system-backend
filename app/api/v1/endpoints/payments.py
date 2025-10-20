# app/endpoints/payments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.crud import crud_payment
from app import schemas

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

@router.post("/", response_model=schemas.payment.PaymentOut)
def create_payment(payload: schemas.payment.PaymentCreate, db: Session = Depends(get_db)):
    # validate invoice exists is optional
    payment = crud_payment.create_payment(db, invoice_id=payload.invoice_id, amount_paid=payload.amount_paid, method=payload.payment_method or "Efectivo", notes=payload.notes)
    return payment

@router.get("/", response_model=List[schemas.payment.PaymentOut])
def list_payments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Payment).order_by(models.Payment.created_at.desc()).offset(skip).limit(limit).all()
