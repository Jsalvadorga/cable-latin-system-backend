from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List
import os
from twilio.rest import Client as TwilioClient  # 🔹 Import Twilio

router = APIRouter(
    prefix="/api/v1/clients",
    tags=["clients"]
)

# -------------------------------
# Modelo de cliente
# -------------------------------
class Client(BaseModel):
    full_name: str
    document: str
    email: str
    phone_number: str
    service_address: str
    billing_address: str
    client_type: str
    plan_type: str

# -------------------------------
# Conexión a la base de datos
# -------------------------------
def get_connection():
    return psycopg2.connect(
        host="127.0.0.1",  # Cambia a tu host de Render si corresponde
        port="5432",
        dbname="cable_latin_db",
        user="postgres",
        password="MiNuevaClave123",
        cursor_factory=RealDictCursor
    )

# -------------------------------
# GET: Listar clientes
# -------------------------------
@router.get("/", response_model=List[Client])
def get_clients():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM clients ORDER BY created_at DESC;")
        clients = cur.fetchall()
        return clients
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener clientes: {str(e)}")
    finally:
        cur.close()
        conn.close()

# -------------------------------
# POST: Crear cliente
# -------------------------------
@router.post("/")
def create_client(client: Client):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO clients 
            (full_name, document, email, phone_number, service_address, billing_address, client_type, plan_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, full_name, document, email, phone_number, service_address, billing_address, client_type, plan_type;
        """, (
            client.full_name,
            client.document,
            client.email,
            client.phone_number,
            client.service_address,
            client.billing_address,
            client.client_type,
            client.plan_type
        ))

        new_client = cur.fetchone()
        conn.commit()

        # 🔹 Enviar mensaje WhatsApp usando Twilio Sandbox
        try:
            TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
            TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
            TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")  # sandbox: whatsapp:+14155238886

            twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

            # Formatear número del cliente con código de país si no tiene
            phone_to = new_client["phone_number"]
            if not phone_to.startswith("+"):
                phone_to = "+51" + phone_to  # Cambia +51 si tu país es otro

            mensaje = (
                f"¡Hola {new_client['full_name']}! 🎉\n"
                "Bienvenido a Cable Latín System.\n"
                "Tu primer pago será el mismo día del próximo mes, y luego se facturará mensualmente."
            )

            twilio_client.messages.create(
                body=mensaje,
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=f"whatsapp:{phone_to}"
            )

            print(f"✅ Mensaje de bienvenida enviado a {phone_to}")

        except Exception as e:
            print(f"⚠️ No se pudo enviar mensaje WhatsApp: {e}")

        return {"client": new_client}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear cliente: {str(e)}")
    finally:
        cur.close()
        conn.close()

# -------------------------------
# PUT: Actualizar cliente
# -------------------------------
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

        return {"client": updated}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar cliente: {str(e)}")
    finally:
        cur.close()
        conn.close()

# -------------------------------
# DELETE: Eliminar cliente
# -------------------------------
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
        raise HTTPException(status_code=500, detail=f"Error al eliminar cliente: {str(e)}")
    finally:
        cur.close()
        conn.close()
