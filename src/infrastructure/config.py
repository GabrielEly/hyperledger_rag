"""
Configurações centralizadas da aplicação.
Suporta variáveis de ambiente e diferentes ambientes (dev, staging, prod).
"""

from pydantic_settings import BaseSettings
from typing import Optional, Literal
import os
from functools import lru_cache

class Settings(BaseSettings):
    """Configurações da aplicação"""
    # Compatibilidade: variáveis de ambiente extras serão ignoradas
    
    # Aplicação
    APP_NAME: str = "Hyperledger RAG API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_PREFIX: str = "/api/v1"
    WORKERS: int = int(os.getenv("WORKERS", "4"))
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100  # requests
    RATE_LIMIT_PERIOD: int = 60     # seconds
    
    # Auth
    API_KEY_REQUIRED: bool = os.getenv("API_KEY_REQUIRED", "true").lower() == "true"
    API_KEYS: str = os.getenv("API_KEYS", "")  # comma-separated
    
    # RAG Configuration
    RAG_MODEL_ID: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-l6-v2"
    VECTOR_DB_PATH: str = "faiss_index_v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 100
    RETRIEVAL_K: int = 4  # número de documentos recuperados
    
    # LLM Parameters
    LLM_MAX_TOKENS: int = 512
    LLM_TEMPERATURE: float = 0.7
    LLM_TOP_K: int = 50
    LLM_TOP_P: float = 0.95
    LLM_DO_SAMPLE: bool = True
    
    # Cache
    # Aceita qualquer string para compatibilidade com valores antigos (será normalizado em runtime)
    CACHE_BACKEND: str = os.getenv("CACHE_BACKEND", "memory")
    CACHE_ENABLED: bool = True
    CACHE_TTL_RESPONSES: int = 86400      # 24 horas
    CACHE_TTL_EMBEDDINGS: int = 2592000   # 30 dias
    CACHE_MAX_SIZE: int = 10000           # para in-memory
    
    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", None)
    
    # WebSocket
    WEBSOCKET_ENABLED: bool = True
    WEBSOCKET_PING_INTERVAL: int = 30  # segundos
    
    # Crawling
    CRAWLER_TARGET_URL: str = "https://hyperledger-fabric.readthedocs.io/en/latest/"
    CRAWLER_MAX_PAGES: int = 100
    CRAWLER_TIMEOUT: int = 30
    CRAWLER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância única de configurações (singleton)"""
    s = Settings()
    # Garantir compatibilidade: forçar backend de cache para memory após remoção do Redis/híbrido
    try:
        s.CACHE_BACKEND = "memory"
    except Exception:
        pass
    return s


# Presets para diferentes ambientes
ENVIRONMENT_PRESETS = {
    "development": {
        "DEBUG": True,
        "LOG_LEVEL": "DEBUG",
        "WORKERS": 1,
    },
    "staging": {
        "DEBUG": False,
        "LOG_LEVEL": "INFO",
        "WORKERS": 2,
        "API_KEY_REQUIRED": True,
    },
    "production": {
        "DEBUG": False,
        "LOG_LEVEL": "WARNING",
        "WORKERS": 8,
        "API_KEY_REQUIRED": True,
        "RATE_LIMIT_ENABLED": True,
    }
}
