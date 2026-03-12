from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def insert_student(db: Session, data: dict[str, Any]):
    return db.execute(text("""
        INSERT INTO students (cpf, name, birth_date, sex, email, phone)
        VALUES (:cpf, :name, :birth_date, :sex, :email, :phone)
        RETURNING id, cpf, name, birth_date, age, sex, email, phone, created_at;
    """), data).mappings().one()


def select_student_by_id(db: Session, student_id: int):
    return db.execute(text("""
        SELECT id, cpf, name, birth_date, age, sex, email, phone, created_at
        FROM students WHERE id = :id;
    """), {"id": student_id}).mappings().one_or_none()


def select_student_by_cpf(db: Session, cpf: str):
    return db.execute(text("""
        SELECT id, cpf, name, birth_date, age, sex, email, phone, created_at
        FROM students WHERE cpf = :cpf;
    """), {"cpf": cpf}).mappings().one_or_none()


def select_students(db: Session):
    return db.execute(text("""
        SELECT id, cpf, name, birth_date, age, sex, email, phone, created_at
        FROM students ORDER BY id DESC;
    """)).mappings().all()


def update_student_fields(db: Session, data: dict[str, Any]):
    return db.execute(text("""
        UPDATE students
        SET name       = COALESCE(:name, name),
            birth_date = COALESCE(:birth_date, birth_date),
            sex        = COALESCE(:sex, sex),
            email      = COALESCE(:email, email),
            phone      = COALESCE(:phone, phone)
        WHERE id = :id
        RETURNING id, cpf, name, birth_date, age, sex, email, phone, created_at;
    """), data).mappings().one()


def delete_student_by_id(db: Session, student_id: int) -> int:
    return db.execute(text("DELETE FROM students WHERE id = :id;"), {"id": student_id}).rowcount
