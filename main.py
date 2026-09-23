from typing import Any, Dict

from fastapi import FastAPI

from registry import get_tool
from planner import Planner
from executor import Executor
from validator import Validator
from recovery import RecoveryEngine
from memory import MemoryManager
from approval import ApprovalManager
from orchestrator import Orchestrator
from input_resolver import InputResolver
from result_aggregator import ResultAggregator
from business_reasoning import BusinessReasoning


app = FastAPI(
    title="BizOps Agent AI",
    description="Agentic AI system for business operations",
    version="1.0.0",
)

memory_manager = MemoryManager()
input_resolver = InputResolver()


@app.get("/")
def root():
    return {
        "status": "success",
        "message": "BizOps Agent AI API is running",
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


@app.post("/agent/execute")
def execute_task(input_data: Dict[str, Any]):
    task = input_data.get("task")
    tool_input = input_data.get("input", {})

    executor = Executor()

    return executor.execute_task(
        task,
        tool_input,
    )


@app.post("/agent/validate")
def validate_task(input_data: Dict[str, Any]):
    task = input_data.get("task")
    result = input_data.get("result")

    validator = Validator()

    return validator.validate_task_result(
        task,
        result,
    )


@app.post("/agent/recover")
def recover_task(input_data: Dict[str, Any]):
    task = input_data.get("task")
    result = input_data.get("result")

    recovery_state = input_data.get(
        "recovery_state",
        {
            "retry_count": 0,
        },
    )

    recovery_engine = RecoveryEngine()

    return recovery_engine.recover(
        task,
        result,
        recovery_state,
    )


@app.post("/memory/add")
def add_memory(input_data: Dict[str, Any]):
    session_id = input_data.get("session_id")
    key = input_data.get("key")
    value = input_data.get("value")

    return memory_manager.add_memory(
        session_id,
        key,
        value,
    )


@app.post("/memory/get")
def get_memory(input_data: Dict[str, Any]):
    session_id = input_data.get("session_id")
    key = input_data.get("key")

    return memory_manager.get_relevant_memory(
        session_id,
        key,
    )


@app.post("/agent/approval")
def check_approval(input_data: Dict[str, Any]):
    action = input_data.get("action")
    action_input = input_data.get("input", {})

    approval_manager = ApprovalManager()

    return approval_manager.check_approval(
        action,
        action_input,
    )

@app.post("/agent/resolve-input")
def resolve_input(input_data: Dict[str, Any]):
    task = input_data.get("task")
    user_request = input_data.get("request", "")
    task_inputs = input_data.get("task_inputs", {})

    if not task:
        return {
            "status": "failed",
            "error": "Task is required.",
        }

    return input_resolver.resolve(
        task=task,
        user_request=user_request,
        task_inputs=task_inputs,
    )


@app.post("/agent/run")
def run_agent(input_data: Dict[str, Any]):
    user_request = input_data.get("request")
    task_inputs = input_data.get("task_inputs", {})

    session_id = input_data.get(
        "session_id",
        "default_session",
    )

    orchestrator = Orchestrator(
        memory_manager,
    )

    result = orchestrator.run(
        user_request,
        task_inputs,
        session_id,
    )

    result["trace"] = orchestrator.trace.get_trace()

    return result

@app.post("/agent/aggregate-test")
def aggregate_test(input_data: Dict[str, Any]):

    execution_results = input_data.get(
        "execution_results",
        []
    )

    aggregator = ResultAggregator()

    return aggregator.aggregate(
        execution_results
    )

@app.post("/agent/reason-test")
def reason_test(input_data: Dict[str, Any]):

    aggregated_result = input_data.get(
        "aggregated_result",
        {}
    )

    reasoning = BusinessReasoning()

    return reasoning.reason(
        aggregated_result
    )




        
