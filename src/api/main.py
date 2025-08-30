from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Fitness Gen API")

# Modelo de dados da avaliação do aluno
class Assessment(BaseModel):
    name: str
    age: int
    sex: str
    weight: float
    height: float
    posture_issues: Optional[List[str]] = []
    injuries: Optional[List[str]] = []
    training_history: Optional[str] = None
    goals: Optional[List[str]] = []

# Modelo de retorno do plano de treino
class ExercisePlan(BaseModel):
    exercise: str
    sets: int
    reps: int
    focus: str
    explanation: str

@app.get("/")
def read_root():
    return {"message": "Projeto Fitness Genativo ativo!"}

@app.post("/generate-plan", response_model=List[ExercisePlan])
def generate_plan(assessment: Assessment):
    """
    Endpoint que recebe a avaliação do aluno e retorna um plano de treino mock.
    """
    # Mock de exercícios - depois será substituído pelo ML + LLM
    mock_plan = [
        ExercisePlan(
            exercise="Agachamento",
            sets=3,
            reps=12,
            focus="Força de pernas",
            explanation="O agachamento fortalece quadríceps e glúteos, ajuda a melhorar postura."
        ),
        ExercisePlan(
            exercise="Remada Curvada",
            sets=3,
            reps=10,
            focus="Costas",
            explanation="Fortalece a musculatura das costas e melhora a postura, especialmente em casos de desvio postural leve."
        ),
        ExercisePlan(
            exercise="Prancha",
            sets=3,
            reps=60,
            focus="Core",
            explanation="Melhora estabilidade do core, previne lesões e ajuda na postura."
        ),
    ]
    return mock_plan
