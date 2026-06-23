import sys
from pathlib import Path

# sobe três níveis: test/ontology/test.py -> projeto
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from src.core.ontology import HyperledgerOntology

# Enriquecer query
query = "Como funciona o consensus entre peers?"
enrichment = HyperledgerOntology.enrich_query(query)

print("Entities found:", enrichment["entities"])
print("Related context:", enrichment["related_context"])
print("Enrichment score:", enrichment["enrichment_score"])

# Buscar entidade específica
peer = HyperledgerOntology.get_entity("peer")
print(f"\n{peer.name}")
print(f"Description: {peer.description}")
print(f"Aliases: {peer.aliases}")
print(f"Related to: {peer.related_to}")