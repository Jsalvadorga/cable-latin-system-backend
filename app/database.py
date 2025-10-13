import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv  # ✅ Agregado

# -----------------------------------------------
# 🔹 Cargar variables desde .env (solo localmente)
# -----------------------------------------------
load_dotenv()

# -----------------------------------------------
# 🔹 Leer la variable de entorno DATABASE_URL
# -----------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

# -----------------------------------------------
# 🔹 Configuración por defecto (solo si no existe DATABASE_URL)
# -----------------------------------------------
if not DATABASE_URL:
    DB_HOST = "127.0.0.1"
    DB_PORT = "5432"
    DB_NAME = "cable_latin_db"
    DB_USER = "postgres"
    DB_PASS = "MiNuevaClave123"
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# -----------------------------------------------
# ✅ Ajuste para Render (evita error SSL o mal formato en SQLAlchemy)
# -----------------------------------------------
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# -----------------------------------------------
# 🔹 Crear conexión con SQLAlchemy
# -----------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"} if "render.com" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# -----------------------------------------------
# 🔹 Función para obtener sesión de DB
# -----------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
