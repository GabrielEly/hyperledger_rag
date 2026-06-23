"""
Script de teste da API RAG - Fases 1, 2, 3
Testa todos os endpoints principais
"""

import requests
import json
import time
from typing import Dict, Any
import asyncio

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "sk-rag-demo-key-123"
TIMEOUT = 100  # Timeout padrão para requisições

class RAGAPITester:
    def __init__(self, base_url: str = BASE_URL, api_key: str = API_KEY):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.results = []
    
    def _headers(self, with_auth: bool = True) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if with_auth:
            headers["X-API-Key"] = self.api_key
        return headers
    
    def _print_result(self, test_name: str, success: bool, message: str = "", data: Any = None):
        status = "PASS" if success else "FAIL"
        print(f"\n{status} | {test_name}")
        if message:
            print(f"   → {message}")
        if data and isinstance(data, dict):
            print(f"   → {json.dumps(data, indent=2)[:200]}...")
        
        self.results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def test_health_check(self):
        """Teste: Health Check (sem autenticação)"""
        try:
            response = requests.get(f"{self.base_url}/health")
            success = response.status_code == 200
            data = response.json()
            self._print_result(
                "Health Check",
                success,
                f"Status: {data.get('status', 'unknown')}",
                data
            )
        except Exception as e:
            self._print_result("Health Check", False, str(e))
    
    def test_simple_query(self):
        """Teste: Query Simples com Cache"""
        try:
            payload = {
                "query": "O que é um peer no Hyperledger Fabric?",
                "use_cache": True,
                "use_ontology": True,
                "top_k": 4
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/query",
                headers=self._headers(),
                json=payload,
                timeout=TIMEOUT
            )
            latency = (time.time() - start_time) * 1000
            
            success = response.status_code == 200
            data = response.json()
            
            self._print_result(
                "Simple Query",
                success,
                f"Latency: {latency:.0f}ms | Cache: {data.get('from_cache', False)} | Entities: {data.get('ontology_entities', [])}",
                data
            )
            
            return data if success else None
        except Exception as e:
            self._print_result("Simple Query", False, str(e))
            return None
    
    def test_query_with_cache(self):
        """Teste: Query com Cache (deve ser mais rápida)"""
        try:
            payload = {
                "query": "O que é chaincode?",
                "use_cache": True,
                "use_ontology": False
            }
            
            # Primeira query (será cacheada)
            response1 = self.session.post(
                f"{self.base_url}/query",
                headers=self._headers(),
                json=payload,
                timeout=TIMEOUT
            )
            time1 = response1.json().get("total_time_ms", 0)
            cached1 = response1.json().get("from_cache", False)
            print(f"1ª query: {time1}ms | Cached: {cached1}")

            # Segunda query (deve vir do cache)
            time.sleep(5)
            response2 = self.session.post(
                f"{self.base_url}/query",
                headers=self._headers(),
                json=payload,
                timeout=TIMEOUT
            )
            time2 = response2.json().get("total_time_ms", 0)
            cached2 = response2.json().get("from_cache", False)
            print(f"2ª query: {time2}ms | Cached: {cached2}")

            speedup = time1 / max(time2, 1)
            success = time2 < time1
            
            self._print_result(
                "Cache Performance",
                success,
                f"1ª query: {time1}ms | 2ª query: {time2}ms | Speedup: {speedup:.1f}x | Cached: {cached2}",
                {"first_response_time_ms": time1, "cached_response_time_ms": time2}
            )
        except Exception as e:
            self._print_result("Cache Performance", False, str(e))
    
    def test_ontology_enrichment(self):
        """Teste: Enriquecimento com Ontologia"""
        try:
            payload = {
                "query": "peer orderer chaincode",
                "use_ontology": True
            }
            
            response = self.session.post(
                f"{self.base_url}/query",
                headers=self._headers(),
                json=payload,
                timeout=TIMEOUT
            )
            
            data = response.json()
            entities = data.get("ontology_entities", [])
            success = len(entities) > 0 and response.status_code == 200
            
            self._print_result(
                "Ontology Enrichment",
                success,
                f"Entities found: {entities}",
                data
            )
        except Exception as e:
            self._print_result("Ontology Enrichment", False, str(e))
    
    def test_streaming_query(self):
        """Teste: Query com Streaming SSE"""
        try:
            payload = {
                "query": "Explique blockchain",
                "stream": True
            }
            
            response = self.session.post(
                f"{self.base_url}/query/stream",
                headers=self._headers(),
                json=payload,
                timeout=TIMEOUT,
                stream=True
            )
            
            success = response.status_code == 200
            tokens_received = 0
            
            for line in response.iter_lines():
                if line and line.startswith(b'data:'):
                    tokens_received += 1
            
            success = success and tokens_received > 0
            
            self._print_result(
                "Streaming Query",
                success,
                f"Received {tokens_received} SSE events",
                {"tokens": tokens_received}
            )
        except Exception as e:
            self._print_result("Streaming Query", False, str(e))
    
    
    def test_crawl_job(self):
        """Teste: Iniciar Job de Crawl (Fase 2 - Admin)"""
        try:
            payload = {
                "max_pages": 5,
                "force_refresh": False
            }
            
            response = self.session.post(
                f"{self.base_url}/crawl",
                headers=self._headers(),
                json=payload,
                timeout=TIMEOUT*5  # Long timeout para crawl
            )
            
            success = response.status_code == 200
            data = response.json()
            
            self._print_result(
                "Crawl Job",
                success,
                f"Job ID: {data.get('job_id', 'N/A')} | Pages crawled: {data.get('pages_crawled', 0)}",
                data
            )
        except Exception as e:
            self._print_result("Crawl Job", False, str(e))
    
    def test_auth_required(self):
        """Teste: Verificar se autenticação é obrigatória"""
        try:
            # Tenta fazer query sem API Key
            response = self.session.post(
                f"{self.base_url}/query",
                json={"query": "test"},
                timeout=TIMEOUT
            )
            
            # Espera 401 Unauthorized
            success = response.status_code == 401
            
            self._print_result(
                "Authentication Requirement",
                success,
                f"Status code: {response.status_code} (esperado 401)"
            )
        except Exception as e:
            self._print_result("Authentication Requirement", False, str(e))
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("\n" + "="*60)
        print("HYPERLEDGER RAG API - TEST SUITE")
        print("="*60)
        
        tests = [
            ("BASIC", [
                self.test_health_check,
                #self.test_auth_required, #Só caso enviroment == production
            ]),
            ("FASE 1 - API & CACHE", [
                self.test_simple_query,
                self.test_query_with_cache,
                self.test_ontology_enrichment,
                self.test_streaming_query,
            ]),
        ]
        
        for category, test_list in tests:
            print(f"\n{'='*60}")
            print(f"{category}")
            print(f"{'='*60}")
            
            for test in test_list:
                try:
                    test()
                except Exception as e:
                    print(f"ERRO: {test.__name__} - {str(e)}")
        
        # Resumo
        print(f"\n{'='*60}")
        print("RESUMO DOS TESTES")
        print(f"{'='*60}")
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed
        
        print(f"Total: {total} | Passou: {passed} | Falhou: {failed}")
        print(f"Taxa de sucesso: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\nTestes falhados:")
            for r in self.results:
                if not r["success"]:
                    print(f"  - {r['test']}: {r['message']}")
        else:
            print("\n🎉 Todos os testes passaram!")


if __name__ == "__main__":
    print("Iniciando testes da API...")
    print(f"Base URL: {BASE_URL}")
    print(f"Aguarde 2 segundos para conectar...\n")
    
    time.sleep(2)
    
    tester = RAGAPITester()
    tester.run_all_tests()
