# src/IA/llm_generator.py
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from src.core.settings import settings
    
load_dotenv()
log = logging.getLogger("fitnessgen")


class LLMGenerator:
    """
    Recebe um bundle sanitizado e gera um plano em JSON.
    """

    def __init__(self, model_id: str | None = None, temperature: float | None = None):
        self.model_id = model_id or settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE if temperature is None else temperature
        self.client = ChatGroq(model=self.model_id, temperature=self.temperature)
        

    def _hash(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]

    def _build_prompt(self, bundle: dict[str, Any]) -> str:
        """
        Prompt unico, prescritivo e orientado pelo historico do professor.
        """
        generation_context = bundle.get("generation_context") or bundle
        current_plan_context = bundle.get("current_plan_context") or {}
        context = {key: value for key, value in generation_context.items() if key != "_learning_context"}
        learning = generation_context.get("_learning_context") or {}

        assessment = context.get("assessment") or {}
        restrictions = assessment.get("restrictions") or []
        injuries = assessment.get("injuries") or []
        red_flags = assessment.get("red_flags") or []
        readiness = assessment.get("readiness") or {}

    
        system = (
            "Voce e um treinador fisico especialista. Gere um plano de treino estruturado, "
            "seguro e realista, respeitando objetivo, nivel, postura, restricoes e tempo de sessao.\n"
            "REGRAS:\n"
            "1) Responda somente com JSON valido contendo as chaves 'plan_meta' e 'items'.\n"
            "2) Nao invente exercicios, lesoes, equipamentos ou dados do aluno.\n"
            "3) Nunca reproduza ou solicite dados sensiveis: nome, CPF, email, telefone, endereco, documento, "
            "identificadores ou texto livre desnecessario. Se algum dado sensivel aparecer no contexto, ignore-o.\n"
            "4) Se houver conflito entre contexto clinico e historico do professor, priorize seguranca.\n"
            "5) Restricoes, lesoes, red_flags, readiness, warnings e contraindications sao obrigatorios. "
            "Nao prescreva exercicios, amplitudes, cargas ou progressos que conflitem com esses sinais.\n"
            "6) Quando houver warning clinico, escolha a opcao mais conservadora: regressao, menor carga, "
            "menor complexidade tecnica e menor fadiga sistemica.\n"
            "7) Use o historico do professor como regra de estilo: estrutura semanal, selecao de exercicios, "
            "ajustes de sets/reps/rest/rpe/tempo e split.\n"
            "8) Em 'items', cada exercicio deve conter: week, day, exercise_name, sets, reps, rest_s, tempo.\n"
            "9) Campos opcionais permitidos: block, exercise_code, rpe, load_pct_1rm, equipment, focus, cues, "
            "regression, progression, contraindications, notes.\n"
            "10) 'plan_meta' deve conter: split, goal, periodization, constraints, version=1, status='draft'.\n"
            "11) Prefira consistencia com os padroes aprendidos em vez de variedade gratuita.\n"
            "12) Nao inclua texto explicativo, observacoes fora do schema ou justificativas fora do JSON.\n"
        )

        user_payload = {
            "contexto_aluno": context,
            "plano_atual_e_memoria": current_plan_context,
            "alertas_de_seguranca": {
                "restrictions": restrictions,
                "injuries": injuries,
                "red_flags": red_flags,
                "readiness": readiness,
            },
            "regras_de_geracao": [
                "Distribua as sessoes respeitando freq_per_week e session_time_min.",
                "Inclua mobilidade, ativacao ou regressao quando houver postura alterada, restricoes ou lesoes.",
                "Respeite integralmente os red_flags, warnings e sinais de baixa prontidao.",
                "Nao exponha nem reflita dados sensiveis no conteudo gerado.",
                "Evite redundancia de exercicios no mesmo dia sem justificativa.",
                "Nao inclua explicacoes fora do JSON."
            ],
            "prioridade_de_decisao": [
                "1. Seguranca clinica e restricoes.",
                "2. Red flags, warnings e readiness.",
                "3. Objetivo, nivel e disponibilidade.",
                "4. Padroes recorrentes do professor para casos semelhantes.",
                "5. Clareza e simplicidade da progressao."
            ],
            "formato_esperado": {
                "plan_meta": {
                    "split": "ABC",
                    "goal": "hipertrofia com ajustes posturais",
                    "periodization": {"macrocycle": "base", "mesocycle_week": 1},
                    "constraints": {"obs": "respeitar red_flags e restricoes"},
                    "version": 1,
                    "status": "draft"
                },
                "items": [
                    {
                        "week": 1,
                        "day": "A",
                        "exercise_name": "Agachamento Livre",
                        "sets": 4,
                        "reps": "6-8",
                        "rest_s": 120,
                        "tempo": "3-1-1",
                        "block": "Forca",
                        "focus": "Quadriceps e gluteos",
                        "cues": "coluna neutra e joelhos acompanham os pes",
                        "regression": "Agachamento no Smith",
                        "progression": "Agachamento Frontal",
                        "contraindications": []
                    }
                ]
            },
            "saida": "APENAS JSON valido."
        }
        if learning:
            user_payload["aprendizado_do_professor"] = learning
        

        return f"[SYSTEM]\n{system}\n[USER]\n{json.dumps(user_payload, ensure_ascii=False)}"

    def _parse_json_safe(self, content: str) -> dict[str, Any]:
        try:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError("Resposta nao contem JSON valido.")
            raw_json = content[start : end + 1]
            data = json.loads(raw_json)
        except Exception:
            data = {
                "plan_meta": {
                    "split": "ABC",
                    "goal": "ajustar conforme objetivo do aluno",
                    "periodization": {"macrocycle": "base", "mesocycle_week": 1},
                    "constraints": {"obs": "verificar red_flags"},
                    "version": 1,
                    "status": "draft",
                },
                "items": [],
            }

        if "plan_meta" not in data or not isinstance(data["plan_meta"], dict):
            data["plan_meta"] = {
                "split": "ABC",
                "goal": "ajustar conforme objetivo do aluno",
                "periodization": {"macrocycle": "base", "mesocycle_week": 1},
                "constraints": {"obs": "verificar red_flags"},
                "version": 1,
                "status": "draft",
            }
        if "items" not in data or not isinstance(data["items"], list):
            data["items"] = []
        return data

    def generate_plan(
        self,
        bundle: dict[str, Any],
        correlation_id: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        prompt = self._build_prompt(bundle)
        start = time.perf_counter()
        error = None
        content = ""
        try:
            response = self.client.invoke(prompt)
            content = response.content or ""
        except Exception as exc:
            error = repr(exc)
        duration_ms = (time.perf_counter() - start) * 1000

        meta = {
            "provider": settings.LLM_PROVIDER,
            "model": self.model_id,
            "prompt_hash": self._hash(prompt),
            "prompt_len": len(prompt),
            "resp_len": len(content),
            "duration_ms": round(duration_ms, 2),
            "error": error,
            "correlation_id": correlation_id,
            "resp_raw": content[:5000],
        }

        log.info({"event": "llm_call", **meta})
        plan = self._parse_json_safe(content)
        return plan, meta
