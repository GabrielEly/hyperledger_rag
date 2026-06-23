"""
Esquemas Pydantic para validação de requisições/respostas da API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class QueryRequest(BaseModel):
    """Request para fazer uma query ao RAG"""
    query: str = Field(..., min_length=3, max_length=1000, description="Pergunta para o RAG")
    model_version: str = Field(default="v1", description="Versão do modelo a usar")
    use_cache: bool = Field(default=True, description="Usar cache se disponível")
    use_ontology: bool = Field(default=True, description="Enriquecer com ontologia")
    top_k: int = Field(default=4, min_value=1, max_value=10, description="Top K documentos a recuperar")
    stream: bool = Field(default=False, description="Streaming de resposta")
    
    class Config:
        example = {
            "query": "O que é um chaincode no Hyperledger Fabric?",
            "use_cache": True,
            "use_ontology": True,
            "top_k": 4
        }


class SourceReference(BaseModel):
    """Referência a um documento/fonte"""
    title: str
    url: Optional[str] = None
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    snippet: Optional[str] = None


class QueryResponse(BaseModel):
    """Response com resposta do RAG"""
    query: str
    response: str
    sources: List[SourceReference]
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    retrieval_time_ms: int
    generation_time_ms: int
    total_time_ms: int
    from_cache: bool = False
    ontology_entities: List[str] = Field(default_factory=list)
    model_version: str
    
    class Config:
        example = {
            "query": "O que é um chaincode?",
            "response": "Um chaincode é um programa (smart contract)...",
            "sources": [
                {
                    "title": "Chaincodes Introduction",
                    "url": "https://example.com/chaincodes",
                    "relevance_score": 0.95,
                    "snippet": "Chaincode is business logic..."
                }
            ],
            "relevance_score": 0.92,
            "retrieval_time_ms": 45,
            "generation_time_ms": 1230,
            "total_time_ms": 1275,
            "from_cache": False,
            "ontology_entities": ["chaincode", "peer", "transaction"],
            "model_version": "v1"
        }


class StreamingResponse(BaseModel):
    """Response para streaming de respostas"""
    type: str = Field(..., description="'start', 'token', 'end', 'error'")
    data: Optional[str] = None
    query_id: Optional[str] = None
    progress: Optional[float] = None  # 0.0 a 1.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FeedbackRequest(BaseModel):
    """Request para enviar feedback sobre uma resposta"""
    query_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating de 1 a 5 stars")
    was_helpful: bool
    comment: Optional[str] = None
    suggested_improvement: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Response confirmando feedback recebido"""
    success: bool
    message: str
    feedback_id: str


class CrawlRequest(BaseModel):
    """Request para iniciar um job de crawling"""
    max_pages: int = Field(default=100, ge=1, le=1000)
    force_refresh: bool = Field(default=False, description="Faz re-crawl mesmo se já existe índice")


class CrawlResponse(BaseModel):
    """Response do status de crawling"""
    job_id: str
    status: str  # pending, running, completed, failed
    pages_crawled: int
    pages_target: int
    documents_created: int
    chunks_created: int
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class HealthResponse(BaseModel):
    """Response de health check"""
    status: str  # ok, degraded, error
    version: str
    timestamp: datetime
    uptime_seconds: float
    services: Dict[str, str]  # service_name -> status
    cache_stats: Optional[Dict[str, Any]] = None


class StatsResponse(BaseModel):
    """Response com estatísticas de uso"""
    total_queries: int
    total_responses: int
    average_response_time_ms: float
    cache_hit_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    active_sessions: int
    total_documents_indexed: int
    total_chunks_indexed: int
    ontology_entities_indexed: int
    disk_usage_mb: float
    last_crawl_time: Optional[datetime] = None
    
    class Config:
        example = {
            "total_queries": 1250,
            "total_responses": 1250,
            "average_response_time_ms": 1850.5,
            "cache_hit_rate": 0.34,
            "active_sessions": 12,
            "total_documents_indexed": 450,
            "total_chunks_indexed": 4500,
            "ontology_entities_indexed": 16,
            "disk_usage_mb": 250.5
        }


class IndexInfoResponse(BaseModel):
    """Informações sobre o índice vetorial"""
    status: str  # exists, not_found, corrupted
    total_documents: int
    total_chunks: int
    dimensions: int
    memory_usage_mb: float
    created_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    model_version: str


class ErrorResponse(BaseModel):
    """Response padrão para erros"""
    error: str
    detail: Optional[str] = None
    error_code: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


# Enums
class DocumentSortBy(str, Enum):
    """Ordenação de documentos nos resultados"""
    relevance = "relevance"
    date = "date"
    popularity = "popularity"


class OntologyContext(str, Enum):
    """Contextos temáticos da ontologia"""
    architecture = "architecture"
    smart_contracts = "smart_contracts"
    security = "security"
    consensus = "consensus"
    networking = "networking"
