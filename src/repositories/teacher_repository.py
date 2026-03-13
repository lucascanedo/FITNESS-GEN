from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def insert_teacher(db: Session, data: dict[str, Any]):
    return db.execute(
        text(
            """
            INSERT INTO teachers (name, email, password_hash, is_active)
            VALUES (:name, :email, :password_hash, :is_active)
            RETURNING id, name, email, is_active, created_at, updated_at;
            """
        ),
        data,
    ).mappings().one()


def select_teacher_by_email(db: Session, email: str):
    return db.execute(
        text(
            """
            SELECT id, name, email, password_hash, is_active, created_at, updated_at
            FROM teachers
            WHERE email = :email;
            """
        ),
        {"email": email},
    ).mappings().one_or_none()


def select_teacher_by_id(db: Session, teacher_id: int):
    return db.execute(
        text(
            """
            SELECT id, name, email, password_hash, is_active, created_at, updated_at
            FROM teachers
            WHERE id = :id;
            """
        ),
        {"id": teacher_id},
    ).mappings().one_or_none()
