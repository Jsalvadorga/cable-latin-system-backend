from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter(
    prefix="/api/v1/clients",
    tags=["clients"]
)

class Client(BaseModel):
    full_name: str
    document: str
    email: str
    phone_number: str
    service_address: str
    billing_address: str
    client_type: str
    plan_type: str

def get_connection():
    return psycopg2.connect(
        host="127.0.0.1",
        port="5432",
        dbname="cable_latin_db",
        user="postgres",
        password="MiNuevaClave123",
        cursor_factory=RealDictCursor
    )

# ✅ PUT para actualizar un cliente
@router.put("/{client_id}")
def update_client(client_id: int, client: Client):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE clients
            SET full_name = %s,
                document = %s,
                email = %s,
                phone_number = %s,
                service_address = %s,
                billing_address = %s,
                client_type = %s,
                plan_type = %s
            WHERE id = %s
            RETURNING id, full_name, document, email, phone_number, service_address, billing_address, client_type, plan_type;
        """, (
            client.full_name,
            client.document,
            client.email,
            client.phone_number,
            client.service_address,
            client.billing_address,
            client.client_type,
            client.plan_type,
            client_id
        ))

        updated = cur.fetchone()
        conn.commit()

        if not updated:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        # ✅ Devolver directamente el objeto actualizado (sin envoltorio "message")
        return updated

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar cliente: {str(e)}")
    finally:
        cur.close()
        conn.close()
