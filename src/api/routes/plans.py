# src/api/routes/plans.py
from __future__ import annotations

import json
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.db.database import get_db
from src.core.settings import settings
from src.api.schemas.plans import (
    PlanPreview, PlanCreate, PlanOut, PlanItem, PlanMeta
)

router = APIRouter(prefix="/plans", tags=["plans"])

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _fetch_assessment_bundle_strict(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    enforce_assessment_snapshot_match: bool = False,
) -> Dict[str, Any]:
    """
    Carrega student + assessment + measurement com validação forte:
      - assessment.student_id == student_id
      - measurement.student_id == student_id
      - (opcional) se assessment.measurement_id estiver setado e enforce=True,
        exige que assessment.measurement_id == measurement_id
    Retorna um bundle (dict) com dados do assessment + métricas da measurement.
    """
    a = db.execute(text("""
        SELECT
            a.id          AS assessment_id,
            a.student_id  AS assessment_student_id,
            s.id          AS student_id,
            s.name        AS student_name,
            s.sex         AS sex,
            s.age         AS age,
            a.measurement_id AS assessment_snapshot_mid,
            a.objectives, a.posture, a.injuries, a.restrictions, a.history,
            a.level, a.freq_per_week, a.session_time_min,
            a.case_notes, a.equipment, a.red_flags, a.readiness, a.periodization, a.status
        FROM assessments a
        JOIN students s ON s.id = a.student_id
        WHERE a.id = :aid;
    """), {"aid": assessment_id}).mappings().one_or_none()

    if a is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if a["student_id"] != student_id or a["assessment_student_id"] != student_id:
        raise HTTPException(
            status_code=400,
            detail=f"assessment_id={assessment_id} não pertence ao student_id={student_id}."
        )

    m = db.execute(text("""
        SELECT
            id, student_id, height_m, weight_kg, body_fat_percent, muscle_mass_kg,
            ROUND(bmi::numeric, 2) AS bmi
        FROM measurements
        WHERE id = :mid;
    """), {"mid": measurement_id}).mappings().one_or_none()

    if m is None:
        raise HTTPException(status_code=404, detail="Measurement not found")

    if m["student_id"] != student_id:
        raise HTTPException(
            status_code=400,
            detail=f"measurement_id={measurement_id} não pertence ao student_id={student_id}."
        )

    if enforce_assessment_snapshot_match and a["assessment_snapshot_mid"] is not None:
        if a["assessment_snapshot_mid"] != measurement_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Measurement informada difere da snapshot salva no assessment. "
                    "Se deseja usar outra measurement, desative a exigência "
                    "ou atualize o assessment."
                )
            )

    bundle = {
        "assessment_id": a["assessment_id"],
        "student_id": a["student_id"],
        "student_name": a["student_name"],
        "sex": a["sex"],
        "age": a["age"],
        "measurement_id": m["id"],
        "objectives": a["objectives"],
        "posture": a["posture"],
        "injuries": a["injuries"],
        "restrictions": a["restrictions"],
        "history": a["history"],
        "level": a["level"],
        "freq_per_week": a["freq_per_week"],
        "session_time_min": a["session_time_min"],
        "case_notes": a["case_notes"],
        "equipment": a["equipment"],
        "red_flags": a["red_flags"],
        "readiness": a["readiness"],
        "periodization": a["periodization"],
        "status": a["status"],
        # métricas
        "height_m": m["height_m"],
        "weight_kg": m["weight_kg"],
        "body_fat_percent": m["body_fat_percent"],
        "muscle_mass_kg": m["muscle_mass_kg"],
        "bmi": m["bmi"],
    }
    return bundle


