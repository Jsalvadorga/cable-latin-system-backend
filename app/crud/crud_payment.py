# app/crud/crud_payment.py
from sqlalchemy.orm import Session
from app.db import models

def create_payment(db: Session, invoice_id: int, amount_paid: float, method: str = "Efectivo", notes: str = None):
    payment = models.Payment(invoice_id=invoice_id, amount_paid=amount_paid, payment_method=method, notes=notes)
    db.add(payment)
    # also mark invoice paid
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if invoice:
        invoice.status = "paid"
    db.commit()
    db.refresh(payment)
    return payment
