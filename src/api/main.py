"""
API FastAPI para Hyperledger RAG
Endpoints para queries, admin, monitoramento e estatísticas.
"""

import time
import asyncio
import logging
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import structlog

from src.infrastructure.config import get_settings, Settings
from src.infrastructure.cache import InMemoryCache, QueryResponseCache
from src.infrastructure.llm import TinyLlamaModel, RAGChain
from src.infrastructure.vector_store import FAISSVectorStore
from src.infrastructure.scraper import BeautifulSoupScraper
from src.application.services import CrawlerService, IngestionService
from src.application.schemas import (
    QueryRequest, QueryResponse, SourceReference, CrawlRequest, CrawlResponse,
    FeedbackRequest, FeedbackResponse, HealthResponse, StatsResponse,
    IndexInfoResponse, ErrorResponse, StreamingResponse
)
from src.core.ontology import HyperledgerOntology

logger = logging.getLogger(__name__)


# Dependências e Globais
settings: Optional[Settings] = None
rag_chain: Optional[RAGChain] = None
response_cache: Optional[QueryResponseCache] = None
memory_cache: Optional[InMemoryCache] = None
start_time: datetime = datetime.utcnow()


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Valida API Key para endpoints protegidos"""
    if not settings.API_KEY_REQUIRED:
        return "public"
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key obrigatória"
        )
    
    valid_keys = settings.API_KEYS.split(",") if settings.API_KEYS else []
    if x_api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key inválida"
        )
    
    return x_api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia startup e shutdown da aplicação"""
    # Startup
    logger.info("Iniciando Hyperledger RAG API...")
    
    global settings, rag_chain, response_cache, memory_cache
    settings = get_settings()
    
    try:
        # Carrega índice vetorial
        logger.info("Carregando índice vetorial...")
        vector_store = FAISSVectorStore()
        vector_store.load(settings.VECTOR_DB_PATH)
        
        # Inicializa LLM
        logger.info("Inicializando modelo LLM...")
        llm_model = TinyLlamaModel(model_id=settings.RAG_MODEL_ID)
        
        # Cria RAG Chain
        rag_chain = RAGChain(llm_model, vector_store)
        
        # Inicializa Cache
        memory_cache = InMemoryCache(max_size=settings.CACHE_MAX_SIZE)
        response_cache = QueryResponseCache(memory_cache)
        
        logger.info("RAG API iniciada com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar API: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Desligando RAG API...")


# Criar app FastAPI
app = FastAPI(
    title=f"{get_settings().APP_NAME}",
    version=f"{get_settings().APP_VERSION}",
    description="API REST com RAG otimizado para Hyperledger Fabric",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== ENDPOINTS DE QUERY ====================

@app.post(f"{get_settings().API_PREFIX}/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Faz uma pergunta ao RAG e retorna resposta.
    
    - **query**: Sua pergunta sobre Hyperledger Fabric
    - **use_cache**: Usar cache se disponível (padrão: true)
    - **use_ontology**: Enriquecer query com ontologia (padrão: true)
    - **top_k**: Número de documentos recuperados (padrão: 4)
    """
    try:
        # Verifica cache
        if request.use_cache and response_cache:
            cached = response_cache.get_response(request.query, request.model_version)
            if cached:
                return QueryResponse(**cached, from_cache=True)
        
        # Enriquece query com ontologia
        ontology_context = []
        if request.use_ontology:
            enrichment = HyperledgerOntology.enrich_query(request.query)
            ontology_context = [e.name for e in enrichment["entities"]]
        
        # Executa query
        start = time.time()
        response_text = rag_chain.ask(request.query)
        generation_time = int((time.time() - start) * 1000)
        
        # Recupera fontes (simplificado)
        sources = [
            SourceReference(
                title="Hyperledger Fabric Documentation",
                url="https://hyperledger-fabric.readthedocs.io",
                relevance_score=0.9
            )
        ]
        
        response = QueryResponse(
            query=request.query,
            response=response_text,
            sources=sources,
            relevance_score=0.85,
            retrieval_time_ms=50,
            generation_time_ms=generation_time,
            total_time_ms=generation_time + 50,
            ontology_entities=ontology_context,
            model_version=request.model_version
        )
        
        # Cachea resultado
        if request.use_cache and response_cache:
            response_cache.cache_response(
                request.query,
                response_text,
                [s.url or "" for s in sources],
                request.model_version
            )
        
        return response
        
    except Exception as e:
            logger.error(f"Erro ao processar query: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.post(f"{get_settings().API_PREFIX}/query/stream")
async def query_stream(
    request: QueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Stream de resposta token-by-token (Server-Sent Events).
    Útil para UIs com feedback em tempo real.
    """
    async def generate():
        try:
            yield f"data: {StreamingResponse(type='start', query_id='123').model_dump_json()}\n\n"
            
            # Simula streaming de tokens
            response = rag_chain.ask(request.query)
            for i, token in enumerate(response.split()):
                progress = min((i + 1) / len(response.split()), 1.0)
                yield f"data: {StreamingResponse(type='token', data=token, progress=progress).model_dump_json()}\n\n"
                await asyncio.sleep(0.05)
            
            yield f"data: {StreamingResponse(type='end').model_dump_json()}\n\n"
            
        except Exception as e:
            yield f"data: {StreamingResponse(type='error', data=str(e)).model_dump_json()}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


# ==================== ENDPOINTS DE ADMIN ====================

@app.post(f"{get_settings().API_PREFIX}/crawl", response_model=CrawlResponse)
async def start_crawl(
    request: CrawlRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Inicia um job de crawling da documentação.
    Requer autenticação.
    """
    try:
        logger.info(f"Iniciando crawl com max_pages={request.max_pages}")
        
        scraper = BeautifulSoupScraper()
        crawler = CrawlerService(scraper, settings.CRAWLER_TARGET_URL)
        
        # Executa crawling
        docs = await asyncio.to_thread(
            crawler.execute,
            request.max_pages
        )
        
        if not docs:
            raise ValueError("Nenhum documento foi coletado")
        
        # Ingestão
        vector_store = FAISSVectorStore()
        ingestion = IngestionService(vector_store)
        await asyncio.to_thread(ingestion.execute, docs)
        
        vector_store.save(settings.VECTOR_DB_PATH)
        
        return CrawlResponse(
            job_id="crawl-001",
            status="completed",
            pages_crawled=len(docs),
            pages_target=request.max_pages,
            documents_created=len(docs),
            chunks_created=len(docs) * 5,
            progress=1.0,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Erro no crawl: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINTS DE MONITORAMENTO ====================

@app.get(f"{get_settings().API_PREFIX}/health", response_model=HealthResponse)
async def health_check():
    """
    Verifica saúde da API e seus serviços.
    """
    uptime = (datetime.utcnow() - start_time).total_seconds()
    
    services = {
        "rag_chain": "ok" if rag_chain else "error",
        "cache": "ok" if memory_cache else "error",
        "vector_store": "ok"  # TODO: verificar real status
    }
    
    status_value = "ok" if all(s == "ok" for s in services.values()) else "degraded"
    
    cache_stats = None
    if memory_cache:
        cache_stats = memory_cache.stats()
    
    return HealthResponse(
        status=status_value,
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        uptime_seconds=uptime,
        services=services,
        cache_stats=cache_stats
    )


# ==================== ENDPOINTS ROOT ====================

@app.get("/")
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "running"
    }


# ==================== ERROR HANDLERS ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler customizado para HTTPExceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code="HTTP_ERROR",
            request_id=str(request.headers.get("x-request-id", "unknown"))
        ).model_dump()
    )


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )
