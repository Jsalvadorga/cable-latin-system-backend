from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.main import get_connection  # Usamos tu función de conexión

router = APIRouter()

# Modelos
class InvoiceBase(BaseModel):
    client_id: int
    amount: float
    due_date: str

class PaymentCreate(BaseModel):
    invoice_id: int
    amount_paid: float
    payment_method: str = "Efectivo"
    notes: Optional[str] = None

# Obtener facturas
@router.get("/invoices")
def get_invoices(client_id: Optional[int] = None):
    try:
        conn = get_connection()
        cur = conn.cursor()
        if client_id:
            cur.execute("SELECT * FROM invoices WHERE client_id = %s ORDER BY id ASC", (client_id,))
        else:
            cur.execute("SELECT * FROM invoices ORDER BY id ASC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener facturas: {e}")

# Registrar pago
@router.post("/payments")
def create_payment(payment: PaymentCreate):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO payments (invoice_id, amount_paid, payment_method, notes) VALUES (%s, %s, %s, %s) RETURNING id;",
            (payment.invoice_id, payment.amount_paid, payment.payment_method, payment.notes),
        )
        payment_id = cur.fetchone()["id"]
        cur.execute(
            "UPDATE invoices SET status = 'paid', updated_at = NOW() WHERE id = %s;",
            (payment.invoice_id,)
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"message": "Pago registrado correctamente", "payment_id": payment_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar pago: {e}")

# Marcar factura como pagada
@router.put("/invoices/{invoice_id}/pay")
def mark_as_paid(invoice_id: int):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE invoices SET status = 'paid', updated_at = NOW() WHERE id = %s;",
            (invoice_id,)
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"message": "Factura marcada como pagada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar factura: {e}")
