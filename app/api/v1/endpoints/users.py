from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Router
router = APIRouter()

# -------------------------------------------------
# 🔹 Conexión dinámica (Render o local)
# -------------------------------------------------
def get_connection():
    db_url = os.getenv("DATABASE_URL")

    if db_url:
        # Render usa 'postgres://' pero psycopg2 requiere 'postgresql://'
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    else:
        # Config local por si lo ejecutas desde tu PC
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
# 🔹 Modelo Pydantic (para crear usuarios)
# -------------------------------------------------
class User(BaseModel):
    username: str
    password: str

# -------------------------------------------------
# 🔹 Listar todos los usuarios
# -------------------------------------------------
@router.get("/users")
def get_users():
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Incluye también la fecha de creación
        cur.execute("SELECT id, username, created_at FROM users ORDER BY id ASC;")
        users = cur.fetchall()
        cur.close()
        conn.close()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {e}")

# -------------------------------------------------
# 🔹 Eliminar usuario
# -------------------------------------------------
@router.delete("/users/{username}")
def delete_user(username: str):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username = %s;", (username,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        cur.execute("DELETE FROM users WHERE username = %s;", (username,))
        conn.commit()
        cur.close()
        conn.close()
        return {"message": f"✅ Usuario '{username}' eliminado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {e}")

# -------------------------------------------------
# 🔹 Crear usuario
# -------------------------------------------------
@router.post("/register")
def register_user(user: User):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username = %s;", (user.username,))
        existing = cur.fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="El usuario ya existe")

        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id, created_at;",
            (user.username, user.password)
        )
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {
            "id": result["id"],
            "username": user.username,
            "created_at": result["created_at"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario: {e}")
