from typing import Any, Dict, List


class MemoryManager:

    def __init__(self):
        self.memories: List[Dict[str, Any]] = []

    def add_memory(
        self,
        session_id: str,
        key: str,
        value: Any
    ) -> Dict[str, Any]:

        memory = {
            "session_id": session_id,
            "key": key,
            "value": value
        }

        self.memories.append(memory)

        return {
            "status": "success",
            "message": "Memory stored successfully.",
            "memory": memory
        }

    def get_relevant_memory(
        self,
        session_id: str,
        key: str
    ) -> Dict[str, Any]:

        matches = [
            memory
            for memory in self.memories
            if memory["session_id"] == session_id
            and memory["key"] == key
        ]

        return {
            "status": "success",
            "count": len(matches),
            "memories": matches
        }
