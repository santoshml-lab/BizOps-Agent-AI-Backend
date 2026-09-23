from typing import Dict

from base import BaseTool


TOOL_REGISTRY: Dict[str, BaseTool] = {}


def register_tool(tool: BaseTool) -> None:
    TOOL_REGISTRY[tool.name] = tool


def get_tool(tool_name: str) -> BaseTool:
    tool = TOOL_REGISTRY.get(tool_name)

    if tool is None:
        raise ValueError(f"Tool not found: {tool_name}")

    return tool
