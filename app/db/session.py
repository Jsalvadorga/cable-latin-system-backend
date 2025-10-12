from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 🧩 Cambia los valores según tu configuración real de PostgreSQL
DATABASE_URL = "postgresql+psycopg2://postgres:MiNuevaClave123@127.0.0.1:5432/cable_latin_db"

# 🔗 Crear el motor de conexión
engine = create_engine(DATABASE_URL)

# ⚙️ Configurar sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 🧩 Dependencia para inyección en los endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
