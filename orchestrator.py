from typing import Any, Dict

from planner import Planner
from executor import Executor
from validator import Validator
from recovery import RecoveryEngine
from approval import ApprovalManager
from memory import MemoryManager
from trace import AgentTrace
from response_builder import ResponseBuilder
from input_resolver import InputResolver
from result_aggregator import ResultAggregator
from business_reasoning import BusinessReasoning
from investigation import InvestigationPlanner


class Orchestrator:

    def __init__(self, memory_manager=None):
        self.planner = Planner()
        self.executor = Executor()
        self.validator = Validator()
        self.recovery = RecoveryEngine()
        self.approval = ApprovalManager()
        self.memory = memory_manager or MemoryManager()
        self.trace = AgentTrace()
        self.response_builder = ResponseBuilder()
        self.result_aggregator = ResultAggregator()
        self.input_resolver = InputResolver()
        self.business_reasoning = BusinessReasoning()
        self.investigation_planner = InvestigationPlanner()

    def run(
        self,
        user_request: str,
        task_inputs: Dict[str, Dict[str, Any]],
        session_id: str = "default_session"
    ) -> Dict[str, Any]:

        # -------------------------------------------------
        # MEMORY
        # -------------------------------------------------

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

        # -------------------------------------------------
        # PLANNING
        # -------------------------------------------------

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

        tasks = plan.get(
            "tasks",
            []
        )

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

        # -------------------------------------------------
        # TASK EXECUTION
        # -------------------------------------------------

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

            # -------------------------------------------------
            # INPUT RESOLUTION
            # -------------------------------------------------

            resolved_input = self.input_resolver.resolve(
                task=task,
                user_request=user_request,
                task_inputs=task_inputs
            )

            self.trace.add_event(
                "INPUT_RESOLUTION",
                "Agent resolved the input required for the task.",
                {
                    "task_id": task_id,
                    "tool": tool_name,
                    "status": resolved_input.get(
                        "status"
                    ),
                    "source": resolved_input.get(
                        "source"
                    )
                }
            )

            if resolved_input.get("status") != "success":

                self.trace.add_event(
                    "FINAL_RESPONSE",
                    "Agent could not resolve the required task input.",
                    {
                        "status": "failed",
                        "task_id": task_id,
                        "tool": tool_name
                    }
                )

                return {
                    "status": "failed",
                    "plan": plan,
                    "memory_context": memory_context,
                    "execution_results": execution_results,
                    "validation_results": validation_results,
                    "recovery_results": recovery_results,
                    "input_resolution": resolved_input,
                    "trace": self.trace.get_trace()
                }

            resolved_task_input = resolved_input.get(
                "input",
                {}
            )

            # -------------------------------------------------
            # APPROVAL
            # -------------------------------------------------

            approval = self.approval.check_approval(
                tool_name,
                resolved_task_input
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
                    "status": approval.get(
                        "status"
                    )
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
                    "recovery_results": recovery_results,
                    "input_resolution": resolved_input,
                    "trace": self.trace.get_trace()
                }

            # -------------------------------------------------
            # RECOVERY STATE
            # -------------------------------------------------

            recovery_state = {
                "retry_count": 0
            }

            task_completed = False

            # -------------------------------------------------
            # EXECUTION + VALIDATION + RECOVERY
            # -------------------------------------------------

            while True:

                result = self.executor.execute_task(
                    task,
                    resolved_task_input
                )

                self.trace.add_event(
                    "TOOL_EXECUTION",
                    "Agent executed the selected tool.",
                    {
                        "task_id": task_id,
                        "tool": tool_name,
                        "status": result.get(
                            "status"
                        ),
                        "retry_count": recovery_state.get(
                            "retry_count",
                            0
                        )
                    }
                )

                execution_results.append(
                    result
                )

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
                        "status": validation.get(
                            "status"
                        ),
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

                validation_results.append(
                    validation
                )

                if validation["status"] == "passed":

                    task_completed = True
                    break

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
                        "status": recovery_result.get(
                            "status"
                        ),
                        "strategy": recovery_result.get(
                            "strategy"
                        ),
                        "retry_count": recovery_result.get(
                            "retry_count",
                            0
                        )
                    }
                )

                recovery_results.append(
                    recovery_result
                )

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
                        "recovery_results": recovery_results,
                        "trace": self.trace.get_trace()
                    }

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

        # -------------------------------------------------
        # BUSINESS INSIGHT
        # -------------------------------------------------

        aggregated_result = self.result_aggregator.aggregate(
            execution_results
        )

        self.trace.add_event(
            "RESULT_AGGREGATION",
            "Agent aggregated validated tool results.",
            {
                "status": aggregated_result.get(
                    "status"
                ),
                "count": aggregated_result.get(
                    "count",
                    0
                )
            }
        )

        # -------------------------------------------------
        # BUSINESS REASONING
        # -------------------------------------------------

        reasoning_result = self.business_reasoning.reason(
            aggregated_result
        )

        self.trace.add_event(
            "BUSINESS_REASONING",
            "Agent generated business reasoning from aggregated results.",
            {
                "status": reasoning_result.get(
                    "status"
                ),
                "insight_count": len(
                    reasoning_result.get(
                        "insights",
                        []
                    )
                ),
                "recommendation_count": len(
                    reasoning_result.get(
                        "recommendations",
                        []
                    )
                )
            }
        )

        # -------------------------------------------------
        # INVESTIGATION CHECK
        # -------------------------------------------------

        investigation = reasoning_result.get(
            "investigation",
            {}
        )

        if investigation.get("required"):

            self.trace.add_event(
                "INVESTIGATION_REQUIRED",
                "Agent determined that additional investigation is required.",
                {
                    "reason": investigation.get(
                        "reason"
                    ),
                    "questions": investigation.get(
                        "questions",
                        []
                    )
                }
            )

            investigation_plan = self.investigation_planner.create_tasks(
                investigation
            )

            self.trace.add_event(
                "INVESTIGATION_PLANNED",
                "Agent converted investigation questions into investigation tasks.",
                {
                    "status": investigation_plan.get(
                        "status"
                    ),
                    "task_count": investigation_plan.get(
                        "task_count",
                        0
                    ),
                    "tasks": investigation_plan.get(
                        "tasks",
                        []
                    )
                }
            )
            # -------------------------------------------------
            # INVESTIGATION EXECUTION
            # -------------------------------------------------

            investigation_results = []

            for investigation_task in investigation_plan.get(
                "tasks",
                []
            ):

                if investigation_task.get("type") == "data_request":

                    investigation_results.append({
                        "task_id": investigation_task.get(
                            "task_id"
                        ),
                        "type": "data_request",
                        "status": "waiting_for_data",
                        "message": (
                            "Additional internal business data "
                            "is required to answer this investigation."
                        )
                    })

                elif investigation_task.get(
                    "type"
                ) == "external_research":

                    investigation_query = (
                        "Product sales performance for A, B, C "
                        "and relevant market or competitor trends "
                        "in 2026"
                    )

                    investigation_execution = (
                        self.executor.execute_task(
                            {
                                "task_id": investigation_task.get(
                                    "task_id"
                                ),
                                "description": investigation_task.get(
                                    "description"
                                ),
                                "tool": "web_search",
                                "status": "pending"
                            },
                            {
                                "query": investigation_query
                            }
                        )
                    )

                    investigation_results.append({
                        "task_id": investigation_task.get(
                            "task_id"
                        ),
                        "type": "external_research",
                        "status": investigation_execution.get(
                            "status"
                        ),
                        "query": investigation_query,
                        "output": investigation_execution.get(
                            "output"
                        ),
                        "error": investigation_execution.get(
                            "error"
                        )
                    })

            self.trace.add_event(
                "INVESTIGATION_EXECUTION",
                "Agent executed available investigation tasks.",
                {
                    "task_count": len(
                        investigation_results
                    ),
                    "results": investigation_results
                }
            )
        # -------------------------------------------------
        # INVESTIGATION VALIDATION
        # -------------------------------------------------

        investigation_validation_results = []

        for investigation_result in investigation_results:

            status = investigation_result.get(
                "status"
            )

            task_id = investigation_result.get(
                "task_id"
            )

            if status == "success":

                investigation_validation_results.append({
                    "task_id": task_id,
                    "status": "passed",
                    "issues": []
                })

            elif status == "waiting_for_data":

                investigation_validation_results.append({
                    "task_id": task_id,
                    "status": "waiting",
                    "issues": [
                        "Required internal business data is still missing."
                    ]
                })

            else:

                investigation_validation_results.append({
                    "task_id": task_id,
                    "status": "failed",
                    "issues": [
                        investigation_result.get(
                            "error",
                            "Investigation execution failed."
                        )
                    ]
                })

        self.trace.add_event(
            "INVESTIGATION_VALIDATION",
            "Agent validated investigation results.",
            {
                "results": investigation_validation_results
            }
        )

        
            
            
            

            

            
                
                
            

                
                    

        

        # -------------------------------------------------
        # RESPONSE BUILDING
        # -------------------------------------------------

        response = self.response_builder.build(
            user_request=user_request,
            plan=plan,
            execution_results=execution_results,
            memory_context=memory_context,
            reasoning_result=reasoning_result
        )

        self.trace.add_event(
            "BUSINESS_INSIGHT",
            "Agent generated business insights from validated results.",
            {
                "insight_count": len(
                    response.get(
                        "insights",
                        []
                    )
                ),
                "recommendation_count": len(
                    response.get(
                        "recommendations",
                        []
                    )
                )
            }
        )

        # -------------------------------------------------
        # FINAL RESPONSE
        # -------------------------------------------------

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
            "recovery_results": recovery_results,
            "insights": response.get(
                "insights",
                []
            ),
            "recommendations": response.get(
                "recommendations",
                []
            ),
            "final_response": response.get(
                "final_response"
            ),
            "trace": self.trace.get_trace()
        }
