from sqlalchemy.orm import Session
from app.db.session import engine, get_db
from app.db import models
from app.core.security import get_password_hash

# Usuario administrador que quieres crear
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def create_admin():
    # Crear sesión con la DB
    db = Session(bind=engine)

    # Verificar si ya existe
    existing_admin = db.query(models.User).filter(models.User.username == ADMIN_USERNAME).first()
    if existing_admin:
        print(f"Usuario '{ADMIN_USERNAME}' ya existe en la base de datos.")
        db.close()
        return

    # Crear nuevo admin con contraseña en hash
    hashed_password = get_password_hash(ADMIN_PASSWORD)
    new_admin = models.User(username=ADMIN_USERNAME, hashed_password=hashed_password)
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    db.close()
    print(f"Usuario admin creado: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")

if __name__ == "__main__":
    create_admin()
