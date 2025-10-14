from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt

# -------------------------------------------------
# 🔹 Configuración
# -------------------------------------------------
app = FastAPI(title="API de Clientes - Cable Latín System")

origins = [
    "https://cable-latin-system.web.app",
    "https://cable-latin-system.firebaseapp.com",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# 🔹 Seguridad de contraseñas y JWT
# -------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "clave_jwt_ultra_secreta")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# -------------------------------------------------
# 🔹 Conexión PostgreSQL
# -------------------------------------------------
def get_connection():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    else:
        DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
        DB_PORT = os.getenv("DB_PORT", "5432")
        DB_NAME = os.getenv("DB_NAME", "cable_latin_db")
        DB_USER = os.getenv("DB_USER", "postgres")
        DB_PASS = os.getenv("DB_PASS", "MiNuevaClave123")
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )

# -------------------------------------------------
# 🔹 Crear tablas si no existen
# -------------------------------------------------
def create_tables():
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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(200) NOT NULL,
                full_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tablas 'clients' y 'users' verificadas o creadas correctamente.")
    except Exception as e:
        print(f"⚠️ Error al crear/verificar tablas: {e}")

create_tables()

# -------------------------------------------------
# 🔹 Modelos
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

class User(BaseModel):
    username: str
    password: str
    full_name: str = ""

# -------------------------------------------------
# 🔹 Dependencia de usuario actual con JWT
# -------------------------------------------------
def get_current_user(token: str = Depends(oauth2_scheme)):
    username = decode_access_token(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=%s;", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user

# -------------------------------------------------
# 🔹 CRUD CLIENTES (requiere token)
# -------------------------------------------------
@app.get("/api/v1/clients", response_model=List[Client])
def get_clients(current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients ORDER BY id ASC;")
    clients = cur.fetchall()
    cur.close()
    conn.close()
    return clients

@app.post("/api/v1/clients")
def create_client(client: Client, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO clients (full_name, document, email, phone_number, service_address, billing_address, client_type, plan_type)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;
    """, (
        client.full_name, client.document, client.email, client.phone_number,
        client.service_address, client.billing_address, client.client_type, client.plan_type
    ))
    client_id = cur.fetchone()["id"]
    conn.commit()
    cur.execute("SELECT * FROM clients WHERE id=%s;", (client_id,))
    created = cur.fetchone()
    cur.close()
    conn.close()
    return {"message": "Cliente creado correctamente", "client": created}

@app.put("/api/v1/clients/{client_id}")
def update_client(client_id: int, client: Client, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE id=%s;", (client_id,))
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
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Cliente actualizado correctamente", "client": updated}

@app.delete("/api/v1/clients/{client_id}")
def delete_client(client_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE id=%s;", (client_id,))
    existing = cur.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    cur.execute("DELETE FROM clients WHERE id=%s;", (client_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Cliente eliminado correctamente"}

# -------------------------------------------------
# 🔹 Usuarios y login JWT
# -------------------------------------------------
@app.post("/api/v1/users")
def create_user(user: User):
    conn = get_connection()
    cur = conn.cursor()
    hashed = hash_password(user.password)
    cur.execute("INSERT INTO users (username, password, full_name) VALUES (%s,%s,%s) RETURNING id;",
                (user.username, hashed, user.full_name))
    user_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Usuario creado correctamente", "user_id": user_id}

@app.post("/api/v1/auth/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=%s;", (form_data.username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    token = create_access_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

# -------------------------------------------------
# 🔹 Endpoint raíz
# -------------------------------------------------
@app.get("/")
def root():
    return {"message": "✅ API de Clientes y Usuarios funcionando con JWT"}
