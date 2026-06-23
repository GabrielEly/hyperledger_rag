"""
WebSocket para comunicação bidirecional e streaming de respostas em tempo real.
"""

import json
import asyncio
import logging
from typing import Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Gerencia conexões WebSocket"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Envia mensagem para todas as conexões ativas"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem: {e}")
                disconnected.append(connection)
        
        # Remove conexões mortas
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """Envia mensagem para uma conexão específica"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem pessoal: {e}")


manager = ConnectionManager()


async def handle_rag_query_websocket(websocket: WebSocket, rag_chain, response_cache):
    """
    Handler para WebSocket de queries ao RAG.
    
    Protocolo:
    1. Client envia: {"type": "query", "query": "...", "use_cache": true}
    2. Server responde com tokens:
       - {"type": "start", "query_id": "..."}
       - {"type": "token", "data": "...", "progress": 0.5}
       - {"type": "end", "query_id": "..."}
       - {"type": "error", "error": "..."}
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Recebe mensagem do cliente
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            
            if msg_type == "query":
                await handle_query_message(websocket, message, rag_chain, response_cache)
            
            elif msg_type == "ping":
                await manager.send_personal(websocket, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            else:
                await manager.send_personal(websocket, {
                    "type": "error",
                    "error": f"Tipo de mensagem desconhecido: {msg_type}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket desconectado")
    
    except Exception as e:
        logger.error(f"Erro no WebSocket: {e}")
        manager.disconnect(websocket)


async def handle_query_message(websocket: WebSocket, message: dict, rag_chain, response_cache):
    """Processa mensagem de query via WebSocket"""
    try:
        query = message.get("query")
        use_cache = message.get("use_cache", True)
        model_version = message.get("model_version", "v1")
        
        if not query:
            await manager.send_personal(websocket, {
                "type": "error",
                "error": "Query é obrigatória"
            })
            return
        
        # Verifica cache
        if use_cache and response_cache:
            cached = response_cache.get_response(query, model_version)
            if cached:
                await manager.send_personal(websocket, {
                    "type": "start",
                    "query_id": "cached",
                    "from_cache": True
                })
                
                await manager.send_personal(websocket, {
                    "type": "response",
                    "data": cached["response"],
                    "progress": 1.0,
                    "from_cache": True
                })
                
                await manager.send_personal(websocket, {"type": "end"})
                return
        
        # Envia start
        await manager.send_personal(websocket, {
            "type": "start",
            "query_id": "ws-query-001",
            "from_cache": False
        })
        
        # Executa query em thread separada
        response = await asyncio.to_thread(rag_chain.ask, query)
        
        # Streaming de tokens
        tokens = response.split()
        for i, token in enumerate(tokens):
            progress = (i + 1) / len(tokens)
            
            await manager.send_personal(websocket, {
                "type": "token",
                "data": token,
                "progress": progress
            })
            
            # Pequeno delay para simular streaming
            await asyncio.sleep(0.01)
        
        # Envia end
        await manager.send_personal(websocket, {
            "type": "end",
            "query_id": "ws-query-001"
        })
        
        # Cachea resultado
        if use_cache and response_cache:
            response_cache.cache_response(query, response, [], model_version)
    
    except Exception as e:
        logger.error(f"Erro ao processar query via WebSocket: {e}")
        await manager.send_personal(websocket, {
            "type": "error",
            "error": str(e)
        })


# Cliente WebSocket Python para teste
class RAGWebSocketClient:
    """Cliente para conectar ao RAG via WebSocket"""
    
    def __init__(self, url: str = "ws://localhost:8000/api/v1/ws"):
        self.url = url
        self.websocket = None
    
    async def connect(self):
        """Conecta ao servidor"""
        try:
            import websockets
            self.websocket = await websockets.connect(self.url)
            logger.info(f"Conectado ao servidor WebSocket: {self.url}")
        except Exception as e:
            logger.error(f"Erro ao conectar WebSocket: {e}")
            raise
    
    async def query(self, query_text: str, use_cache: bool = True):
        """Envia query e recebe resposta em streaming"""
        if not self.websocket:
            raise Exception("Não conectado ao servidor")
        
        # Envia query
        await self.websocket.send(json.dumps({
            "type": "query",
            "query": query_text,
            "use_cache": use_cache
        }))
        
        # Recebe respostas
        while True:
            message = await self.websocket.recv()
            data = json.loads(message)
            
            msg_type = data.get("type")
            
            if msg_type == "start":
                print(f"🚀 Iniciando resposta...")
            
            elif msg_type == "token":
                print(data.get("data"), end=" ", flush=True)
            
            elif msg_type == "end":
                print("\n✅ Resposta concluída")
                break
            
            elif msg_type == "error":
                print(f"\n❌ Erro: {data.get('error')}")
                break
    
    async def disconnect(self):
        """Desconecta do servidor"""
        if self.websocket:
            await self.websocket.close()


# Exemplo de uso
async def example_websocket_client():
    """Exemplo de uso do cliente WebSocket"""
    client = RAGWebSocketClient()
    
    try:
        await client.connect()
        
        # Faz uma query
        await client.query("O que é um blockchain?")
        
        # Outra query
        await client.query("Como funciona o Hyperledger Fabric?")
    
    finally:
        await client.disconnect()


if __name__ == "__main__":
    # Para testar: python -m src.api.websocket
    asyncio.run(example_websocket_client())
