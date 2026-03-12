# src/services/student_service.py
from __future__ import annotations
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException

from src.repositories import student_repository


def _normalize_cpf(cpf: str) -> str:
    return cpf.replace(".", "").replace("-", "")


def create_student(db: Session, data: dict[str, Any]) -> dict[str, Any]:
    data = dict(data)
    if "cpf" in data and data["cpf"]:
        data["cpf"] = _normalize_cpf(str(data["cpf"]))
    try:
        row = student_repository.insert_student(db, data)
        db.commit()
        return dict(row)
    except IntegrityError as e:
        db.rollback()
        _raise_unique_error(e)
        raise


def _raise_unique_error(e: IntegrityError) -> None:
    pgcode = getattr(getattr(e, "orig", None), "pgcode", None)
    diag = getattr(getattr(e, "orig", None), "diag", None)
    constraint = getattr(diag, "constraint_name", "") if diag else ""
    if pgcode == "23505":
        if "students_cpf_key" in constraint or "cpf" in constraint.lower():
            raise HTTPException(status_code=409, detail="CPF já cadastrado.")
        if "students_email_key" in constraint or "email" in constraint.lower():
            raise HTTPException(status_code=409, detail="Email já cadastrado.")
        raise HTTPException(status_code=409, detail="Violação de unicidade.")
    raise HTTPException(status_code=400, detail="Erro de integridade ao criar aluno.")


def get_student_by_id(db: Session, student_id: int) -> dict[str, Any] | None:
    row = student_repository.select_student_by_id(db, student_id)
    return dict(row) if row else None


def get_student_by_cpf(db: Session, cpf: str) -> dict[str, Any] | None:
    row = student_repository.select_student_by_cpf(db, _normalize_cpf(cpf))
    return dict(row) if row else None


def list_students(db: Session) -> list[dict[str, Any]]:
    rows = student_repository.select_students(db)
    return [dict(r) for r in rows]


def update_student(db: Session, student_id: int, data: dict[str, Any]) -> dict[str, Any]:
    data = {k: v for k, v in data.items() if v is not None}
    if not data:
        student = get_student_by_id(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return student
    data["id"] = student_id
    try:
        row = student_repository.update_student_fields(db, data)
        db.commit()
        return dict(row)
    except IntegrityError as e:
        db.rollback()
        _raise_unique_error(e)
        raise


def delete_student(db: Session, student_id: int) -> bool:
    rowcount = student_repository.delete_student_by_id(db, student_id)
    db.commit()
    return rowcount > 0
