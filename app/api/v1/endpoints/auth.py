from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import os

router = APIRouter()

# -------------------------------------------------
# 🔹 Configuración de la conexión a la base de datos
# -------------------------------------------------
def get_connection():
    db_url = os.getenv('DATABASE_URL')

    if db_url:
        # Render usa 'postgres://' pero psycopg2 requiere 'postgresql://'
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
# 🔹 Modelo Pydantic para registrar usuarios
# -------------------------------------------------
class RegisterUser(BaseModel):
    username: str
    password: str

# -------------------------------------------------
# 🔹 Crear tabla de usuarios si no existe (con 'rol')
# -------------------------------------------------
def create_users_table():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                rol VARCHAR(20) DEFAULT 'USER'
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tabla 'users' verificada o creada correctamente.")
    except Exception as e:
        print(f"⚠️ Error al crear la tabla 'users': {e}")

create_users_table()

# -------------------------------------------------
# 🔹 Endpoint: Registrar usuario
# -------------------------------------------------
@router.post("/register")
def register_user(user: RegisterUser):
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Verificar si ya existe
        cur.execute("SELECT * FROM users WHERE username = %s;", (user.username,))
        existing_user = cur.fetchone()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario ya existe"
            )

        # Encriptar contraseña
        hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Asignar rol: ADMIN solo si el username es 'administrador'
        rol = "ADMIN" if user.username.lower() == "administrador" else "USER"

        cur.execute("INSERT INTO users (username, password, rol) VALUES (%s, %s, %s);",
                    (user.username, hashed_pw, rol))
        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Usuario creado correctamente", "rol": rol}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario: {e}")

# -------------------------------------------------
# 🔹 Endpoint: Login de usuario
# -------------------------------------------------
@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username = %s;", (form_data.username,))
        user = cur.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")

        # Verificar contraseña
        if not bcrypt.checkpw(form_data.password.encode("utf-8"), user["password"].encode("utf-8")):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

        # Token simple (simulación)
        token = f"token-{user['username']}"

        cur.close()
        conn.close()

        # ✅ Devuelve también el rol
        return {
            "access_token": token,
            "token_type": "bearer",
            "username": user["username"],
            "rol": user.get("rol", "USER")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el login: {e}")
