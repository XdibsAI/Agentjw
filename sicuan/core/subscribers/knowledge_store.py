"""
Knowledge Store Subscriber - Menyimpan pengetahuan dari artifact events
"""

from sicuan.core.artifact_event import ArtifactEvent
from sicuan.core.knowledge_index import KnowledgeIndex


def knowledge_store_subscriber(event: ArtifactEvent):
    """Subscriber untuk knowledge store"""
    print(f"[KNOWLEDGE] Processing event: {event.artifact_id}")
    for knowledge in event.knowledge:
        index = KnowledgeIndex()
        fact = f"{knowledge.attribute}: {knowledge.value}"
        index.add(
            entity=knowledge.entity,
            fact=fact,
            source=knowledge.source or event.action,
            confidence=knowledge.confidence,
            metadata={
                "attribute": knowledge.attribute,
                "value": knowledge.value,
                "session_id": event.session_id,
                "project": event.project
            }
        )
        print(f"[KNOWLEDGE] Stored: {knowledge.entity} -> {knowledge.attribute} = {knowledge.value}")
