# src/api/main.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.settings import settings
from src.db.database import ping_db

# Routers
from src.api.routes.students import router as students_router
from src.api.routes.measurements import router as measurements_router
from src.api.routes.assessments import router as assessments_router
from src.api.routes.plans import router as plans_router
from src.api.routes.llm import router as llm_router


def _resolve_cors_origins() -> list[str]:
    """
    Converte settings.ALLOWED_ORIGINS em lista.
    - Se for "*", libera todos.
    - Se for string com vírgulas, split/strip.
    """
    ao = (settings.ALLOWED_ORIGINS or "*").strip()
    if ao == "*" or ao.lower() == "all":
        return ["*"]
    return [o.strip() for o in ao.split(",") if o.strip()]


app = FastAPI(title="Fitness Gen API")

# CORS
origins = _resolve_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Projeto Fitness Gen ativo!"}

@app.get("/healthz")
def health_check():
    """Ping da API + status do banco."""
    return {"status": "ok", "database": ping_db()}

# Registra routers
app.include_router(students_router)
app.include_router(measurements_router)
app.include_router(assessments_router)
app.include_router(plans_router)
app.include_router(llm_router)
