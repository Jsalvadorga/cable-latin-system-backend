import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    """Devuelve una conexión activa a la base de datos."""
    db_url = os.getenv("DATABASE_URL")
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

# 🔹 Dependencia FastAPI para endpoints
def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
