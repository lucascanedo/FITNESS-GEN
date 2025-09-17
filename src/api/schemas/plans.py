from __future__ import annotations
from typing import List, Literal, Dict, Any, Annotated
from pydantic import BaseModel, Field, conint, confloat, field_validator, ConfigDict


# -----------------------------
# Núcleo do plano (editável)
# -----------------------------
class PlanMeta(BaseModel):
    """
    Metadados do plano retornado pelo LLM e editado no front.
    """
    split: str = Field(..., description="Ex.: ABC, Full-body, UL, PPL…")
    goal: str = Field(..., description="Objetivo do plano (ex.: hipertrofia + postura)")
    periodization: Dict[str, Any] = Field(
        ..., description="Informações sobre ciclo, meso, macro, etc."
    )
    constraints: Dict[str, Any] = Field(
        ..., description="Restrições/observações de segurança."
    )
    version: int = Field(default=1)
    status: Literal["draft", "active", "archived"] = Field(default="draft")


class PlanItem(BaseModel):
    """
    Linha de prescrição de treino (um exercício em um dia/semana).
    """
    week: Annotated[int, Field(ge=1, description="Semana do ciclo (>=1).")]
    day: Annotated[str, Field(description="Identificador do dia (ex.: 'A', 'B', 'seg', 'ter').")]
    exercise_name: Annotated[str, Field(description="Nome do exercício em PT-BR.")]
    block: Annotated[str, Field(description="Ex.: Força, Potência, Acessório")]
    sets: Annotated[int, Field(ge=1, description="Número de séries (>=1).")]
    reps: Annotated[str, Field(description="Ex.: '6-8' ou '10'")]
    rest_s: Annotated[int, Field(ge=0, description="Descanso em segundos.")]
    tempo: Annotated[str, Field(description="Ex.: '3-1-1' ou '3-1-1-0'.")]

    exercise_code: Annotated[str, Field(description="Código interno opcional")]
    rpe: Annotated[float, Field(ge=0, le=10, description="Esforço percebido (0–10)")]
    load_pct_1rm: Annotated[float, Field(ge=0, le=100, description="% de 1RM estimada")]

    equipment: str = Field(..., description="Equipamento")
    focus: str = Field(..., description="Foco muscular principal")
    cues: str = Field(..., description="Dicas de execução")
    regression: str = Field(..., description="Versão mais fácil")
    progression: str = Field(..., description="Versão mais difícil")
    contraindications: List[str] = Field(..., description="Lista de contraindicações")
    notes: str = Field(..., description="Observações extras")

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
    """
    Corpo do plano que o LLM retorna e o front edita antes de salvar.
    """
    plan_meta: PlanMeta
    items: List[PlanItem]


# -----------------------------
# Contratos de entrada/saída
# -----------------------------
class PlanCreate(BaseModel):
    """
    Payload para salvar um plano no banco.
    """
    student_id: int
    plan_meta: PlanMeta
    items: List[PlanItem]


class PlanUpdate(BaseModel):
    plan_meta: PlanMeta
    items: List[PlanItem]


class PlanOut(BaseModel):
    """
    Saída ao buscar um plano salvo no banco.
    """
    id: int
    student_id: int
    plan_json: PlanBody
    created_at: str
