from pydantic import BaseModel, field_serializer
from typing import Optional, Dict, Any
from datetime import datetime

class AssessmentCreate(BaseModel):
    student_id: int
    measurement_id: Optional[int] = None  # snapshot opcional
    objectives: Optional[Dict[str, Any]] = None
    posture: Optional[Dict[str, Any]] = None
    injuries: Optional[Dict[str, Any]] = None
    restrictions: Optional[Dict[str, Any]] = None
    history: Optional[Dict[str, Any]] = None
    level: Optional[str] = None
    freq_per_week: Optional[int] = None
    session_time_min: Optional[int] = None
    case_notes: Optional[str] = None
    equipment: Optional[Dict[str, Any]] = None
    red_flags: Optional[Dict[str, Any]] = None
    readiness: Optional[Dict[str, Any]] = None
    periodization: Optional[Dict[str, Any]] = None
    status: Optional[str] = "draft"

class AssessmentUpdate(BaseModel):
    student_id: Optional[int] = None
    measurement_id: Optional[int] = None
    objectives: Optional[Dict[str, Any]] = None
    posture: Optional[Dict[str, Any]] = None
    injuries: Optional[Dict[str, Any]] = None
    restrictions: Optional[Dict[str, Any]] = None
    history: Optional[Dict[str, Any]] = None
    level: Optional[str] = None
    freq_per_week: Optional[int] = None
    session_time_min: Optional[int] = None
    case_notes: Optional[str] = None
    equipment: Optional[Dict[str, Any]] = None
    red_flags: Optional[Dict[str, Any]] = None
    readiness: Optional[Dict[str, Any]] = None
    periodization: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class AssessmentOut(BaseModel):
    id: int
    student_id: int
    measurement_id: Optional[int] = None
    objectives: Optional[Dict[str, Any]] = None
    posture: Optional[Dict[str, Any]] = None
    injuries: Optional[Dict[str, Any]] = None
    restrictions: Optional[Dict[str, Any]] = None
    history: Optional[Dict[str, Any]] = None
    level: Optional[str] = None
    freq_per_week: Optional[int] = None
    session_time_min: Optional[int] = None
    case_notes: Optional[str] = None
    equipment: Optional[Dict[str, Any]] = None
    red_flags: Optional[Dict[str, Any]] = None
    readiness: Optional[Dict[str, Any]] = None
    periodization: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

    created_at: datetime

    @field_serializer("created_at")
    def _fmt_dt(self, v: datetime):
        return v.strftime("%Y-%m-%d %H:%M")

    class Config:
        orm_mode = True
