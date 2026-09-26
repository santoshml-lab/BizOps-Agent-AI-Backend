from typing import Any, Dict, List
from datetime import datetime

class AgentTrace:

 def __init__(self):
    self.events: List[Dict[str, Any]] = []

# ============================================================
# ADD EVENT
# ============================================================

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

# ============================================================
# GET FULL TRACE
# ============================================================

def get_trace(self) -> List[Dict[str, Any]]:
    return self.events

# ============================================================
# GET EVENT COUNT
# ============================================================

def get_event_count(self) -> int:
    return len(self.events)

# ============================================================
# GET EVENT TYPE SUMMARY
# ============================================================

def get_event_summary(self) -> Dict[str, int]:

    summary: Dict[str, int] = {}

    for event in self.events:

        event_type = event.get(
            "event_type",
            "UNKNOWN"
        )

        summary[event_type] = (
            summary.get(event_type, 0) + 1
        )

    return summary

# ============================================================
# GET LATEST EVENT
# ============================================================

def get_latest_event(self) -> Dict[str, Any] | None:

    if not self.events:
        return None

    return self.events[-1]

# ============================================================
# CLEAR TRACE
# ============================================================

def clear(self) -> None:
    self.events.clear()
