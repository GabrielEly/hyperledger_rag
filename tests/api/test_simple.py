import requests

BASE_URL = "http://localhost:8000/api/v1"

# Query simples
response = requests.post(
    f"{BASE_URL}/query",
    json={
        "query": "O que é um peer no Hyperledger?",
        "use_ontology": True,
        "use_cache": True,
        "top_k": 4
    }
)

print(response.json())