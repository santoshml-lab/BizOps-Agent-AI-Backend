from typing import Any, Dict

from planner import Planner
from executor import Executor
from validator import Validator
from recovery import RecoveryEngine
from approval import ApprovalManager
from memory import MemoryManager
from trace import AgentTrace


class Orchestrator:

    def __init__(self, memory_manager=None):
    self.planner = Planner()
    self.executor = Executor()
    self.validator = Validator()
    self.recovery = RecoveryEngine()
    self.approval = ApprovalManager()
    self.memory = memory_manager or MemoryManager()
    self.trace = AgentTrace()
        

    def run(
        self,
        user_request: str,
        task_inputs: Dict[str, Dict[str, Any]],
        session_id: str = "default_session"
    ) -> Dict[str, Any]:

        # ---------------------------------------------------------
        # Memory Retrieval
        # ---------------------------------------------------------

        self.trace.add_event(
            "MEMORY_RETRIEVAL",
            "Agent is retrieving relevant memory.",
            {
                "session_id": session_id
            }
        )

        memory_result = self.memory.get_relevant_memory(
            session_id,
            "business_goal"
        )

        memory_context = memory_result.get(
            "memories",
            []
        )

        self.trace.add_event(
            "MEMORY_CONTEXT",
            "Relevant memory retrieved for planning.",
            {
                "count": len(memory_context),
                "memory": memory_context
            }
        )

        # ---------------------------------------------------------
        # Planning
        # ---------------------------------------------------------

        self.trace.add_event(
            "PLANNING",
            "Agent is creating an execution plan.",
            {
                "user_request": user_request
            }
        )

        plan = self.planner.plan(
            user_request,
            memory_context
        )

        tasks = plan.get("tasks", [])

        self.trace.add_event(
            "PLAN_CREATED",
            "Execution plan created successfully.",
            {
                "task_count": len(tasks),
                "tasks": tasks,
                "memory_used": len(memory_context) > 0
            }
        )

        execution_results = []
        validation_results = []
        recovery_results = []

        # ---------------------------------------------------------
        # Task Execution Loop
        # ---------------------------------------------------------

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

            # -----------------------------------------------------
            # Human Approval
            # -----------------------------------------------------

            approval = self.approval.check_approval(
                tool_name,
                task_inputs.get(task_id, {})
            )

            self.trace.add_event(
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

                self.trace.add_event(
                    "APPROVAL_REQUIRED",
                    "Agent paused execution and requested human approval.",
                    {
                        "task_id": task_id,
                        "tool": tool_name
                    }
                )

                return {
                    "status": "approval_required",
                    "plan": plan,
                    "task": task,
                    "approval": approval,
                    "memory_context": memory_context,
                    "execution_results": execution_results,
                    "validation_results": validation_results,
                    "recovery_results": recovery_results
                }

            # -----------------------------------------------------
            # Recovery State
            # -----------------------------------------------------

            recovery_state = {
                "retry_count": 0
            }

            task_completed = False

            # -----------------------------------------------------
            # Execution + Validation + Recovery
            # -----------------------------------------------------

            while True:

                result = self.executor.execute_task(
                    task,
                    task_inputs.get(task_id, {})
                )

                self.trace.add_event(
                    "TOOL_EXECUTION",
                    "Agent executed the selected tool.",
                    {
                        "task_id": task_id,
                        "tool": tool_name,
                        "status": result.get("status"),
                        "retry_count": recovery_state.get(
                            "retry_count",
                            0
                        )
                    }
                )

                execution_results.append(result)

                validation = self.validator.validate_task_result(
                    task,
                    result
                )

                self.trace.add_event(
                    "VALIDATION",
                    "Agent validated the tool result.",
                    {
                        "task_id": task_id,
                        "tool": tool_name,
                        "status": validation.get("status"),
                        "issues": validation.get(
                            "issues",
                            []
                        ),
                        "retry_count": recovery_state.get(
                            "retry_count",
                            0
                        )
                    }
                )

                validation_results.append(validation)

                # -------------------------------------------------
                # Successful Task
                # -------------------------------------------------

                if validation["status"] == "passed":

                    task_completed = True
                    break

                # -------------------------------------------------
                # Recovery
                # -------------------------------------------------

                recovery_result = self.recovery.recover(
                    task,
                    result,
                    recovery_state
                )

                self.trace.add_event(
                    "RECOVERY",
                    "Agent evaluated recovery or retry strategy.",
                    {
                        "task_id": task_id,
                        "tool": tool_name,
                        "status": recovery_result.get("status"),
                        "strategy": recovery_result.get(
                            "strategy"
                        ),
                        "retry_count": recovery_result.get(
                            "retry_count",
                            0
                        )
                    }
                )

                recovery_results.append(recovery_result)

                # -------------------------------------------------
                # Recovery Failed
                # -------------------------------------------------

                if recovery_result["status"] != "retry":

                    self.trace.add_event(
                        "FINAL_RESPONSE",
                        "Agent completed with a failed status.",
                        {
                            "status": "failed",
                            "task_count": len(tasks)
                        }
                    )

                    return {
                        "status": "failed",
                        "plan": plan,
                        "memory_context": memory_context,
                        "execution_results": execution_results,
                        "validation_results": validation_results,
                        "recovery_results": recovery_results
                    }

                # -------------------------------------------------
                # Update Retry Count
                # -------------------------------------------------

                recovery_state["retry_count"] = recovery_result.get(
                    "retry_count",
                    recovery_state["retry_count"] + 1
                )

                self.trace.add_event(
                    "RETRY_EXECUTION",
                    "Agent is retrying the failed task.",
                    {
                        "task_id": task_id,
                        "tool": tool_name,
                        "retry_count": recovery_state[
                            "retry_count"
                        ]
                    }
                )

            if task_completed:
                continue

        # ---------------------------------------------------------
        # Final Successful Response
        # ---------------------------------------------------------

        self.trace.add_event(
            "FINAL_RESPONSE",
            "Agent completed the request successfully.",
            {
                "status": "success",
                "task_count": len(tasks)
            }
        )

        return {
            "status": "success",
            "plan": plan,
            "memory_context": memory_context,
            "execution_results": execution_results,
            "validation_results": validation_results,
            "recovery_results": recovery_results
        }
