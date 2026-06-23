# 🚀 Quick Start - Hyperledger RAG API

## ⚡ Iniciar Rápido (5 minutos)

### Fase 1: API Local (Sem Docker)

```bash
# 1. Clone e entre no diretório
cd hyperledger_rag-main

# 2. Crie um ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Instale dependências
pip install -r requirements.txt

# 4. Se não tiver índice, faça crawl
python src/main.py crawl --pages 50

# 5. Inicie a API
uvicorn src.api.main:app --reload

# 6. Acesse:
# - API Docs: http://localhost:8000/docs
# - Health: http://localhost:8000/api/v1/health
```

**Teste com curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "O que é Hyperledger?"}'
```

---

### Fase 2: Com Docker Compose (Simplificado)

```bash
# 1. Entre no diretório
cd hyperledger_rag-main

# 2. Inicie o serviço
docker-compose up -d

# 3. Aguarde inicialização (30-40s)
docker-compose logs -f rag-api

# 4. Acesse:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
```

**Teste:**
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "X-API-Key: sk-rag-demo-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "O que é um peer?",
    "use_ontology": true
  }'
```

---

## 📋 Arquitetura Atual

### ✅ **FastAPI + RAG Otimizado**
- API REST completa
- Ontologia do Hyperledger (16 entidades)
- Cache em memória
- WebSocket para streaming
- Validação com Pydantic

### 🐳 **Docker**
- Containerização da API
- Docker Compose para execução simplificada
- Documentação completa

---

## 📚 Documentação

- **SETUP_GUIDE.md**: Guia completo com todas as 3 fases
- **Swagger Docs**: `/docs` na API
- **ReDoc**: `/redoc` na API

---

## 🔗 Principais Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/query` | Query ao RAG |
| POST | `/api/v1/query/stream` | Streaming SSE |
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/feedback` | Enviar feedback |
| GET | `/api/v1/stats` | Estatísticas |
| POST | `/api/v1/crawl` | Admin: Fazer crawl |

---

## 🐳 Comandos Docker Úteis

```bash
# Ver logs
docker-compose logs -f rag-api

# Entrar no container
docker-compose exec rag-api bash

# Fazer crawl
docker-compose exec rag-api python src/main.py crawl --pages 100

# Parar
docker-compose down

# Limpar tudo
docker-compose down -v
```

---

## 🧪 Testar API

```bash
# Rodar suite de testes
python test_api.py

# Ou teste específico
curl "http://localhost:8000/api/v1/health"
```

---

## 🔑 Variáveis de Ambiente Principais

```bash
ENVIRONMENT=development          # development, staging, production
API_PORT=8000                   # Porta da API
API_KEY_REQUIRED=false          # Require API keys
```

Veja `.env` para todas as opções.

---

## ⚠️ Troubleshooting

### Erro: "FAISS index not found"
```bash
python src/main.py crawl --pages 50
```

### Erro: "Porta 8000 já em uso"
```bash
# Mudar porta em .env
API_PORT=8001
```

---

## 🎯 Stack

- **Backend**: FastAPI + Uvicorn
- **RAG**: LangChain + FAISS + TinyLlama
- **Container**: Docker + Docker Compose

---

**Versão**: 1.0.0
