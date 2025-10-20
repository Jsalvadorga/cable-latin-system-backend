from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional
from datetime import date, datetime

router = APIRouter(
    prefix="/api/v1/clients",
    tags=["clients"]
)

# ✅ Datos de Render (NO localhost)
def get_connection():
    return psycopg2.connect(
        host="dpg-d3mloifdiees73caejgg-a.oregon-postgres.render.com",
        dbname="cable_latin_db",
        user="cable_latin_db_user",
        password="72Ix3JB1VHHviXjk99SjBXU2X0G24kwb",
        port="5432",
        cursor_factory=RealDictCursor
    )

# ✅ Modelo para crear cliente
class ClientCreate(BaseModel):
    full_name: str
    document: str
    email: str
    phone_number: str
    service_address: str
    billing_address: str
    client_type: str
    plan_type: str

# ✅ Modelo para actualizar (deuda, estado, vencimiento)
class ClientUpdate(BaseModel):
    activo: Optional[bool] = None
    deuda: Optional[float] = None
    vencimiento: Optional[str] = None
    last_payment: Optional[str] = None

# ✅ GET: Listar clientes con todos los datos y calcular deuda y estado
@router.get("/")
def get_clients():
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Traer clientes
        cur.execute("SELECT * FROM clients ORDER BY created_at DESC;")
        clientes = cur.fetchall()

        # Traer facturas pendientes
        cur.execute("""
            SELECT client_id, SUM(amount) AS deuda_total, MAX(due_date) AS vencimiento 
            FROM invoices 
            WHERE status='pending' 
            GROUP BY client_id;
        """)
        facturas = cur.fetchall()
        facturas_dict = {f["client_id"]: f for f in facturas}

        # Ajustar deuda y estado
        today = date.today()
        for cliente in clientes:
            f = facturas_dict.get(cliente["id"])
            deuda = float(f["deuda_total"]) if f and f["deuda_total"] else 0
            vencimiento = datetime.strptime(f["vencimiento"], "%Y-%m-%d").date() if f and f["vencimiento"] else None

            cliente["deuda"] = deuda
            cliente["vencimiento"] = vencimiento

            # Determinar estado
            if deuda > 0 and vencimiento and vencimiento < today:
                cliente["activo"] = False
            else:
                cliente["activo"] = True

        return clientes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener clientes: {e}")
    finally:
        cur.close()
        conn.close()

# ✅ POST: Crear cliente
@router.post("/")
def create_client(client: ClientCreate):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO clients 
            (full_name, document, email, phone_number, service_address, billing_address, client_type, plan_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
        """, (
            client.full_name, client.document, client.email, client.phone_number,
            client.service_address, client.billing_address, client.client_type, client.plan_type
        ))
        conn.commit()
        return cur.fetchone()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear cliente: {e}")
    finally:
        cur.close()
        conn.close()

# ✅ PUT: Actualizar deuda y estado automáticamente
@router.put("/{client_id}")
def update_client(client_id: int, client: ClientUpdate):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Obtener deuda pendiente y vencimiento
        cur.execute("""
            SELECT SUM(amount) AS deuda_total, MAX(due_date) AS vencimiento
            FROM invoices
            WHERE client_id=%s AND status='pending';
        """, (client_id,))
        deuda_res = cur.fetchone()
        deuda_pendiente = float(deuda_res["deuda_total"]) if deuda_res["deuda_total"] else 0
        vencimiento = deuda_res["vencimiento"]

        today = date.today()
        activo_final = client.activo if client.activo is not None else (deuda_pendiente == 0 or (vencimiento and vencimiento >= today))

        cur.execute("""
            UPDATE clients
            SET activo = %s,
                deuda = COALESCE(%s, deuda),
                vencimiento = COALESCE(%s, vencimiento),
                last_payment = COALESCE(%s, last_payment)
            WHERE id = %s
            RETURNING *;
        """, (
            activo_final,
            client.deuda,
            client.vencimiento or vencimiento,
            client.last_payment,
            client_id
        ))
        updated = cur.fetchone()
        conn.commit()

        if not updated:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        return {"message": "Cliente actualizado", "client": updated}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar cliente: {e}")
    finally:
        cur.close()
        conn.close()

# ✅ DELETE: Eliminar cliente
@router.delete("/{client_id}")
def delete_client(client_id: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM clients WHERE id = %s RETURNING id;", (client_id,))
        deleted = cur.fetchone()
        conn.commit()

        if not deleted:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        return {"message": "Cliente eliminado correctamente"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar cliente: {e}")
    finally:
        cur.close()
        conn.close()