def _build_llm_prompt(bundle: Dict[str, Any]) -> Dict[str, str]:
    """
    Monta system/user prompts anti-alucinação + JSON-ONLY.
    O output esperado é exatamente PlanPreview (plan_meta + items).
    """
    system = (
        "Você é um assistente de treinamento físico de nível especialista. "
        "Sua tarefa é propor um rascunho de plano de treino estruturado, "
        "considerando meta, nível, limitações e postura do aluno.\n\n"
        "REGRAS:\n"
        "1) NÃO invente exercícios inexistentes; use nomes comuns no BR.\n"
        "2) Evite exercícios contraindicados conforme red_flags/restrictions.\n"
        "3) Volume e descanso coerentes com objetivo e nível.\n"
        "4) Saída OBRIGATÓRIA: APENAS JSON válido com as chaves 'plan_meta' e 'items'.\n"
        "5) Em 'items', cada linha deve conter: week, day, block (opcional), "
        "exercise_code (opcional), exercise_name, sets, reps (ex.: '8-10' ou '8'), "
        "rest_s, tempo (ex.: '3-1-1' ou '3-1-1-0'), rpe (opcional), load_pct_1rm (opcional), "
        "equipment (opcional), focus (opcional), cues (opcional), "
        "regression (opcional), progression (opcional), contraindications (opcional: lista), notes (opcional).\n"
        "6) Em 'plan_meta', inclua: split, goal, periodization, constraints, version=1, status='draft'."
    )

    user = {
        "contexto": bundle,
        "formato_esperado": {
            "plan_meta": {
                "assessment_id": bundle.get("assessment_id"),
                "split": "ABC",
                "goal": "defina claramente (ex.: hipertrofia + postura)",
                "periodization": {"macrocycle": "base", "mesocycle_week": 1},
                "constraints": {"observações": "respeitar red_flags"},
                "version": 1,
                "status": "draft"
            },
            "items": [
                {
                    "week": 1, "day": "A", "block": "Força",
                    "exercise_code": "SQ_BACK",
                    "exercise_name": "Agachamento Livre",
                    "sets": 4, "reps": "6-8", "rest_s": 120, "tempo": "3-1-1",
                    "rpe": 7.5, "load_pct_1rm": None, "equipment": "barra",
                    "focus": "Quadríceps e glúteos",
                    "cues": "joelhos acompanham os pés; coluna neutra",
                    "regression": "Agachamento no Smith",
                    "progression": "Agachamento Frontal",
                    "contraindications": ["dor lombar aguda"],
                    "notes": "deixar 1–2 reps na reserva"
                }
            ]
        },
        "instrucoes": [
            "Ajuste volume conforme freq_per_week e sessão (minutos).",
            "Inclua mobilidade/ativação quando postura exigir.",
            "Respeite red_flags/restrictions.",
            "Se não tiver certeza, omita campos opcionais em vez de inventar."
        ]
    }

    return {"system": system, "user": json.dumps(user, ensure_ascii=False)}


def _call_llm_return_json(system: str, user: str) -> Dict[str, Any]:
    """
    Chama OpenAI ou Groq, retorna dict já parseado.
    Se não houver API key, devolve um MOCK determinístico.
    """
    # 1) Sem chave -> MOCK seguro
    if not (settings.OPENAI_API_KEY or settings.GROQ_API_KEY):
        mock = {
            "plan_meta": {
                "assessment_id": None,
                "split": "ABC",
                "goal": "hipertrofia + postura",
                "periodization": {"macrocycle": "base", "mesocycle_week": 1},
                "constraints": {"observações": "evitar overhead por desconforto no ombro"},
                "version": 1,
                "status": "draft"
            },
            "items": [
                {
                    "week": 1, "day": "A", "block": "Força",
                    "exercise_code": "SQ_BACK",
                    "exercise_name": "Agachamento Livre",
                    "sets": 4, "reps": "6-8", "rest_s": 120, "tempo": "3-1-1",
                    "rpe": 7.5, "load_pct_1rm": None, "equipment": "barra",
                    "focus": "Quadríceps e glúteos", "cues": "coluna neutra",
                    "regression": "Agachamento no Smith", "progression": "Agachamento Frontal",
                    "contraindications": [], "notes": "deixar 1–2 reps na reserva"
                },
                {
                    "week": 1, "day": "A", "block": "Acessório",
                    "exercise_code": "ROW_CABLE",
                    "exercise_name": "Remada Baixa na Polia",
                    "sets": 3, "reps": "10-12", "rest_s": 75, "tempo": "2-1-2",
                    "equipment": "máquina", "focus": "escápulas (retração)",
                    "cues": "ombros para trás e baixo", "contraindications": []
                }
            ]
        }
        return mock

    # 2) OPENAI
    if settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            return json.loads(content)
        except Exception:
            return {
                "plan_meta": {"split": "ABC", "goal": "hipertrofia", "periodization": {"mesocycle_week": 1}, "version": 1, "status": "draft"},
                "items": []
            }

    # 3) GROQ
    if settings.GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            model = getattr(settings, "GROQ_MODEL", "llama3-8b-8192")
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=0.2,
            )
            content = resp.choices[0].message.content
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                content = content[start:end+1]
            return json.loads(content)
        except Exception:
            return {"plan_meta": {"split": "ABC", "goal": "hipertrofia", "version": 1, "status": "draft"}, "items": []}

    return {"plan_meta": {"split": "ABC", "goal": "hipertrofia", "version": 1, "status": "draft"}, "items": []}


