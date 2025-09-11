# src/api/schemas/students.py
from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional

# Entrada (quando o professor cadastrar um novo aluno)
class StudentCreate(BaseModel):
    cpf: str
    name: str
    birth_date: date   # já vamos calcular idade depois a partir daqui
    sex: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

# Saída (quando devolvermos aluno ao front)
class StudentOut(BaseModel):
    id: int
    cpf: str
    name: str
    birth_date: date
    age: int
    sex: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
