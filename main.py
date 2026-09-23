from typing import Any, Dict

from fastapi import FastAPI

from registry import get_tool


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
