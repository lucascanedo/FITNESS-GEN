from pydantic import BaseModel
from datetime import datetime
from typing import Dict

# Saída (plano gerado por LLM)
class PlanOut(BaseModel):
    id: int
    student_id: int
    assessment_id: int
    plan_json: Dict
    created_at: datetime

    class Config:
        orm_mode = True
