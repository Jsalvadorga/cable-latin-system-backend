from sqlalchemy import Column, Integer, String
from app.database import Base

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
    plan_type = Column(String, nullable=False)
