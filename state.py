from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class AgentState:
    session_id: str
    user_request: str

    tasks: List[Dict[str, Any]] = field(default_factory=list)

    tool_results: List[Dict[str, Any]] = field(default_factory=list)

    validation: Dict[str, Any] = field(
        default_factory=lambda: {
            "status": "pending",
            "issues": []
        }
    )

    recovery: Dict[str, Any] = field(
        default_factory=lambda: {
            "attempted": False,
            "retry_count": 0,
            "strategy": None,
            "last_error": None,
            "recovered": False
        }
    )

    memory: List[Dict[str, Any]] = field(default_factory=list)

    final_response: Optional[str] = None
