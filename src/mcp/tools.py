from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from src.IA.llm_helpers import get_llm_bundle
from src.services.assessment_service import get_assessment
from src.services.llm_context_service import sanitize_bundle_for_prompt
from src.services.llm_service import build_generation_payload
from src.services.measurement_service import get_measurement
from src.services.plan_analysis_service import (
    build_student_plan_mcp_context,
    get_plan_comparison,
    get_professor_learning_diagnostics,
)
from src.services.plan_service import get_current_student_plan
from src.services.student_service import get_student_by_id


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def dump_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return json_ready(payload)


def register_tools(mcp, db_session) -> None:
    @mcp.tool(
        name="get_generation_context",
        description="Retorna o contexto compacto principal para gerar o plano do aluno com padrÃµes do professor e plano atual.",
        structured_output=True,
    )
    def get_generation_context_tool(
        student_id: int,
        assessment_id: int,
        measurement_id: int,
        include_learning: bool = True,
        include_current_plan: bool = True,
    ) -> dict[str, Any]:
        with db_session() as db:
            return dump_payload(
                build_generation_payload(
                    db=db,
                    student_id=student_id,
                    assessment_id=assessment_id,
                    measurement_id=measurement_id,
                    include_learning=include_learning,
                    include_current_plan=include_current_plan,
                )
            )

    @mcp.tool(
        name="get_student_snapshot",
        description="Retorna um snapshot sanitizado do aluno, assessment e measurement para uso em geraÃ§Ã£o.",
        structured_output=True,
    )
    def get_student_snapshot_tool(
        student_id: int,
        assessment_id: int,
        measurement_id: int,
    ) -> dict[str, Any]:
        with db_session() as db:
            bundle = get_llm_bundle(
                db=db,
                student_id=student_id,
                assessment_id=assessment_id,
                measurement_id=measurement_id,
                enforce_snapshot_match=False,
            )
            return dump_payload(
                {
                    "student_id": student_id,
                    "assessment_id": assessment_id,
                    "measurement_id": measurement_id,
                    "snapshot": sanitize_bundle_for_prompt(bundle),
                }
            )

    @mcp.tool(
        name="get_current_student_plan",
        description="Retorna o plano atual ativo do aluno, se existir.",
        structured_output=True,
    )
    def get_current_student_plan_tool(student_id: int) -> dict[str, Any]:
        with db_session() as db:
            return dump_payload(
                {
                    "student_id": student_id,
                    "current_plan": get_current_student_plan(db, student_id),
                }
            )

    @mcp.tool(
        name="get_plan_memory",
        description="Retorna memÃ³ria compacta do aluno: plano atual, comparaÃ§Ã£o atual e diagnÃ³sticos de aprendizado.",
        structured_output=True,
    )
    def get_plan_memory_tool(student_id: int) -> dict[str, Any]:
        with db_session() as db:
            return dump_payload(build_student_plan_mcp_context(db, student_id))

    @mcp.tool(
        name="get_plan_comparison",
        description="Retorna a comparaÃ§Ã£o entre o plano gerado pela LLM e o plano final salvo pelo professor.",
        structured_output=True,
    )
    def get_plan_comparison_tool(plan_id: int) -> dict[str, Any]:
        with db_session() as db:
            return dump_payload(
                {
                    "plan_id": plan_id,
                    "comparison": get_plan_comparison(db, plan_id),
                }
            )

    @mcp.tool(
        name="get_professor_learning_diagnostics",
        description="Retorna mÃ©tricas agregadas dos padrÃµes do professor para aprendizado da IA.",
        structured_output=True,
    )
    def get_professor_learning_diagnostics_tool(student_id: int | None = None) -> dict[str, Any]:
        with db_session() as db:
            return dump_payload(
                {
                    "student_id": student_id,
                    "diagnostics": get_professor_learning_diagnostics(db, student_id=student_id),
                }
            )

    @mcp.tool(
        name="get_student_record",
        description="Retorna dados diretos do aluno, assessment e measurement sem contexto agregado.",
        structured_output=True,
    )
    def get_student_record_tool(
        student_id: int,
        assessment_id: int | None = None,
        measurement_id: int | None = None,
    ) -> dict[str, Any]:
        with db_session() as db:
            return dump_payload(
                {
                    "student": get_student_by_id(db, student_id),
                    "assessment": get_assessment(db, assessment_id) if assessment_id is not None else None,
                    "measurement": get_measurement(db, measurement_id) if measurement_id is not None else None,
                }
            )
