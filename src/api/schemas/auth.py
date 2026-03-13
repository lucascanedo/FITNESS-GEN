from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer


class TeacherRegister(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TeacherLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TeacherOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at")
    def serialize_dates(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M")


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    teacher: TeacherOut
