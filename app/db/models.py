# app/db/models.py
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base  # adapta la importación según tu estructura

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    document = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    service_address = Column(String, nullable=False)
    billing_address = Column(String, nullable=False)
    client_type = Column(String, nullable=False)
    plan_type = Column(String, nullable=True)  # <= agregado (puede ser NULL si no lo llenaste)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    invoices = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    issue_date = Column(Date, server_default=func.current_date())
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    client = relationship("Client", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    amount_paid = Column(Numeric(10,2), nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    payment_method = Column(String(50), default="Efectivo")
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    invoice = relationship("Invoice", back_populates="payments")
