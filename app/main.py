from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from twilio.rest import Client as TwilioClient
import os

# 🔹 Routers existentes
from app.api.v1.endpoints import auth, users, clients, invoices, payments

# -------------------------------------------------
# 🔹 Configuración inicial
# -------------------------------------------------
app = FastAPI(title="API de Clientes - Cable Latín System")

# Routers originales
app.include_router(clients.router, prefix="/api/v1/endpoint", tags=["clients"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/auth", tags=["Users"])
app.include_router(invoices.router, prefix="/api/v1", tags=["Invoices"])
app.include_router(payments.router, prefix="/api/v1", tags=["Payments"])

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# 🔹 Conexión a la base de datos
# -------------------------------------------------
def get_connection():
    """Devuelve una conexión activa a PostgreSQL (local o Render)."""
    db_url = os.getenv("DATABASE_URL")
    print("DATABASE_URL actual:", db_url)

    try:
        if db_url:  # Para Render u otro servidor
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

        # Local
        return psycopg2.connect(
            host="127.0.0.1",
            port="5432",
            database="cable_latin_db",
            user="postgres",
            password="MiNuevaClave123",
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        print("❌ Error de conexión a DB:", e)
        raise

# -------------------------------------------------
# 🔹 Crear tabla clients si no existe
# -------------------------------------------------
def create_table_if_not_exists():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                document VARCHAR(20),
                email VARCHAR(100),
                phone_number VARCHAR(20),
                service_address TEXT,
                billing_address TEXT,
                client_type VARCHAR(50),
                plan_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tabla 'clients' verificada o creada correctamente.")
    except Exception as e:
        print(f"⚠️ Error al crear/verificar la tabla 'clients': {e}")

# Ejecutar al iniciar
create_table_if_not_exists()

# -------------------------------------------------
# 🔹 Modelo Cliente
# -------------------------------------------------
class Client(BaseModel):
    full_name: str
    document: str
    email: str
    phone_number: str
    service_address: str
    billing_address: str
    client_type: str
    plan_type: str

# -------------------------------------------------
# 🔹 Endpoints CLIENTES
# -------------------------------------------------
@app.get("/api/v1/clients")
def get_clients():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM clients ORDER BY id ASC")
        clients = cur.fetchall()
        cur.close()
        conn.close()
        return clients
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/clients")
def create_client(client: Client):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO clients (full_name, document, email, phone_number, service_address, billing_address, client_type, plan_type)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id;
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
        client_id = cur.fetchone()["id"]
        conn.commit()

        cur.execute("SELECT * FROM clients WHERE id = %s;", (client_id,))
        cliente_creado = cur.fetchone()

        # 🔹 Enviar WhatsApp
        try:
            TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
            TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
            TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

            twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

            mensaje = (
                f"¡Hola {cliente_creado['full_name']}! 🎉\n"
                "Bienvenido a Cable Latín System.\n"
                "Tu primer pago será el mismo día del próximo mes."
            )

            twilio_client.messages.create(
                body=mensaje,
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=f"whatsapp:{cliente_creado['phone_number']}"
            )
            print(f"✅ Mensaje enviado a {cliente_creado['phone_number']}")
        except Exception as e:
            print(f"⚠️ No se pudo enviar WhatsApp: {e}")

        cur.close()
        conn.close()
        return {"message": "Cliente creado correctamente", "client": cliente_creado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------
# 🔹 USERS
# -------------------------------------------------
class UserDB(BaseModel):
    username: str
    password: str

@app.get("/api/v1/users")
def get_users():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, created_at FROM users ORDER BY id ASC;")
        users = cur.fetchall()
        cur.close()
        conn.close()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {e}")

@app.delete("/api/v1/users/{user_id}")
def delete_user(user_id: int):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return {"message": f"Usuario '{user['username']}' eliminado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {e}")

# -------------------------------------------------
# 🔹 Login
# -------------------------------------------------
@app.post("/api/v1/auth/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "admin" and form_data.password == "1234":
        return {"access_token": "fake-jwt-token-for-admin", "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

# -------------------------------------------------
# 🔹 Endpoint raíz
# -------------------------------------------------
@app.get("/")
def root():
    return {"message": "✅ API de Clientes y Usuarios de Cable Latín System funcionando correctamente"}

