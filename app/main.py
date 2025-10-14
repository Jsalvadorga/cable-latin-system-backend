from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import psycopg2
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import users
from app.api.v1.endpoints import clients
from psycopg2.extras import RealDictCursor
import os
from passlib.context import CryptContext  # 🔹 Para hashear contraseñas

# -------------------------------------------------
# 🔹 Configuración inicial
# -------------------------------------------------
app = FastAPI(title="API de Clientes - Cable Latín System")

# -------------------------------------------------
# 🔹 Routers existentes
# -------------------------------------------------
app.include_router(clients.router, prefix="/api/v1/endpoint", tags=["clients"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])

# -------------------------------------------------
# 🔹 CORS para permitir Firebase frontend
# -------------------------------------------------
origins = [
    "https://cable-latin-system.web.app",
    "https://cable-latin-system.firebaseapp.com",
    "http://localhost:3000",  # si usabas React tradicional
    "http://localhost:5173",  # para Vite dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# 🔹 Conexión a la base de datos PostgreSQL
# -------------------------------------------------
def get_connection():
    db_url = os.getenv("DATABASE_URL")
    print("DATABASE_URL actual:", db_url)
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
# 🔹 Seguridad de contraseñas
# -------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str):
    return pwd_context.hash(password)

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
        cur.execute("SELECT * FROM clients WHERE id = %s;", (client_id,))
        cliente_creado = cur.fetchone()
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
# 🔹 Endpoint Login con usuarios reales de DB
# -------------------------------------------------
@app.post("/api/v1/auth/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=%s",
            (form_data.username,)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user or not verify_password(form_data.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )

        return {"access_token": f"jwt-token-for-{user['username']}", "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al autenticar usuario: {e}")

# -------------------------------------------------
# 🔹 Endpoint raíz
# -------------------------------------------------
@app.get("/")
def root():
    return {"message": "✅ API de Clientes y Usuarios de Cable Latín System funcionando correctamente, Sistema de Juanjo"}
