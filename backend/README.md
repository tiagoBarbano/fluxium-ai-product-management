# Fluxium backend

## Ambiente local

Suba a infraestrutura a partir da raiz do projeto:

```bash
docker compose -f docker/docker-compose.infra.yml up -d mongo redis ollama
```

Instale as dependências e crie o lockfile com UV:

```bash
cd backend
uv sync --dev
```

Execute a API:

```bash
uv run uvicorn app.main:app --reload
```

O health check fica disponível em `http://localhost:8000/api/v1/health`.