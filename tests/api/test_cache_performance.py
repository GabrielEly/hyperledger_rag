import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

query = "O que é um chaincode?"

# Primeira query (sem cache)
print("1ª Query (sem cache)...")
start = time.time()
r1 = requests.post(f"{BASE_URL}/query", json={"query": query, "use_cache": False, "use_ontology": True, "top_k": 4})
time1 = time.time() - start
print(f"Tempo: {time1:.2f}s | From cache: {r1.json()['from_cache']}")

# Segunda query (com cache)
print("\n2ª Query (com cache)...")
start = time.time()
r2 = requests.post(f"{BASE_URL}/query", json={"query": query, "use_cache": True, "use_ontology": True, "top_k": 4})
time2 = time.time() - start
print(f"Tempo: {time2:.2f}s | From cache: {r2.json()['from_cache']}")

# Speedup
speedup = time1 / time2
print(f"\n⚡ Speedup: {speedup:.1f}x mais rápido com cache!")