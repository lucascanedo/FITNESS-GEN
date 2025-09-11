from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

# Entrada
class AssessmentCreate(BaseModel):
    student_id: int
    objectives: Optional[Dict] = None
    posture: Optional[Dict] = None
    injuries: Optional[Dict] = None
    restrictions: Optional[Dict] = None
    history: Optional[Dict] = None
    level: Optional[str] = None
    freq_per_week: Optional[int] = None
    session_time_min: Optional[int] = None

# Saída
class AssessmentOut(BaseModel):
    id: int
    student_id: int
    objectives: Optional[Dict] = None
    posture: Optional[Dict] = None
    injuries: Optional[Dict] = None
    restrictions: Optional[Dict] = None
    history: Optional[Dict] = None
    level: Optional[str] = None
    freq_per_week: Optional[int] = None
    session_time_min: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True
