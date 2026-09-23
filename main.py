from typing import Any, Dict

from fastapi import FastAPI

from registry import get_tool
from planner import Planner


app = FastAPI(
    title="BizOps Agent AI",
    description="Agentic AI system for business operations",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "status": "success",
        "message": "BizOps Agent AI API is running"
    }


@app.post("/tools/calculator")
def calculate(input_data: Dict[str, Any]):
    calculator = get_tool("calculator")
    return calculator.execute(input_data)

@app.post("/tools/data-analysis")
def data_analysis(input_data: Dict[str, Any]):
    data_tool = get_tool("data_analysis")
    return data_tool.execute(input_data)

@app.post("/tools/web-search")
def web_search(input_data: Dict[str, Any]):
    search_tool = get_tool("web_search")
    return search_tool.execute(input_data)

@app.post("/agent/plan")
def create_plan(input_data: Dict[str, Any]):
    user_request = input_data.get("request")

    planner = Planner()

    return planner.plan(user_request)
