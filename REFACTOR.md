# Refatoração FITNESS-GEN

## O que foi preservado

- **Backend FastAPI** em `src/api/main.py` com CORS, middleware de correlation_id e registro de routers
- **Rotas existentes**: students, assessments, measurements, plans, llm — mesmos endpoints
- **Schemas Pydantic** de Student, Assessment, Measurement, Plan (com extensões)
- **LLM**: `src/IA/llm_helpers.py` e `src/IA/llm_generator.py` — mesma integração Groq
- **Fluxo de geração**: POST `/llm/generate-plan/...` retorna rascunho; POST `/plans/` persiste o plano editado
- **Validação de FKs** (student/assessment/measurement coerentes)

## O que mudou

### Banco de dados
- **plans**: novos campos `generated_plan_json`, `llm_call_id`, `edit_count`, `updated_at`
- **plan_versions**: nova tabela para histórico de versões (source: llm | teacher)
- **llm_calls**: nova tabela (se não existia) para auditoria
- **assessments**: colunas adicionadas: case_notes, equipment, red_flags, readiness, periodization, status

### Arquitetura
- **Camada de serviços** em `src/services/`:
  - `student_service`, `assessment_service`, `measurement_service`
  - `plan_service` — create_plan, create_plan_from_llm, update_plan, create_plan_version, get_student_plans
  - `plan_analysis_service` — analyze_plan_differences, get_professor_edit_patterns, build_llm_learning_context
  - `llm_service` — build_generation_context, generate_plan_with_learning_context, log_llm_call

### Rotas (thin layer)
- Rotas delegam para services; sem lógica de negócio
- `PlanGenerationResponse` — resposta inclui `llm_call_id` para vincular ao salvar
- Novos endpoints: `GET /plans/{id}/analysis`, `GET /plans/edit-patterns?student_id=`

### LLM e aprendizado
- O prompt recebe `_learning_context` quando há histórico de edições do treinador
- O LLM **não** consulta o banco; o backend injeta o contexto no prompt

### Frontend
- Novo frontend React + TypeScript em `frontend/` (Vite)
- Páginas: /login, /dashboard, /students, /students/new, /students/:id, /students/:id/plan/new, /plans/:id/edit
- Estrutura: api/, types/, pages/, components/, context/

## Migração de banco existente

```bash
psql -U postgres -d fitnessgen -f src/db/migrations/001_plan_versioning.sql
```

Para instalação nova, use `src/db/schema.sql` completo.

## Como rodar

### Backend
```bash
cd "c:\Users\Lucas\OneDrive - Globalweb\Documentos\PROJETOS\FITNESS-GEN"
uv run uvicorn src.api.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

O frontend roda em http://localhost:5173 e faz proxy de `/api` para `http://127.0.0.1:8000`.

### Login
Use qualquer email e senha (demo; não há autenticação real ainda).

## O que falta implementar

- Autenticação real (JWT/sessão) no backend e frontend
- Testes automatizados
- CRUD de assessments e measurements no frontend (tabs do aluno)
- Interface mais rica para edição de planos (arrastar exercícios, etc.)
- MCP (preparado na arquitetura, não implementado)
