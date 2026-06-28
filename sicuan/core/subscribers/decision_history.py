"""
Decision History Subscriber - Menyimpan keputusan dari artifact events
"""

from sicuan.core.artifact_event import ArtifactEvent
from sicuan.core.decision_history import DecisionHistory


def decision_history_subscriber(event: ArtifactEvent):
    """Subscriber untuk decision history"""
    print(f"[DECISION] Processing event: {event.artifact_id}")
    if not event.decision:
        print("[DECISION] No decision in event")
        return
    
    history = DecisionHistory()
    history.add(
        action=event.decision.selected_action,
        reason=event.decision.reason_code,
        candidates=[c.action for c in event.decision.candidate_actions],
        confidence=event.decision.confidence,
        evidence=event.decision.evidence,
        constraints=event.decision.constraints,
        artifact_id=event.artifact_id,
        project=event.project,
        session_id=event.session_id
    )
    print(f"[DECISION] Stored: {event.decision.selected_action} (confidence: {event.decision.confidence})")
