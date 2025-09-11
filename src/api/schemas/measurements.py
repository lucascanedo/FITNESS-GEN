from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Entrada (quando registrar uma medição)
class MeasurementCreate(BaseModel):
    student_id: int
    measured_at: Optional[datetime] = None   # se não vier, banco usa CURRENT_TIMESTAMP
    height_m: Optional[float] = None
    weight_kg: Optional[float] = None
    body_fat_percent: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    source: Optional[str] = None
    notes: Optional[str] = None

# Saída (quando buscar uma medição do banco)
class MeasurementOut(BaseModel):
    id: int
    student_id: int
    measured_at: datetime
    height_m: Optional[float] = None
    weight_kg: Optional[float] = None
    body_fat_percent: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    bmi: Optional[float] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
