# app/routes/services.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, crud

router = APIRouter()

@router.post("/", response_model=schemas.ServiceResponse)
def create_service(service: schemas.ServiceCreate, db: Session = Depends(get_db)):
    return crud.create_service(db, service)

@router.get("/", response_model=list[schemas.ServiceResponse])
def read_services(db: Session = Depends(get_db)):
    return crud.get_services(db)

@router.get("/{service_id}", response_model=schemas.ServiceResponse)
def read_service(service_id: int, db: Session = Depends(get_db)):
    db_service = crud.get_service(db, service_id)
    if db_service is None:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return db_service

@router.put("/{service_id}", response_model=schemas.ServiceResponse)
def update_service(service_id: int, service: schemas.ServiceUpdate, db: Session = Depends(get_db)):
    db_service = crud.update_service(db, service_id, service)
    if db_service is None:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return db_service

@router.delete("/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db)):
    db_service = crud.delete_service(db, service_id)
    if db_service is None:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return {"detail": "Servicio eliminado"}
