from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db  # Debe devolver conexión psycopg2 con yield

router = APIRouter()

# ----------------------
# MODELOS
# ----------------------
class InvoiceBase(BaseModel):
    client_id: int
    amount: float
    due_date: datetime

class PaymentCreate(BaseModel):
    invoice_id: int
    amount_paid: float
    payment_method: str = "Efectivo"
    notes: Optional[str] = None

# ----------------------
# OBTENER FACTURAS
# ----------------------
@router.get("/invoices")
def get_invoices(client_id: Optional[int] = None, db=Depends(get_db)):
    try:
        cursor = db.cursor()
        if client_id:
            cursor.execute("SELECT * FROM invoices WHERE client_id = %s ORDER BY id ASC", (client_id,))
        else:
            cursor.execute("SELECT * FROM invoices ORDER BY id ASC")
        rows = cursor.fetchall()
        cursor.close()
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener facturas: {e}")

# ----------------------
# REGISTRAR PAGO
# ----------------------
@router.post("/payments")
def create_payment(payment: PaymentCreate, db=Depends(get_db)):
    try:
        cursor = db.cursor()

        # Insertar pago
        cursor.execute("""
            INSERT INTO payments (invoice_id, amount_paid, payment_method, notes, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id;
        """, (payment.invoice_id, payment.amount_paid, payment.payment_method, payment.notes))
        payment_id = cursor.fetchone()["id"]

        # Actualizar factura
        cursor.execute("""
            UPDATE invoices
            SET status = 'paid', updated_at = NOW()
            WHERE id = %s
        """, (payment.invoice_id,))

        db.commit()
        cursor.close()
        return {"message": "Pago registrado correctamente ✅", "payment_id": payment_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar pago: {e}")

# ----------------------
# MARCAR FACTURA COMO PAGADA
# ----------------------
@router.put("/invoices/{invoice_id}/pay")
def mark_as_paid(invoice_id: int, db=Depends(get_db)):
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE invoices
            SET status = 'paid', updated_at = NOW()
            WHERE id = %s
        """, (invoice_id,))
        db.commit()
        cursor.close()
        return {"message": "Factura marcada como pagada ✅"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al marcar factura como pagada: {e}")
