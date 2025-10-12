from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import models
from app.schemas.service import ServiceCreate, ServiceUpdate

def get_services(db: Session, skip: int = 0, limit: int = 100) -> List[models.Service]:
    return db.query(models.Service).offset(skip).limit(limit).all()

def get_service(db: Session, service_id: int) -> Optional[models.Service]:
    return db.query(models.Service).filter(models.Service.id == service_id).first()

def create_service(db: Session, service: ServiceCreate) -> models.Service:
    db_service = models.Service(**service.dict())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def update_service(db: Session, service_id: int, service_update: ServiceUpdate) -> Optional[models.Service]:
    db_service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not db_service:
        return None
    for field, value in service_update.dict(exclude_unset=True).items():
        setattr(db_service, field, value)
    db.commit()
    db.refresh(db_service)
    return db_service

def delete_service(db: Session, service_id: int) -> Optional[models.Service]:
    db_service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if db_service:
        db.delete(db_service)
        db.commit()
    return db_service
