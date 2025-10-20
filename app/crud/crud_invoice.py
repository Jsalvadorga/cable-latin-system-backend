# app/crud/crud_invoice.py
from sqlalchemy.orm import Session
from app.db import models
from datetime import date
from typing import List

def create_invoice(db: Session, client_id: int, amount: float, due_date: date):
    inv = models.Invoice(client_id=client_id, amount=amount, due_date=due_date)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv

def get_invoices(db: Session, skip: int = 0, limit: int = 100) -> List[models.Invoice]:
    return db.query(models.Invoice).order_by(models.Invoice.created_at.desc()).offset(skip).limit(limit).all()

def get_invoice_by_id(db: Session, invoice_id: int):
    return db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()

def get_invoices_for_client(db: Session, client_id: int):
    return db.query(models.Invoice).filter(models.Invoice.client_id == client_id).order_by(models.Invoice.issue_date.desc()).all()

def mark_invoice_paid(db: Session, invoice_id: int):
    inv = get_invoice_by_id(db, invoice_id)
    if not inv:
        return None
    inv.status = "paid"
    db.commit()
    db.refresh(inv)
    return inv

def invoice_exists_for_month(db: Session, client_id: int, year: int, month: int):
    q = db.query(models.Invoice).filter(
        models.Invoice.client_id == client_id,
        func.date_part('year', models.Invoice.issue_date) == year,
        func.date_part('month', models.Invoice.issue_date) == month
    ).first()
    return q is not None
