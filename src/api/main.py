# src/api/main.py
from __future__ import annotations
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time, uuid, logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.settings import settings
from src.db.database import ping_db

# Routers
from src.api.routes.students import router as students_router
from src.api.routes.measurements import router as measurements_router
from src.api.routes.assessments import router as assessments_router
from src.api.routes.plans import router as plans_router
from src.api.routes.llm import router as llm_router


log = logging.getLogger("fitnessgen")

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # gera um ID único para rastrear essa requisição de ponta a ponta
        cid = str(uuid.uuid4())
        request.state.correlation_id = cid

        start = time.perf_counter()
        response = await call_next(request)
        dur_ms = (time.perf_counter() - start) * 1000

        log.info({
            "event": "http_request",
            "path": request.url.path,
            "method": request.method,
            "status": response.status_code,
            "duration_ms": round(dur_ms, 2),
            "correlation_id": cid,
        })
        return response


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
app.add_middleware(RequestContextMiddleware)