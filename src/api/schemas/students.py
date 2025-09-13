# src/api/schemas/students.py
from pydantic import BaseModel, EmailStr, field_validator, field_serializer
from datetime import date, datetime
from typing import Optional
import re

# Entrada (quando o professor cadastrar um novo aluno)
class StudentCreate(BaseModel):
    cpf: str
    name: str
    birth_date: date   # já vamos calcular idade depois a partir daqui
    sex: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    # Validação de CPF
    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        # remove pontuação
        cpf = re.sub(r"\D", "", v)
        # checa tamanho e se não são todos dígitos iguais (tipo 00000000000)
        if len(cpf) != 11 or len(set(cpf)) == 1:
            raise ValueError("CPF inválido")
        # checa dígitos verificadores
        for i in range(9, 11):
            soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(0, i))
            dig = ((soma * 10) % 11) % 10
            if dig != int(cpf[i]):
                raise ValueError("CPF inválido")
        return cpf

# Normaliza strings vazias -> None
    @field_validator("email", "phone", "sex")
    @classmethod
    def vazio_para_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class StudentUpdate(BaseModel):
    cpf: Optional[str] = None
    name: Optional[str] = None
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    # Validação de CPF
    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        # remove pontuação
        cpf = re.sub(r"\D", "", v)
        # checa tamanho e se não são todos dígitos iguais (tipo 00000000000)
        if len(cpf) != 11 or len(set(cpf)) == 1:
            raise ValueError("CPF inválido")
        # checa dígitos verificadores
        for i in range(9, 11):
            soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(0, i))
            dig = ((soma * 10) % 11) % 10
            if dig != int(cpf[i]):
                raise ValueError("CPF inválido")
        return cpf

    # Normaliza strings vazias -> None
    @field_validator("email", "phone", "sex")
    @classmethod
    def vazio_para_none(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v  
    


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

    @field_serializer("created_at")
    def _fmt_created_at(self, v: Optional[datetime]):
        return v.strftime("%Y-%m-%d %H:%M") if v else None
    class Config:
        orm_mode = True