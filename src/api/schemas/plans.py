from __future__ import annotations
from pydantic import BaseModel, Field, field_validator, field_serializer
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import re

# ---------------------------
# Linha da tabela (um exercício)
# ---------------------------
class PlanItem(BaseModel):
    week: int = Field(..., ge=1, description="Semana do mesociclo (ex.: 1 a 4)")
    day: str = Field(..., description="A/B/C ou Seg/Ter/etc")
    block: Optional[str] = Field(None, description="Força, Mobilidade, Acessório...")

    exercise_code: Optional[str] = Field(None, description="ID canônico opcional (ex.: SQ_BACK)")
    exercise_name: str = Field(..., description="Nome do exercício visível ao professor")

    sets: int = Field(..., ge=1)
    reps: Union[int, str] = Field(..., description='Número (ex.: 8) ou intervalo "8-10"')
    rest_s: int = Field(90, ge=0, description="Descanso em segundos")
    tempo: Optional[str] = Field(None, description='Padrão "3-1-1" ou "3-1-1-0"')

    rpe: Optional[float] = Field(None, description="Esforço percebido (5 a 10)")
    load_pct_1rm: Optional[float] = Field(None, description="Carga como %1RM (0 a 100)")

    equipment: Optional[str] = None
    focus: Optional[str] = None
    cues: Optional[str] = None
    regression: Optional[str] = None
    progression: Optional[str] = None
    contraindications: Optional[List[str]] = None
    notes: Optional[str] = None

    # --- Normalizações / validações simples ---
    @field_validator("day", "block", "exercise_code", "exercise_name",
                     "equipment", "focus", "cues", "regression", "progression", "notes")
    @classmethod
    def _strip_strings(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                return None
        return v

    @field_validator("reps")
    @classmethod
    def _validate_reps(cls, v):
        # aceita int -> vira "8"
        if isinstance(v, int):
            return str(v)
        if isinstance(v, str):
            s = v.strip().replace("–", "-")  # en-dash -> hyphen
            # Formatos aceitos: "8" ou "8-10"
            if re.fullmatch(r"^\d+$", s) or re.fullmatch(r"^\d+\-\d+$", s):
                return s
        raise ValueError('reps inválido. Use número (ex.: 8) ou intervalo "8-10".')

    @field_validator("tempo")
    @classmethod
    def _validate_tempo(cls, v):
        if v is None:
            return v
        s = v.strip()
        # Aceita 3 ou 4 números: ex "3-1-1" ou "3-1-1-0"
        if re.fullmatch(r"^\d+(?:-\d+){2,3}$", s):
            return s
        raise ValueError('tempo inválido. Use "3-1-1" ou "3-1-1-0".')

    @field_validator("rpe")
    @classmethod
    def _validate_rpe(cls, v):
        if v is None:
            return v
        if 5 <= float(v) <= 10:
            return float(v)
        raise ValueError("rpe deve estar entre 5 e 10")

    @field_validator("load_pct_1rm")
    @classmethod
    def _validate_pct(cls, v):
        if v is None:
            return v
        if 0 <= float(v) <= 100:
            return float(v)
        raise ValueError("load_pct_1rm deve estar entre 0 e 100")


# ---------------------------
# Metadados do plano (fora da tabela)
# ---------------------------
class PlanMeta(BaseModel):
    assessment_id: Optional[int] = Field(None, description="Assessment usado como base")
    split: Optional[str] = None                      # ex.: "AB", "ABC", "FullBody 3x"
    goal: Optional[str] = None                       # ex.: "hipertrofia + postura"
    periodization: Optional[Dict[str, Any]] = None   # ex.: {"macrocycle":"base", "mesocycle_week":2}
    constraints: Optional[Dict[str, Any]] = None     # regras/limitações adotadas
    version: int = 1
    status: str = "draft"                            # 'draft' ou 'final'

    @field_validator("split", "goal")
    @classmethod
    def _strip_meta(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                return None
        return v


# ---------------------------
# Estrutura do preview (LLM -> front)
# ---------------------------
class PlanPreview(BaseModel):
    plan_meta: PlanMeta
    items: List[PlanItem]


# ---------------------------
# Entrada para SALVAR no banco (após edição no front)
# ---------------------------
class PlanCreate(BaseModel):
    student_id: int
    assessment_id: int
    plan_meta: PlanMeta
    items: List[PlanItem]

    @field_validator("plan_meta")
    @classmethod
    def _ensure_assessment_in_meta(cls, v, info):
        """
        Garante que o plan_meta.assessment_id exista e
        bata com o campo assessment_id do payload.
        """
        # info.data contém os demais campos já parseados
        assessment_id = info.data.get("assessment_id")
        if v.assessment_id is None:
            v.assessment_id = assessment_id
        elif v.assessment_id != assessment_id:
            raise ValueError("plan_meta.assessment_id deve ser igual a assessment_id do payload.")
        return v


# ---------------------------
# Saída quando persistido no banco
# ---------------------------
class PlanOut(BaseModel):
    id: int
    student_id: int
    assessment_id: int
    plan_json: Dict[str, Any]        # o blob salvo (plan_meta + items)
    created_at: datetime

    @field_serializer("created_at")
    def _fmt_dt(self, v: datetime):
        return v.strftime("%Y-%m-%d %H:%M")

    class Config:
        orm_mode = True
