"""
Cache Manager - Suporta em memória, Redis e hibridez.
Otimiza performance reduzindo latência de embeddings e respostas.
"""

import json
import hashlib
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheBackend(ABC):
    """Interface abstrata para diferentes backends de cache"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 3600):
        pass
    
    @abstractmethod
    def delete(self, key: str):
        pass
    
    @abstractmethod
    def clear(self):
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        pass


class InMemoryCache(CacheBackend):
    """Cache em memória com TTL e limite de tamanho"""
    
    def __init__(self, max_size: int = 10000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            entry = self.cache[key]
            if entry["expires"] > time.time():
                self.hits += 1
                return entry["value"]
            else:
                del self.cache[key]
                self.misses += 1
                return None
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        if len(self.cache) >= self.max_size:
            # Remove entradas expiradas
            self.cache = {
                k: v for k, v in self.cache.items() 
                if v["expires"] > time.time()
            }
        
        self.cache[key] = {
            "value": value,
            "expires": time.time() + ttl,
            "created": datetime.now()
        }
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def exists(self, key: str) -> bool:
        return self.get(key) is not None
    
    def stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "size": len(self.cache),
            "max_size": self.max_size
        }


class QueryResponseCache:
    """Cache específico para respostas de queries com otimizações"""
    
    def __init__(self, backend: CacheBackend):
        self.backend = backend
    
    @staticmethod
    def _generate_key(query: str, model_version: str = "v1") -> str:
        """Gera chave única para query normalizada"""
        normalized = query.lower().strip()
        query_hash = hashlib.md5(normalized.encode()).hexdigest()
        return f"query:{model_version}:{query_hash}"
    
    def get_response(self, query: str, model_version: str = "v1") -> Optional[Dict[str, Any]]:
        """Recupera resposta cacheada"""
        key = self._generate_key(query, model_version)
        return self.backend.get(key)
    
    def cache_response(
        self,
        query: str,
        response: str,
        sources: List[Dict[str, Any]],
        model_version: str = "v1",
        relevance_score: float = 0.0,
        retrieval_time_ms: int = 0,
        generation_time_ms: int = 0,
        total_time_ms: int = 0,
        ontology_entities: Optional[List[str]] = None,
        ttl: int = 86400  # 24 horas
    ):
        """Armazena resposta em cache"""
        key = self._generate_key(query, model_version)
        cached_data = {
            "query": query,
            "response": response,
            "sources": sources,
            "relevance_score": relevance_score,
            "retrieval_time_ms": retrieval_time_ms,
            "generation_time_ms": generation_time_ms,
            "total_time_ms": total_time_ms,
            "ontology_entities": ontology_entities or [],
            "model_version": model_version,
            "timestamp": datetime.now().isoformat(),
        }
        self.backend.set(key, cached_data, ttl)
    
    def invalidate(self, query: str, model_version: str = "v1"):
        """Invalida cache de uma query"""
        key = self._generate_key(query, model_version)
        self.backend.delete(key)


class EmbeddingCache:
    """Cache específico para embeddings de documentos"""
    
    def __init__(self, backend: CacheBackend):
        self.backend = backend
    
    @staticmethod
    def _generate_key(text: str, model_name: str = "default") -> str:
        """Gera chave única para texto/modelo"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"embedding:{model_name}:{text_hash}"
    
    def get_embedding(self, text: str, model_name: str = "default") -> Optional[List[float]]:
        """Recupera embedding cacheado"""
        key = self._generate_key(text, model_name)
        return self.backend.get(key)
    
    def cache_embedding(self, text: str, embedding: List[float], model_name: str = "default"):
        """Armazena embedding em cache"""
        key = self._generate_key(text, model_name)
        self.backend.set(key, embedding, ttl=86400 * 30)  # 30 dias
    
    def batch_cache(self, texts: Dict[str, List[float]], model_name: str = "default"):
        """Armazena múltiplos embeddings em cache"""
        for text, embedding in texts.items():
            self.cache_embedding(text, embedding, model_name)
