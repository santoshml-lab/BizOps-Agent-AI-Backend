from typing import Any, Dict, List
from datetime import datetime


class AgentTrace:

    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def add_event(
        self,
        event_type: str,
        message: str,
        data: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:

        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "message": message,
            "data": data or {}
        }

        self.events.append(event)

        return event

    def get_trace(self) -> List[Dict[str, Any]]:
        return self.events

    def clear(self) -> None:
        self.events.clear()
