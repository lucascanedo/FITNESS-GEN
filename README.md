# Fitness Gen

Backend para gestão de alunos, avaliações, medições e geração de planos de treino com LLM e MCP.

## Visão geral

O fluxo principal do produto é:

1. cadastrar aluno, avaliação e medição;
2. consultar contexto e memória via MCP;
3. gerar um rascunho de plano com LLM;
4. permitir edição do professor;
5. salvar o plano final e comparar LLM x professor para aprendizado futuro.

## Estrutura do backend

```text
src/
  api/                 FastAPI, rotas e contratos HTTP
  IA/                  prompt building e chamada do modelo
  core/                configuração da aplicação
  db/                  engine, schema e migrations
  mcp/                 servidor MCP e ferramentas expostas
  services/            regras de aplicação e acesso ao banco
```

### Responsabilidades

- `src/api`: camada de entrada HTTP.
- `src/services`: orquestra casos de uso, persistência SQL e análise de planos.
- `src/IA`: gera prompt e chama o modelo.
- `src/mcp`: expõe as ferramentas que a IA consulta antes de gerar o plano.
- `src/db`: infraestrutura de banco.
- `src/core`: settings e configuração global.
- `src/frontend/app.py`: app Streamlit legado/local; não é o frontend React principal.

## Estado atual da arquitetura

### O que já está alinhado

- API separada das regras de aplicação.
- MCP isolado em um servidor próprio.
- geração de contexto separada do prompt em `llm_context_service`.
- comparação LLM x professor persistida no banco.
- migration runner explícito.

### O que ainda não é Clean Architecture completa

- os services ainda misturam caso de uso com queries SQL cruas;
- ainda não existe camada de `repositories` / `ports`;
- o `mcp server` e o `llm service` ainda conhecem detalhes concretos de infraestrutura;
- não há models de domínio independentes do banco.

Em outras palavras: a base está organizada e utilizável, mas ainda é uma arquitetura em camadas pragmática, não Clean Architecture pura.

## Banco de dados

Arquivos relevantes:

- `src/db/schema.sql`
- `src/db/migrations/*.sql`
- `src/db/migrate.py`

### Rodar migrations

Banco existente:

```bash
python -m src.db.migrate
```

Criar banco e fazer bootstrap:

```bash
python -m src.db.migrate --create-db --bootstrap
```

## API

Subir a API:

```bash
uvicorn src.api.main:app --reload
```

Healthcheck:

```text
GET /healthz
```

Rotas principais:

- `/students`
- `/measurements`
- `/assessments`
- `/plans`
- `/llm/generate-plan/student/{student_id}/assessment/{assessment_id}/measurement/{measurement_id}`

## MCP server

Rodar por `stdio`:

```bash
python -m src.mcp.server
```

Ferramentas principais:

- `get_generation_context`
- `get_plan_memory`
- `get_current_student_plan`
- `get_plan_comparison`
- `get_professor_learning_diagnostics`
- `get_student_snapshot`

Fluxo recomendado para um agente:

1. chamar `get_generation_context`;
2. usar `get_plan_memory` só quando precisar de auditoria extra;
3. gerar o plano com base no contexto compacto retornado;
4. salvar o plano final via API.

## LLM

Arquivos principais:

- `src/IA/llm_generator.py`
- `src/services/llm_service.py`
- `src/services/llm_context_service.py`

O backend tenta consultar MCP antes da geração. Se o ambiente bloquear subprocesso, cai para execução `inprocess`; se isso também falhar, usa fallback direto para não quebrar a API.

## Configuração

Use `.env.example` como base para criar seu `.env`.

Variáveis mais importantes:

- `DATABASE_URL`
- `GROQ_API_KEY`
- `LLM_MODEL`
- `LLM_TEMPERATURE`
- `ALLOWED_ORIGINS`
- `MCP_SERVER_COMMAND`
- `MCP_SERVER_MODULE`
- `LLM_MCP_MODE`

### Observações sobre `.env`

- não commitar credenciais reais;
- não usar senha padrão em ambiente compartilhado;
- em produção, restringir `ALLOWED_ORIGINS`;
- se quiser evitar subprocesso MCP no backend, usar `LLM_MCP_MODE=inprocess`.

## Testes

```bash
python -m unittest tests\test_learning_context.py tests\test_mcp_server.py tests\test_llm_mcp_integration.py
```

## Próximos passos recomendados

1. extrair `repositories` para reduzir acoplamento SQL nos services.
2. separar melhor domínio de plano, aluno e avaliação em módulos próprios.
3. adicionar autenticação/autorização para acesso às rotas.
4. adicionar observabilidade mais forte para falhas de MCP e LLM.
