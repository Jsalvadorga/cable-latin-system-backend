# app/crud/crud_client.py
from sqlalchemy.orm import Session
from app.db import models
from app.schemas.client import ClienteCreate

def create_cliente(db: Session, cliente: ClienteCreate):
    payload = cliente.model_dump() if hasattr(cliente, "model_dump") else cliente.dict()
    db_cliente = models.Cliente(**payload)
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

def get_clientes(db: Session):
    return db.query(models.Cliente).all()

def get_cliente(db: Session, client_id: int):
    return db.query(models.Cliente).filter(models.Cliente.id == client_id).first()

def update_cliente(db: Session, client_id: int, cliente: ClienteCreate):
    db_cliente = get_cliente(db, client_id)
    if not db_cliente:
        return None
    payload = cliente.model_dump() if hasattr(cliente, "model_dump") else cliente.dict()
    for key, value in payload.items():
        setattr(db_cliente, key, value)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

def delete_cliente(db: Session, client_id: int):
    db_cliente = get_cliente(db, client_id)
    if not db_cliente:
        return False
    db.delete(db_cliente)
    db.commit()
    return True