# -----------------------------------------------------------------------------
# PREVIEW (estrito): exige student_id, assessment_id e measurement_id coerentes
# -----------------------------------------------------------------------------
@router.post(
    "/preview/student/{student_id}/assessment/{assessment_id}/measurement/{measurement_id}",
    response_model=PlanPreview
)
def preview_from_assessment_strict(
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    enforce_assessment_snapshot_match: bool = False,
    db: Session = Depends(get_db),
):
    """
    Gera rascunho (NÃO SALVA) SOMENTE se student_id, assessment_id e measurement_id
    forem coerentes entre si. Opcional: forçar que measurement == snapshot do assessment.
    """
    bundle = _fetch_assessment_bundle_strict(
        db=db,
        student_id=student_id,
        assessment_id=assessment_id,
        measurement_id=measurement_id,
        enforce_assessment_snapshot_match=enforce_assessment_snapshot_match,
    )

    prompts = _build_llm_prompt(bundle)
    raw = _call_llm_return_json(prompts["system"], prompts["user"])

    try:
        preview = PlanPreview.model_validate(raw)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Resposta do LLM inválida: {e}")

    # amarra assessment_id no meta do preview
    preview.plan_meta.assessment_id = assessment_id
    return preview


# -----------------------------------------------------------------------------
# CREATE: salva plano EDITADO no banco
# -----------------------------------------------------------------------------
@router.post("/", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(payload: PlanCreate, db: Session = Depends(get_db)):
    """
    Recebe o JSON final editado (plan_meta + items) e salva no banco.
    Reforça coerência: assessment.student_id deve bater com student_id.
    """
    # valida coerência forte
    fk = db.execute(text("""
        SELECT
          (SELECT student_id FROM assessments WHERE id = :aid) AS a_sid,
          (SELECT 1 FROM students WHERE id = :sid) AS s_ok
    """), {"sid": payload.student_id, "aid": payload.assessment_id}).mappings().one()

    if fk["s_ok"] is None:
        raise HTTPException(status_code=400, detail="student_id inválido.")
    if fk["a_sid"] is None:
        raise HTTPException(status_code=400, detail="assessment_id inválido.")
    if fk["a_sid"] != payload.student_id:
        raise HTTPException(
            status_code=400,
            detail="assessment_id não pertence ao student_id informado."
        )

    plan_blob = {
        "plan_meta": payload.plan_meta.model_dump(),
        "items": [it.model_dump() for it in payload.items]
    }

    stmt = text("""
        INSERT INTO plans (student_id, assessment_id, plan_json)
        VALUES (:sid, :aid, :pjson)
        RETURNING id, student_id, assessment_id, plan_json, created_at;
    """)
    try:
        row = db.execute(stmt, {
            "sid": payload.student_id,
            "aid": payload.assessment_id,
            "pjson": json.dumps(plan_blob, ensure_ascii=False)
        }).mappings().one()
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao salvar plano (FK inválida?).")


# -----------------------------------------------------------------------------
# READs
# -----------------------------------------------------------------------------
@router.get("/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT id, student_id, assessment_id, plan_json, created_at
        FROM plans
        WHERE id = :pid;
    """), {"pid": plan_id}).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return dict(row)

@router.get("/student/{student_id}", response_model=List[PlanOut])
def list_plans_by_student(student_id: int, db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT id, student_id, assessment_id, plan_json, created_at
        FROM plans
        WHERE student_id = :sid
        ORDER BY id DESC;
    """), {"sid": student_id}).mappings().all()
    return [dict(r) for r in rows]


# -----------------------------------------------------------------------------
# UPDATE (parcial) do plan_json
# -----------------------------------------------------------------------------
@router.put("/{plan_id}", response_model=PlanOut)
def update_plan(plan_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Atualiza parcialmente o plan_json.
    Aceita payload:
    {
      "plan_meta": {...},   # opcional (mescla)
      "items": [...]        # opcional (substitui lista inteira)
    }
    """
    row = db.execute(text("SELECT plan_json FROM plans WHERE id = :id;"),
                     {"id": plan_id}).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    current = row["plan_json"]
    if isinstance(current, str):
        current = json.loads(current)

    if "plan_meta" in payload and payload["plan_meta"] is not None:
        meta = PlanMeta.model_validate(payload["plan_meta"])
        current["plan_meta"] = {**current.get("plan_meta", {}), **meta.model_dump()}

    if "items" in payload and payload["items"] is not None:
        items = [PlanItem.model_validate(it).model_dump() for it in payload["items"]]
        current["items"] = items

    stmt = text("""
        UPDATE plans
        SET plan_json = :pjson
        WHERE id = :id
        RETURNING id, student_id, assessment_id, plan_json, created_at;
    """)
    try:
        row2 = db.execute(stmt, {"pjson": json.dumps(current, ensure_ascii=False), "id": plan_id}).mappings().one()
        db.commit()
        return dict(row2)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao atualizar plano.")


# -----------------------------------------------------------------------------
# DELETE
# -----------------------------------------------------------------------------
@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    res = db.execute(text("DELETE FROM plans WHERE id = :id;"), {"id": plan_id})
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    return
