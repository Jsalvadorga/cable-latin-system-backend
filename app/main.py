from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import psycopg2
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import users
from app.api.v1.endpoints import clients
from app.api.v1.endpoints import invoices  # <-- Añadido
from app.api.v1.endpoints import payments
from psycopg2.extras import RealDictCursor
import os
from twilio.rest import Client as TwilioClient  # 🔹 Import Twilio

# -------------------------------------------------
# 🔹 Configuración inicial
# -------------------------------------------------
app = FastAPI(title="API de Clientes - Cable Latín System")

# ---------- Routers existentes ----------
app.include_router(clients.router, prefix="/api/v1/endpoint", tags=["clients"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/auth", tags=["Users"])

# ---------- Nuevo: Router de Invoices ----------
app.include_router(invoices.router, prefix="/api/v1", tags=["invoices"])
app.include_router(payments.router, prefix="/api/v1", tags=["payments"])

# -------------------------------------------------
# 🔹 CORS
# -------------------------------------------------
origins = [
    "https://cable-latin-system.web.app",  # tu frontend de Firebase
    "http://localhost:5173",  # para desarrollo local (Vite)
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,   # dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],     # GET, POST, PUT, DELETE
    allow_headers=["*"],
)

# -------------------------------------------------
# 🔹 Conexión a la base de datos PostgreSQL
# -------------------------------------------------
def get_connection():
    """Devuelve una conexión activa a la base de datos (Render o local)."""
    db_url = os.getenv("DATABASE_URL")
    print("DATABASE_URL actual:", db_url)  # 🔹 Log temporal para Render

    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    else:
        DB_HOST = "127.0.0.1"
        DB_PORT = "5432"
        DB_NAME = "cable_latin_db"
        DB_USER = "postgres"
        DB_PASS = "MiNuevaClave123"
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )

# -------------------------------------------------
# 🔹 Crear tabla de clientes (si no existe)
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

        # 🔹 Nuevo: devolver el cliente completo recién creado
        cur.execute("SELECT * FROM clients WHERE id = %s;", (client_id,))
        cliente_creado = cur.fetchone()

        # -----------------------------
        # 🔹 ENVÍO DE MENSAJE WHATSAPP
        # -----------------------------
        try:
            TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
            TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
            TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")  # Formato: whatsapp:+14155238886

            twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

            mensaje = (
                f"¡Hola {cliente_creado['full_name']}! 🎉\n"
                "Bienvenido a Cable Latín System.\n"
                "Tu primer pago será el mismo día del próximo mes, y luego se facturará mensualmente."
            )

            twilio_client.messages.create(
                body=mensaje,
                from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
                to=f"whatsapp:{cliente_creado['phone_number']}"
            )

            print(f"✅ Mensaje de bienvenida enviado a {cliente_creado['phone_number']}")
        except Exception as e:
            print(f"⚠️ No se pudo enviar mensaje WhatsApp: {e}")

        cur.close()
        conn.close()
        return {"message": "Cliente creado correctamente", "client": cliente_creado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/clients/{client_id}")
def update_client(client_id: int, client: Client):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM clients WHERE id = %s;", (client_id,))
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        cur.execute("""
            UPDATE clients
            SET full_name=%s, document=%s, email=%s, phone_number=%s,
                service_address=%s, billing_address=%s, client_type=%s, plan_type=%s
            WHERE id=%s RETURNING *;
        """, (
            client.full_name, client.document, client.email, client.phone_number,
            client.service_address, client.billing_address, client.client_type, client.plan_type, client_id
        ))

        updated_client = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"message": "Cliente actualizado correctamente", "client": updated_client}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo actualizar el cliente: {e}")


@app.delete("/api/v1/clients/{client_id}")
def delete_client(client_id: int):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM clients WHERE id = %s;", (client_id,))
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        cur.execute("DELETE FROM clients WHERE id = %s;", (client_id,))
        conn.commit()
        cur.close()
        conn.close()
        return {"message": "Cliente eliminado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------
# 🔹 NUEVO: Endpoints USUARIOS
# -------------------------------------------------
class UserDB(BaseModel):
    username: str
    password: str

@app.get("/api/v1/users")
def get_users():
    """Obtiene todos los usuarios registrados"""
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
    """Elimina un usuario por su ID"""
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
# 🔹 Endpoint Login temporal
# -------------------------------------------------
@app.post("/api/v1/auth/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "admin" and form_data.password == "1234":
        return {"access_token": "fake-jwt-token-for-admin", "token_type": "bearer"}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")


# -------------------------------------------------
# 🔹 Endpoint raíz
# -------------------------------------------------
@app.get("/")
def root():
    return {"message": "✅ API de Clientes y Usuarios de Cable Latín System funcionando correctamente, sistema juanjo"}
