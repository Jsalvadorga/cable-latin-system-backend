from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import psycopg2
from datetime import datetime
from app.config.database import get_db  # Asegúrate de tener esta función de conexión

router = APIRouter()

# ✅ MODELOS (Request / Response)
class InvoiceBase(BaseModel):
    client_id: int
    amount: float
    due_date: datetime

class PaymentCreate(BaseModel):
    invoice_id: int
    amount_paid: float
    payment_method: str = "Efectivo"
    notes: Optional[str] = None

# ✅ OBTENER FACTURAS POR CLIENTE
@router.get("/invoices")
def get_invoices(client_id: Optional[int] = None, db=Depends(get_db)):
    cursor = db.cursor()
    if client_id:
        cursor.execute("SELECT * FROM invoices WHERE client_id = %s", (client_id,))
    else:
        cursor.execute("SELECT * FROM invoices")
    rows = cursor.fetchall()
    return rows

# ✅ REGISTRAR PAGO
@router.post("/payments")
def create_payment(payment: PaymentCreate, db=Depends(get_db)):
    cursor = db.cursor()

    # 1. Insertar pago
    cursor.execute("""
        INSERT INTO payments (invoice_id, amount_paid, payment_method, notes)
        VALUES (%s, %s, %s, %s) RETURNING id;
    """, (payment.invoice_id, payment.amount_paid, payment.payment_method, payment.notes))

    # 2. Actualizar factura a "paid"
    cursor.execute("""
        UPDATE invoices
        SET status = 'paid', updated_at = NOW()
        WHERE id = %s;
    """, (payment.invoice_id,))

    db.commit()
    return {"message": "Pago registrado correctamente ✅"}

# ✅ MARCAR FACTURA COMO PAGADA DESDE ID
@router.put("/invoices/{invoice_id}/pay")
def mark_as_paid(invoice_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        UPDATE invoices
        SET status = 'paid', updated_at = NOW()
        WHERE id = %s
    """, (invoice_id,))
    db.commit()

    return {"message": "Factura marcada como pagada ✅"}
