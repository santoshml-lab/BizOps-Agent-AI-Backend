from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with the provided input."""
        pass
