from typing import Dict

from base import BaseTool
from calculator import CalculatorTool
from data_analysis import DataAnalysisTool


TOOL_REGISTRY: Dict[str, BaseTool] = {}


def register_tool(tool: BaseTool) -> None:
    TOOL_REGISTRY[tool.name] = tool


def get_tool(tool_name: str) -> BaseTool:
    tool = TOOL_REGISTRY.get(tool_name)

    if tool is None:
        raise ValueError(f"Tool not found: {tool_name}")

    return tool


register_tool(CalculatorTool())
register_tool(DataAnalysisTool())
