# src/ai/llm_generator.py
import json
from typing import Dict, Any
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()


class LLMGenerator:
    """
    LLM_GENERATOR:
      - recebe um bundle (student + assessment + measurement)
      - monta prompt (system + user) anti-alucinação e JSON-only
      - chama Groq (ChatGroq) e retorna dict {plan_meta, items}
    """

    def __init__(self, model_id: str = "openai/gpt-oss-120b"):
        self.model_id = model_id
        self.client = ChatGroq(model=self.model_id)

    def _build_prompt(self, bundle: Dict[str, Any]) -> str:
        """
        Prompt único (simples e eficaz). Pedimos APENAS JSON válido.
        """
        system = (
            "Você é um treinador físico especialista. Gere um plano de treino estruturado, "
            "seguro e realista, respeitando objetivo, nível, postura e restrições.\n"
            "REGRAS:\n"
            "1) NÃO invente exercícios inexistentes; use nomes comuns no BR.\n"
            "2) Evite exercícios contraindicados conforme red_flags/restrictions.\n"
            "3) Ajuste volume/descanso coerentes com objetivo, nível e duração da sessão.\n"
            "4) SAÍDA OBRIGATÓRIA: SOMENTE JSON VÁLIDO com chaves 'plan_meta' e 'items'.\n"
            "5) Em 'items', cada exercício deve conter obrigatoriamente: "
            "   week, day, exercise_name, sets, reps, rest_s, tempo. "
            "   Campos opcionais: block, exercise_code, rpe, load_pct_1rm, equipment, "
            "   focus, cues, regression, progression, contraindications (lista), notes.\n"
            "6) 'plan_meta' deve conter: split, goal, periodization, constraints, version=1, status='draft'.\n"
        )

        user_payload = {
            "contexto": bundle,
            "formato_esperado": {
                "plan_meta": {
                    "split": "ABC",
                    "goal": "defina claramente (ex.: hipertrofia + postura)",
                    "periodization": {"macrocycle": "base", "mesocycle_week": 1},
                    "constraints": {"obs": "respeitar red_flags e restrições"},
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
                        "block": "Força",
                        "focus": "Quadríceps e glúteos",
                        "cues": "joelhos acompanham os pés; coluna neutra",
                        "regression": "Agachamento no Smith",
                        "progression": "Agachamento Frontal",
                        "contraindications": []
                    }
                ]
            },
            "instrucoes": [
                "Se não tiver certeza, omita opcionais em vez de inventar.",
                "Inclua mobilidade/ativação se houver desvios posturais.",
                "Distribua sessões respeitando freq_per_week e session_time_min."
            ],
            "saida": "APENAS JSON válido."
        }

        # prompt final em texto único (compatível com .invoke(str))
        prompt = (
            f"[SYSTEM]\n{system}\n"
            f"[USER]\n{json.dumps(user_payload, ensure_ascii=False)}"
        )
        return prompt

    def generate_plan(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(bundle)
        response = self.client.invoke(prompt)
        content = response.content or ""

        # Tenta extrair JSON com robustez (pega trecho entre a 1ª { e a última })
        try:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError("Resposta não contém JSON válido.")
            raw_json = content[start:end+1]
            data = json.loads(raw_json)
        except Exception as e:
            # Fallback seguro para não quebrar o front (retorna estrutura mínima)
            data = {
                "plan_meta": {
                    "split": "ABC",
                    "goal": "ajustar conforme objetivo do aluno",
                    "periodization": {"macrocycle": "base", "mesocycle_week": 1},
                    "constraints": {"obs": "verificar red_flags"},
                    "version": 1,
                    "status": "draft"
                },
                "items": []
            }

        # Sanidade mínima: garantir chaves
        if "plan_meta" not in data:
            data["plan_meta"] = {
                "split": "ABC",
                "goal": "ajustar conforme objetivo do aluno",
                "periodization": {"macrocycle": "base", "mesocycle_week": 1},
                "constraints": {"obs": "verificar red_flags"},
                "version": 1,
                "status": "draft"
            }
        if "items" not in data or not isinstance(data["items"], list):
            data["items"] = []

        return data
# ------------------------------------------
