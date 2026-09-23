from typing import Any, Dict

from planner import Planner
from executor import Executor
from validator import Validator
from recovery import RecoveryEngine
from approval import ApprovalManager
from trace import AgentTrace


class Orchestrator:

    def __init__(self):
        self.planner = Planner()
        self.executor = Executor()
        self.validator = Validator()
        self.recovery = RecoveryEngine()
        self.approval = ApprovalManager()
        self.trace = AgentTrace()

    def run(
        self,
        user_request: str,
        task_inputs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:

        self.trace.add_event(
        "PLANNING",
        "Agent is creating an execution plan.",
    {
        "user_request": user_request
    }
)

        plan = self.planner.plan(user_request)

        tasks = plan.get("tasks", [])
        self.trace.add_event(
        "PLAN_CREATED",
        "Execution plan created successfully.",
    {
        "task_count": len(tasks),
        "tasks": tasks
    }
        )

        execution_results = []
        validation_results = []
        recovery_results = []

        for task in tasks:

            task_id = task.get("task_id")
            tool_name = task.get("tool")
            self.trace.add_event(
            "TASK_CREATED",
            "Agent created a task for execution.",
                {
                    "task_id": task_id,
                    "tool": tool_name,
                    "description": task.get("description")
                }
                        )
            
            
                    

            approval = self.approval.check_approval(
                tool_name,
                task_inputs.get(task_id, {})
            )   self.trace.add_event(
                "APPROVAL_CHECK",
                "Agent checked whether human approval is required.",
                {
                    "task_id": task_id,
                    "tool": tool_name,
                    "approval_required": approval.get(
                        "approval_required",
                        False
                    ),
                    "status": approval.get("status")
                }
            )

            if approval["status"] == "approval_required":
                return {
                    "status": "approval_required",
                    "plan": plan,
                    "task": task,
                    "approval": approval,
                    "execution_results": execution_results,
                    "validation_results": validation_results,
                    "recovery_results": recovery_results
                }

            result = self.executor.execute_task(
                task,
                task_inputs.get(task_id, {})
            )

            execution_results.append(result)

            validation = self.validator.validate_task_result(
                task,
                result
            )

            validation_results.append(validation)

            if validation["status"] == "failed":

                recovery_state = {
                    "retry_count": 0
                }

                recovery_result = self.recovery.recover(
                    task,
                    result,
                    recovery_state
                )

                recovery_results.append(recovery_result)

                if recovery_result["status"] != "retry":
                    return {
                        "status": "failed",
                        "plan": plan,
                        "execution_results": execution_results,
                        "validation_results": validation_results,
                        "recovery_results": recovery_results
                    }

        return {
            "status": "success",
            "plan": plan,
            "execution_results": execution_results,
            "validation_results": validation_results,
            "recovery_results": recovery_results
        }
