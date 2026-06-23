"""
Ontologia do Hyperledger Fabric - Define conceitos-chave e relações semânticas.
Otimiza busca e contexto das respostas.
"""

from typing import Dict, List, Set
from dataclasses import dataclass, field

@dataclass
class OntologyEntity:
    """Entidade da ontologia com propriedades e relações"""
    name: str
    description: str
    aliases: List[str] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)
    related_to: Set[str] = field(default_factory=set)

class HyperledgerOntology:
    """Ontologia centralizada do Hyperledger Fabric"""
    
    ENTITIES = {
        # Componentes Principais
        "peer": OntologyEntity(
            name="Peer",
            description="Nó que mantém uma cópia do ledger e executa chaincodes",
            aliases=["nó peer", "nó de validação", "validador"],
            properties={
                "maintains_ledger": "true",
                "executes_chaincode": "true",
                "role": "ledger_keeper"
            },
            related_to={"channel", "chaincode", "ledger", "msp"}
        ),
        "orderer": OntologyEntity(
            name="Orderer",
            description="Serviço que ordena transações em blocos",
            aliases=["serviço de ordenação", "nó ordenador", "ordering_service"],
            properties={
                "orders_transactions": "true",
                "creates_blocks": "true",
                "role": "ordering"
            },
            related_to={"channel", "block", "transaction", "consensus"}
        ),
        "channel": OntologyEntity(
            name="Channel",
            description="Sub-rede privada onde peers e orderers se comunicam",
            aliases=["canal", "sub-rede", "private_network"],
            properties={
                "is_private": "true",
                "isolates_data": "true",
                "role": "network_partition"
            },
            related_to={"peer", "orderer", "chaincode", "ledger", "msp"}
        ),
        "chaincode": OntologyEntity(
            name="Chaincode",
            description="Smart contract que define regras de negócio",
            aliases=["smart contract", "contrato inteligente", "business_logic"],
            properties={
                "defines_rules": "true",
                "state_management": "true",
                "role": "business_logic"
            },
            related_to={"peer", "channel", "ledger", "transaction", "msp"}
        ),
        "ledger": OntologyEntity(
            name="Ledger",
            description="Banco de dados distribuído que armazena todos os registros",
            aliases=["livro-razão", "distributed_database", "state_database"],
            properties={
                "is_distributed": "true",
                "immutable": "true",
                "role": "data_storage"
            },
            related_to={"peer", "block", "transaction", "channel"}
        ),
        "block": OntologyEntity(
            name="Block",
            description="Unidade de dados que contém transações",
            aliases=["bloco", "block_data", "transaction_batch"],
            properties={
                "contains_transactions": "true",
                "immutable": "true",
                "role": "data_unit"
            },
            related_to={"transaction", "ledger", "orderer", "hash"}
        ),
        "transaction": OntologyEntity(
            name="Transaction",
            description="Operação que muda o estado do ledger",
            aliases=["transação", "tx", "state_change"],
            properties={
                "changes_state": "true",
                "requires_signature": "true",
                "role": "operation"
            },
            related_to={"chaincode", "endorsement", "block", "msp"}
        ),
        "endorsement": OntologyEntity(
            name="Endorsement",
            description="Assinatura de um peer que valida a transação",
            aliases=["validação", "approval", "peer_signature"],
            properties={
                "validates_transaction": "true",
                "peer_signed": "true",
                "role": "validation"
            },
            related_to={"transaction", "peer", "msp", "policy"}
        ),
        "msp": OntologyEntity(
            name="MSP (Membership Service Provider)",
            description="Sistema que gerencia identidades e certificados",
            aliases=["serviço de membros", "identity_provider", "certificate_authority"],
            properties={
                "manages_identities": "true",
                "issues_certificates": "true",
                "role": "identity_management"
            },
            related_to={"peer", "orderer", "channel", "organization", "certificate"}
        ),
        "organization": OntologyEntity(
            name="Organization",
            description="Entidade que participa da rede",
            aliases=["organização", "org", "participant"],
            properties={
                "owns_peers": "true",
                "owns_orderers": "true",
                "role": "network_participant"
            },
            related_to={"peer", "orderer", "msp", "channel"}
        ),
        
        # Segurança e Criptografia
        "certificate": OntologyEntity(
            name="Certificate",
            description="Documento digital que prova identidade",
            aliases=["certificado", "cert", "public_key"],
            properties={
                "proves_identity": "true",
                "cryptographically_signed": "true",
                "role": "security"
            },
            related_to={"msp", "peer", "orderer", "organization"}
        ),
        "policy": OntologyEntity(
            name="Policy",
            description="Regra que define quem pode fazer o quê",
            aliases=["política", "access_control", "permission"],
            properties={
                "defines_permissions": "true",
                "enforces_rules": "true",
                "role": "governance"
            },
            related_to={"endorsement", "channel", "chaincode", "organization"}
        ),
        "hash": OntologyEntity(
            name="Hash",
            description="Valor criptográfico que identifica blocos/transações",
            aliases=["hash criptográfico", "fingerprint", "digest"],
            properties={
                "identifies_data": "true",
                "immutable": "true",
                "role": "identification"
            },
            related_to={"block", "transaction", "ledger"}
        ),
        
        # Padrões e Conceitos
        "consensus": OntologyEntity(
            name="Consensus",
            description="Mecanismo que garante acordo entre nós",
            aliases=["consenso", "agreement", "ordering_service"],
            properties={
                "ensures_agreement": "true",
                "distributed": "true",
                "role": "agreement_mechanism"
            },
            related_to={"orderer", "block", "peer"}
        ),
        "endorsement_policy": OntologyEntity(
            name="Endorsement Policy",
            description="Regra que define quantos peers devem validar uma transação",
            aliases=["política de validação", "approval_rule"],
            properties={
                "defines_quorum": "true",
                "peer_based": "true",
                "role": "validation_rule"
            },
            related_to={"endorsement", "policy", "peer", "chaincode"}
        ),
        "state": OntologyEntity(
            name="State (World State)",
            description="Estado atual de todos os ativos no ledger",
            aliases=["estado", "world_state", "current_data"],
            properties={
                "current": "true",
                "mutable": "true",
                "role": "data_representation"
            },
            related_to={"ledger", "transaction", "chaincode"}
        ),
        "anchor_peer": OntologyEntity(
            name="Anchor Peer",
            description="Peer designado que conecta organizações em um canal",
            aliases=["peer âncora", "connection_peer"],
            properties={
                "connects_organizations": "true",
                "cross_org_communication": "true",
                "role": "bridge"
            },
            related_to={"peer", "channel", "organization"}
        ),
    }
    
    @classmethod
    def get_entity(cls, name: str) -> OntologyEntity:
        """Retorna uma entidade da ontologia"""
        return cls.ENTITIES.get(name.lower())
    
    @classmethod
    def search_by_alias(cls, alias: str) -> List[OntologyEntity]:
        """Busca entidades por alias/sinônimo"""
        results = []
        search_term = alias.lower()
        for entity in cls.ENTITIES.values():
            if search_term in [a.lower() for a in entity.aliases] or search_term in entity.name.lower():
                results.append(entity)
        return results
    
    @classmethod
    def get_related_entities(cls, entity_name: str, depth: int = 1) -> Dict[str, OntologyEntity]:
        """Retorna entidades relacionadas (recursivo com limite de profundidade)"""
        if depth == 0:
            return {}
        
        entity = cls.get_entity(entity_name)
        if not entity:
            return {}
        
        related = {}
        for rel_name in entity.related_to:
            rel_entity = cls.get_entity(rel_name)
            if rel_entity:
                related[rel_name] = rel_entity
                if depth > 1:
                    related.update(cls.get_related_entities(rel_name, depth - 1))
        
        return related
    
    @classmethod
    def enrich_query(cls, query: str) -> Dict:
        """Enriquece uma query com contexto ontológico"""
        entities_found = []
        related_context = set()
        
        for entity_name in cls.ENTITIES.keys():
            if entity_name in query.lower():
                entity = cls.get_entity(entity_name)
                entities_found.append(entity)
                related_context.update(cls.get_related_entities(entity_name, depth=2).keys())
        
        # Busca por aliases
        for word in query.lower().split():
            search_results = cls.search_by_alias(word)
            for result in search_results:
                if result not in entities_found:
                    entities_found.append(result)
                related_context.update(cls.get_related_entities(result.name, depth=2).keys())
        
        return {
            "entities": entities_found,
            "related_context": list(related_context),
            "enrichment_score": len(entities_found) / max(len(query.split()), 1)
        }


# Contextos temáticos para melhorar respostas
HYPERLEDGER_CONTEXTS = {
    "architecture": [
        "peer", "orderer", "channel", "ledger", "msp", "organization"
    ],
    "smart_contracts": [
        "chaincode", "transaction", "state", "peer", "channel", "policy"
    ],
    "security": [
        "msp", "certificate", "policy", "endorsement", "hash", "organization"
    ],
    "consensus": [
        "orderer", "consensus", "block", "endorsement", "peer", "transaction"
    ],
    "networking": [
        "channel", "peer", "orderer", "anchor_peer", "organization", "communication"
    ]
}
