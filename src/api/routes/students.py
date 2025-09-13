# src/api/routes/students.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from src.db.database import get_db
from src.api.schemas.students import StudentCreate, StudentOut, StudentUpdate

router = APIRouter(prefix="/students", tags=["students"])

# --------------------------
# Helpers
# --------------------------
def _normalize_cpf(cpf: str) -> str:
    return cpf.replace(".", "").replace("-", "")

def _get_student_by_id_or_cpf(db: Session, id: int | None, cpf: str | None):
    if id is None and cpf is None:
        raise HTTPException(status_code=400, detail="Informe id ou cpf.")
    if id is not None:
        row = db.execute(text("SELECT * FROM students WHERE id = :id;"),
                         {"id": id}).mappings().one_or_none()
    else:
        row = db.execute(text("SELECT * FROM students WHERE cpf = :cpf;"),
                         {"cpf": _normalize_cpf(cpf)}).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return row

def _map_unique_error(e: IntegrityError) -> None:
    pgcode = getattr(getattr(e, "orig", None), "pgcode", None)
    constraint = getattr(getattr(e, "orig", None), "diag", None)
    constraint = getattr(constraint, "constraint_name", "") if constraint else ""
    if pgcode == "23505":
        if "students_cpf_key" in constraint:
            raise HTTPException(status_code=409, detail="CPF já cadastrado.")
        if "students_name_key" in constraint:
            raise HTTPException(status_code=409, detail="Nome já cadastrado.")
        raise HTTPException(status_code=409, detail="Violação de unicidade.")

# --------------------------
# Create
# --------------------------
@router.post("/", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
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
        _map_unique_error(e)
        raise HTTPException(status_code=400, detail="Erro de integridade ao criar aluno.")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro interno ao criar aluno.")

# --------------------------
# Read (list + by id + lookup)
# --------------------------
@router.get("/", response_model=List[StudentOut])
def list_students(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT id, cpf, name, birth_date, age, sex, email, phone, created_at
        FROM students
        ORDER BY id DESC;
    """)).mappings().all()
    return [dict(r) for r in rows]

@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT id, cpf, name, birth_date, age, sex, email, phone, created_at
        FROM students
        WHERE id = :id;
    """), {"id": student_id}).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return dict(row)

@router.get("/lookup", response_model=StudentOut)
def lookup_student(
    id: Optional[int] = Query(None),
    cpf: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    if id is None and cpf is None:
        raise HTTPException(status_code=400, detail="Informe id ou cpf.")
    if id is not None:
        row = db.execute(text("""
            SELECT id, cpf, name, birth_date, age, sex, email, phone, created_at
            FROM students WHERE id = :id;
        """), {"id": id}).mappings().one_or_none()
    else:
        row = db.execute(text("""
            SELECT id, cpf, name, birth_date, age, sex, email, phone, created_at
            FROM students WHERE cpf = :cpf;
        """), {"cpf": _normalize_cpf(cpf)}).mappings().one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return dict(row)

# --------------------------
# Update (parcial) por id OU cpf
# --------------------------
@router.put("/update", response_model=StudentOut)
def update_student_by_id_or_cpf(
    payload: StudentUpdate,
    id: int | None = Query(default=None),
    cpf: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Atualiza usando id OU cpf (se ambos vierem, prioriza id).
    Edição parcial: envia só o que quer mudar.
    Não permite alterar CPF (mantemos o atual do banco).
    """
    current = _get_student_by_id_or_cpf(db, id, cpf)

    # apenas campos enviados (evita sobrescrever com None acidental)
    data = payload.model_dump(exclude_unset=True)

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
        """), {**data, "id": current["id"]}).mappings().one()
        db.commit()
        return dict(row)
    except IntegrityError as e:
        db.rollback()
        _map_unique_error(e)
        raise HTTPException(status_code=400, detail="Erro de integridade ao atualizar aluno.")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar aluno.")

# --------------------------
# Delete (por id OU cpf)
# --------------------------
@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_by_id_or_cpf(
    id: int | None = Query(default=None),
    cpf: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Deleta usando id OU cpf (se ambos vierem, prioriza id).
    ON DELETE CASCADE apaga medições/anamneses/planos vinculados.
    """
    current = _get_student_by_id_or_cpf(db, id, cpf)
    res = db.execute(text("DELETE FROM students WHERE id = :id;"), {"id": current["id"]})
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return
