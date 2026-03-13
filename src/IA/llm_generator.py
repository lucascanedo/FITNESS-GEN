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
        periodization = assessment.get("periodization") or {}
        preferred_days = periodization.get("preferred_days") or []
        split_preference = periodization.get("split_preference") or "auto"

    
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
            "13) Gere a grade semanal completa, sem deixar dias vazios. Se freq_per_week for 3, gere 3 dias; "
            "se for 4, gere 4 dias; e assim por diante.\n"
            "14) Cada dia de treino deve ter no minimo 4 exercicios e, em contexto normal, entre 5 e 8 exercicios.\n"
            "15) No campo 'day', use 'Dia 1', 'Dia 2', 'Dia 3' etc.; se houver dias preferenciais, use "
            "'Dia 1 - Segunda', 'Dia 2 - Quarta' e assim por diante.\n"
            "16) Se houver preferencia por ABC, PPL, Upper/Lower ou Full Body, respeite-a sempre que ela for "
            "compativel com freq_per_week e nivel do aluno.\n"
            "17) Nunca devolva um split com apenas um exercicio por dia. O plano precisa ser utilizavel pelo professor.\n"
        )

        user_payload = {
            "contexto_aluno": context,
            "plano_atual_e_memoria": current_plan_context,
            "preferencias_de_grade": {
                "split_preference": split_preference,
                "preferred_days": preferred_days,
                "freq_per_week": assessment.get("freq_per_week"),
            },
            "alertas_de_seguranca": {
                "restrictions": restrictions,
                "injuries": injuries,
                "red_flags": red_flags,
                "readiness": readiness,
            },
            "regras_de_geracao": [
                "Distribua as sessoes respeitando freq_per_week e session_time_min.",
                "Monte uma grade semanal completa com todos os dias de treino previstos.",
                "Se o aluno treinar 3 dias, entregue 3 sessoes completas; se treinar 4 dias, entregue 4 sessoes completas.",
                "Use a preferencia de split e os dias disponiveis quando estiverem informados.",
                "Inclua mobilidade, ativacao ou regressao quando houver postura alterada, restricoes ou lesoes.",
                "Respeite integralmente os red_flags, warnings e sinais de baixa prontidao.",
                "Nao exponha nem reflita dados sensiveis no conteudo gerado.",
                "Evite redundancia de exercicios no mesmo dia sem justificativa.",
                "Garanta no minimo 4 exercicios por dia de treino.",
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
                    "periodization": {
                        "macrocycle": "base",
                        "mesocycle_week": 1,
                        "preferred_days": ["Segunda", "Quarta", "Sexta"],
                        "split_preference": "ABC"
                    },
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
                    },
                    {
                        "week": 1,
                        "day": "Dia 1 - Segunda",
                        "exercise_name": "Leg Press 45",
                        "sets": 3,
                        "reps": "10-12",
                        "rest_s": 90,
                        "tempo": "2-1-1",
                        "block": "Principal"
                    }
                ]
            },
            "saida": "APENAS JSON valido."
        }
        if learning:
            user_payload["aprendizado_do_professor"] = learning
        

        return f"[SYSTEM]\n{system}\n[USER]\n{json.dumps(user_payload, ensure_ascii=False)}"

    def _build_repair_prompt(self, original_prompt: str, plan: dict[str, Any], bundle: dict[str, Any]) -> str:
        assessment = (bundle.get("generation_context") or bundle).get("assessment") or {}
        freq_per_week = assessment.get("freq_per_week") or 0
        return (
            f"{original_prompt}\n"
            "[QUALITY_CONTROL]\n"
            "O JSON anterior ficou incompleto para uso profissional.\n"
            f"O plano precisa conter pelo menos {freq_per_week} dias de treino quando essa frequencia estiver definida.\n"
            "Cada dia precisa ter no minimo 4 exercicios validos.\n"
            "Reescreva o JSON inteiro mantendo seguranca, objetivo e restricoes.\n"
            "Nao devolva um resumo. Nao devolva explicacoes. Apenas um JSON completo.\n"
            f"JSON anterior insuficiente: {json.dumps(plan, ensure_ascii=False)}"
        )

    def _plan_quality(self, plan: dict[str, Any], bundle: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        assessment = (bundle.get("generation_context") or bundle).get("assessment") or {}
        freq_per_week = int(assessment.get("freq_per_week") or 0)
        items = plan.get("items") if isinstance(plan.get("items"), list) else []
        per_day: dict[str, int] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            day = str(item.get("day") or "").strip()
            exercise_name = str(item.get("exercise_name") or "").strip()
            if not day or not exercise_name:
                continue
            per_day[day] = per_day.get(day, 0) + 1

        day_count = len(per_day)
        min_items_per_day = min(per_day.values()) if per_day else 0
        valid = bool(per_day) and min_items_per_day >= 4 and (freq_per_week <= 0 or day_count >= freq_per_week)
        return valid, {
            "day_count": day_count,
            "min_items_per_day": min_items_per_day,
            "expected_days": freq_per_week,
        }

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
        quality_ok, quality_stats = self._plan_quality(plan, bundle)
        meta["quality_stats"] = quality_stats
        if quality_ok or error:
            return plan, meta

        repair_prompt = self._build_repair_prompt(prompt, plan, bundle)
        try:
            repair_response = self.client.invoke(repair_prompt)
            repair_content = repair_response.content or ""
            repaired_plan = self._parse_json_safe(repair_content)
            repaired_ok, repaired_stats = self._plan_quality(repaired_plan, bundle)
            meta["repair_attempted"] = True
            meta["repair_quality_stats"] = repaired_stats
            if repaired_ok:
                meta["resp_raw"] = repair_content[:5000]
                meta["resp_len"] = len(repair_content)
                return repaired_plan, meta
        except Exception as exc:
            meta["repair_error"] = repr(exc)
        return plan, meta
