from __future__ import annotations

import os
from contextlib import contextmanager

from mcp.server.fastmcp import FastMCP

from src.core.settings import settings
from src.db.database import SessionLocal
from src.mcp.tools import register_tools


SERVER_INSTRUCTIONS = (
    "Use estas ferramentas antes de gerar um plano de treino. "
    "Prefira primeiro `get_generation_context`, que retorna o contexto compacto ideal para geraÃ§Ã£o. "
    "Use as demais ferramentas apenas quando precisar inspecionar detalhes do aluno, do plano atual "
    "ou dos padrÃµes do professor."
)


mcp = FastMCP(
    name="fitness-gen-mcp",
    instructions=SERVER_INSTRUCTIONS,
)


@contextmanager
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


register_tools(mcp, db_session)


@mcp.prompt(
    name="plan_generation_workflow",
    description="InstruÃ§Ã£o curta para um agente usar as ferramentas certas antes de gerar um plano.",
)
def plan_generation_workflow_prompt() -> str:
    return (
        "Antes de gerar o plano: "
        "1. chame `get_generation_context`; "
        "2. se houver dÃºvida sobre o plano ativo, chame `get_current_student_plan` ou `get_plan_memory`; "
        "3. se precisar auditar padrÃµes do professor, chame `get_professor_learning_diagnostics`; "
        "4. gere o plano usando principalmente o retorno de `get_generation_context`."
    )


def main() -> None:
    transport = (settings.MCP_TRANSPORT or "stdio").strip().lower() or "stdio"
    if transport not in {"stdio", "sse", "streamable-http"}:
        raise ValueError("MCP_TRANSPORT deve ser 'stdio', 'sse' ou 'streamable-http'.")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
