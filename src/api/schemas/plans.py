from __future__ import annotations
from typing import List, Literal, Dict, Any, Annotated, Optional
from pydantic import BaseModel, Field, field_validator


# -----------------------------
# Núcleo do plano (editável)
# -----------------------------
class PlanMeta(BaseModel):
    split: str = Field(..., description="Ex.: ABC, Full-body, UL, PPL…")
    goal: str = Field(..., description="Objetivo do plano (ex.: hipertrofia + postura)")
    periodization: Dict[str, Any] = Field(..., description="Ciclo, meso, macro, etc.")
    constraints: Dict[str, Any] = Field(..., description="Restrições de segurança.")
    version: int = Field(default=1)
    status: Literal["draft", "active", "archived"] = Field(default="draft")


class PlanItem(BaseModel):
    week: Annotated[int, Field(ge=1, description="Semana do ciclo (>=1).")]
    day: Annotated[str, Field(description="Ex.: 'A', 'B', 'seg', 'ter'.")]
    exercise_name: Annotated[str, Field(description="Nome do exercício em PT-BR.")]
    block: Annotated[str, Field(default="Principal", description="Ex.: Força, Potência, Acessório")]
    sets: Annotated[int, Field(ge=1, description="Número de séries (>=1).")]
    reps: Annotated[str, Field(description="Ex.: '6-8' ou '10'")]
    rest_s: Annotated[int, Field(ge=0, description="Descanso em segundos.")]
    tempo: Annotated[str, Field(description="Ex.: '3-1-1' ou '3-1-1-0'.")]

    # Opcionais
    exercise_code: Optional[str] = None
    rpe: Optional[float] = Field(None, ge=0, le=10, description="Esforço percebido (0–10)")
    load_pct_1rm: Optional[float] = Field(None, ge=0, le=100, description="% de 1RM")

    equipment: Optional[str] = None
    focus: Optional[str] = None
    cues: Optional[str] = None
    regression: Optional[str] = None
    progression: Optional[str] = None
    contraindications: Optional[List[str]] = []
    notes: Optional[str] = None

    @field_validator("reps")
    @classmethod
    def validate_reps_format(cls, v: str) -> str:
        v = v.strip()
        if v.isdigit():
            return v
        if "-" in v:
            left, _, right = v.partition("-")
            if left.isdigit() and right.isdigit():
                return f"{int(left)}-{int(right)}"
        return v


class PlanBody(BaseModel):
    plan_meta: PlanMeta
    items: List[PlanItem]


# -----------------------------
# Contratos de entrada/saída
# -----------------------------
class PlanCreate(BaseModel):
    student_id: int
    assessment_id: int
    measurement_id: int
    plan_meta: PlanMeta
    items: List[PlanItem]
    generated_plan_json: Optional[Dict[str, Any]] = None  # rascunho original do LLM
    llm_call_id: Optional[int] = None
    correlation_id: Optional[str] = None  # para vincular ao llm_call


class PlanUpdate(BaseModel):
    plan_meta: Optional[PlanMeta] = None
    items: Optional[List[PlanItem]] = None


class PlanGenerationResponse(BaseModel):
    """Resposta da geração LLM: plano + id para vincular ao salvar."""
    plan: "PlanBody"
    llm_call_id: Optional[int] = None


class PlanOut(BaseModel):
    id: int
    student_id: int
    assessment_id: int
    measurement_id: int
    generated_plan_json: Optional[Dict[str, Any]] = None
    plan_json: Dict[str, Any]
    llm_call_id: Optional[int] = None
    edit_count: int = 0
    created_at: str
    updated_at: Optional[str] = None
