from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.api.deps.auth import get_current_teacher
from src.api.schemas.auth import AuthResponse, TeacherLogin, TeacherOut, TeacherRegister
from src.db.database import get_db
from src.services.auth_service import authenticate_teacher, register_teacher


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_teacher_route(payload: TeacherRegister, db: Session = Depends(get_db)):
    register_teacher(db, payload.model_dump())
    teacher_with_token, token = authenticate_teacher(db, payload.email, payload.password)
    return {"access_token": token, "teacher": teacher_with_token}


@router.post("/login", response_model=AuthResponse)
def login_teacher_route(payload: TeacherLogin, db: Session = Depends(get_db)):
    teacher, token = authenticate_teacher(db, payload.email, payload.password)
    return {"access_token": token, "teacher": teacher}


@router.get("/me", response_model=TeacherOut)
def get_me_route(current_teacher=Depends(get_current_teacher)):
    return current_teacher
