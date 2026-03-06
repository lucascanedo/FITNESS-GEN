# src/services/student_service.py
from __future__ import annotations
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException


def _normalize_cpf(cpf: str) -> str:
    return cpf.replace(".", "").replace("-", "")


def create_student(db: Session, data: dict[str, Any]) -> dict[str, Any]:
    data = dict(data)
    if "cpf" in data and data["cpf"]:
        data["cpf"] = _normalize_cpf(str(data["cpf"]))
    stmt = text("""
        INSERT INTO students (cpf, name, birth_date, sex, email, phone)
        VALUES (:cpf, :name, :birth_date, :sex, :email, :phone)
        RETURNING id, cpf, name, birth_date, age, sex, email, phone, created_at;
    """)
    try:
        row = db.execute(stmt, data).mappings().one()
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
    row = db.execute(text("""
        SELECT id, cpf, name, birth_date, age, sex, email, phone, created_at
        FROM students WHERE id = :id;
    """), {"id": student_id}).mappings().one_or_none()
    return dict(row) if row else None


def get_student_by_cpf(db: Session, cpf: str) -> dict[str, Any] | None:
    row = db.execute(text("""
        SELECT id, cpf, name, birth_date, age, sex, email, phone, created_at
        FROM students WHERE cpf = :cpf;
    """), {"cpf": _normalize_cpf(cpf)}).mappings().one_or_none()
    return dict(row) if row else None


def list_students(db: Session) -> list[dict[str, Any]]:
    rows = db.execute(text("""
        SELECT id, cpf, name, birth_date, age, sex, email, phone, created_at
        FROM students ORDER BY id DESC;
    """)).mappings().all()
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
        row = db.execute(text("""
            UPDATE students
            SET name       = COALESCE(:name, name),
                birth_date = COALESCE(:birth_date, birth_date),
                sex        = COALESCE(:sex, sex),
                email      = COALESCE(:email, email),
                phone      = COALESCE(:phone, phone)
            WHERE id = :id
            RETURNING id, cpf, name, birth_date, age, sex, email, phone, created_at;
        """), data).mappings().one()
        db.commit()
        return dict(row)
    except IntegrityError as e:
        db.rollback()
        _raise_unique_error(e)
        raise


def delete_student(db: Session, student_id: int) -> bool:
    res = db.execute(text("DELETE FROM students WHERE id = :id;"), {"id": student_id})
    db.commit()
    return res.rowcount > 0
