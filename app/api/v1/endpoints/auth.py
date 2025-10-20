from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os

router = APIRouter()

# -------------------------------------------------
# 🔹 Configuración de la conexión a la base de datos
# -------------------------------------------------
def get_connection():
    db_url = os.getenv('DATABASE_URL')
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
            host=DB_HOST, port=DB_PORT, database=DB_NAME,
            user=DB_USER, password=DB_PASS, cursor_factory=RealDictCursor
        )

# -------------------------------------------------
# 🔹 Modelo Pydantic
# -------------------------------------------------
class RegisterUser(BaseModel):
    username: str
    password: str

# -------------------------------------------------
# 🔹 Endpoint: Registrar usuario (SIEMPRE COMO LECTOR)
# -------------------------------------------------
@router.post("/register")
def register_user(user: RegisterUser):
    try:
        conn = get_connection()
        cur = conn.cursor()

        # 1. Verificar si el usuario ya existe
        cur.execute("SELECT * FROM users WHERE username = %s;", (user.username,))
        if cur.fetchone():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario ya existe")

        # 2. Insertar el nuevo usuario. El rol 'LECTOR' se asignará por defecto.
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id, rol;",
            (user.username, user.password)
        )
        new_user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        return {"id": new_user['id'], "username": user.username, "rol": new_user['rol'], "message": "Usuario creado correctamente"}
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

        # Verificar contraseña en texto plano
        if user["password"] != form_data.password:
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

        # Generar token simple (simulación)
        token = f"token-para-{user['username']}"

        cur.close()
        conn.close()

        # 👉 DEVOLVEMOS EL ROL JUNTO CON EL TOKEN
        return {
            "access_token": token,
            "token_type": "bearer",
            "username": user["username"],
            "rol": user["rol"] # <--- ¡Clave para el Frontend!
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el login: {e}")
