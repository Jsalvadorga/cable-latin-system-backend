from pydantic import BaseModel, EmailStr


# ✅ Para registrar usuario
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


# ✅ Para devolver usuario al frontend
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    is_active: bool

    class Config:
        from_attributes = True  # reemplaza a orm_mode en Pydantic v2


# ✅ Para tokens de login
class Token(BaseModel):
    access_token: str
    token_type: str
