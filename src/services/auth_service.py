from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.security import create_token, hash_password, verify_password
from src.core.settings import settings
from src.repositories import teacher_repository


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def register_teacher(db: Session, data: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "name": data["name"].strip(),
        "email": _normalize_email(data["email"]),
        "password_hash": hash_password(data["password"]),
        "is_active": True,
    }
    try:
        row = teacher_repository.insert_teacher(db, payload)
        db.commit()
        return dict(row)
    except IntegrityError as exc:
        db.rollback()
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", "") or ""
        if "email" in constraint.lower():
            raise HTTPException(status_code=409, detail="Email ja cadastrado.")
        raise HTTPException(status_code=400, detail="Nao foi possivel criar a conta.") from exc


def authenticate_teacher(db: Session, email: str, password: str) -> tuple[dict[str, Any], str]:
    row = teacher_repository.select_teacher_by_email(db, _normalize_email(email))
    if not row or not verify_password(password, row["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais invalidas.")

    teacher = dict(row)
    if not teacher["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta inativa.")

    token = create_token(
        {"sub": str(teacher["id"]), "email": teacher["email"]},
        settings.AUTH_SECRET_KEY,
        settings.AUTH_TOKEN_EXPIRES_MINUTES * 60,
    )
    teacher.pop("password_hash", None)
    return teacher, token


def get_teacher_by_id(db: Session, teacher_id: int) -> dict[str, Any] | None:
    row = teacher_repository.select_teacher_by_id(db, teacher_id)
    if not row:
        return None
    teacher = dict(row)
    teacher.pop("password_hash", None)
    return teacher
