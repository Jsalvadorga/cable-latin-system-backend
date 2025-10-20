from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.database import get_db
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter()

# ---------------------------
# Modelos
# ---------------------------
class InvoiceBase(BaseModel):
    client_id: int
    amount: float
    due_date: datetime

class PaymentCreate(BaseModel):
    invoice_id: int
    amount_paid: float
    payment_method: str = "Efectivo"
    notes: Optional[str] = None

# ---------------------------
# Obtener facturas
# ---------------------------
@router.get("/invoices")
def get_invoices(client_id: Optional[int] = None, db=Depends(get_db)):
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        if client_id:
            cursor.execute("SELECT * FROM invoices WHERE client_id = %s", (client_id,))
        else:
            cursor.execute("SELECT * FROM invoices")
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener facturas: {e}")

# ---------------------------
# Crear pago
# ---------------------------
@router.post("/payments")
def create_payment(payment: PaymentCreate, db=Depends(get_db)):
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)

        # Insertar pago
        cursor.execute("""
            INSERT INTO payments (invoice_id, amount_paid, payment_method, notes)
            VALUES (%s, %s, %s, %s) RETURNING id;
        """, (payment.invoice_id, payment.amount_paid, payment.payment_method, payment.notes))

        # Actualizar factura a "paid"
        cursor.execute("""
            UPDATE invoices
            SET status = 'paid', updated_at = NOW()
            WHERE id = %s;
        """, (payment.invoice_id,))

        db.commit()
        return {"message": "Pago registrado correctamente ✅"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear pago: {e}")

# ---------------------------
# Marcar factura como pagada
# ---------------------------
@router.put("/invoices/{invoice_id}/pay")
def mark_as_paid(invoice_id: int, db=Depends(get_db)):
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            UPDATE invoices
            SET status = 'paid', updated_at = NOW()
            WHERE id = %s
        """, (invoice_id,))
        db.commit()
        return {"message": "Factura marcada como pagada ✅"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al marcar factura como pagada: {e}")
