# app/services/generate_invoices.py
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.crud import crud_invoice
from app.db import models
from app.db.models import Invoice
from app.database import SessionLocal

def calcular_deuda_por_plan(plan_type: str) -> float:
    if "TV + Internet" in plan_type:
        return 100.0
    if "Internet" in plan_type:
        return 60.0
    return 40.0

def invoice_exists_for_month(db: Session, client_id: int, year: int, month: int) -> bool:
    # simple query
    rows = db.query(Invoice).filter(
        Invoice.client_id == client_id,
        Invoice.issue_date.year == year  # sqlalchemy doesn't support .year directly; use extract if necessary
    ).all()
    # fallback: do a loop and compare
    for r in rows:
        if r.issue_date.year == year and r.issue_date.month == month:
            return True
    return False

def generate_monthly_invoices_once():
    db = SessionLocal()
    try:
        hoy = datetime.utcnow()
        year, month = hoy.year, hoy.month
        clients = db.query(models.Client).all()
        created = 0
        for c in clients:
            # skip if plan_type missing
            if not c.plan_type:
                continue
            # check existing invoice for current month
            exists = db.query(Invoice).filter(
                Invoice.client_id == c.id,
                Invoice.issue_date.year == year,
                Invoice.issue_date.month == month
            ).first()
            if exists:
                continue
            amount = calcular_deuda_por_plan(c.plan_type)
            due_date = date(hoy.year, hoy.month, hoy.day)
            inv = models.Invoice(client_id=c.id, amount=amount, due_date=due_date)
            db.add(inv)
            created += 1
        db.commit()
        return created
    finally:
        db.close()
