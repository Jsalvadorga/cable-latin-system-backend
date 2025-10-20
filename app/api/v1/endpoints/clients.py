from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional
import os

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

# ✅ GET: Listar clientes con todos los datos
@router.get("/")
def get_clients():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM clients ORDER BY created_at DESC;")
        return cur.fetchall()
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

# ✅ PUT: Actualizar deuda, estado y vencimiento desde tu Facturacion.tsx
@router.put("/{client_id}")
def update_client(client_id: int, client: ClientUpdate):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE clients
            SET activo = COALESCE(%s, activo),
                deuda = COALESCE(%s, deuda),
                vencimiento = COALESCE(%s, vencimiento),
                last_payment = COALESCE(%s, last_payment)
            WHERE id = %s
            RETURNING *;
        """, (
            client.activo,
            client.deuda,
            client.vencimiento,
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
