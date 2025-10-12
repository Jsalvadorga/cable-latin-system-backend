from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Configuración de conexión (puedes mover a .env luego)
DB_USER = "postgres"
DB_PASS = "MiNuevaClave123"
DB_HOST = "127.0.0.1"
DB_PORT = "5432"
DB_NAME = "cable_latin_db"

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
