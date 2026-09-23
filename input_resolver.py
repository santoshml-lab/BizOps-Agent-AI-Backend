from typing import Any, Dict


class InputResolver:

    def resolve(
        self,
        task: Dict[str, Any],
        user_request: str,
        task_inputs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:

        task_id = task.get("task_id")
        tool_name = task.get("tool")

        if not task_id:
            raise ValueError("Task ID is required.")

        if not tool_name:
            raise ValueError("Tool name is required.")

        # 1. Use explicitly provided task input first.
        if task_id in task_inputs:
            return {
                "status": "success",
                "task_id": task_id,
                "tool": tool_name,
                "input": task_inputs[task_id],
                "source": "provided"
            }

        # 2. Resolve web search input.
        if tool_name == "web_search":

            search_query = user_request

            if any(
                phrase in user_request.lower()
                for phrase in [
                    "market trends",
                    "market trend",
                    "sales trends",
                    "sales trend",
                    "competitor",
                    "competition",
                    "industry trends",
        ]
    ):

               search_query = (
                   "current business market trends "
                   "and sales trends 2026"
        )

        return {
            "status": "success",
            "task_id": task_id,
            "tool": tool_name,
            "input": {
                "query": search_query
        },
        "source": "task_specific"
    }

            
            

        # 3. Calculator requires an explicit expression.
        if tool_name == "calculator":

            return {
                "status": "failed",
                "task_id": task_id,
                "tool": tool_name,
                "input": {},
                "source": "unresolved",
                "error": "Calculator expression could not be resolved."
            }

        # 4. Data analysis requires explicit data.
        if tool_name == "data_analysis":

            return {
                "status": "failed",
                "task_id": task_id,
                "tool": tool_name,
                "input": {},
                "source": "unresolved",
                "error": "Business data could not be resolved."
            }

        # 5. Tools that require human approval
        # are not automatically given fabricated input.
        if tool_name in {
            "send_email",
            "delete_data",
            "modify_data",
            "make_transaction"
        }:

            return {
                "status": "failed",
                "task_id": task_id,
                "tool": tool_name,
                "input": {},
                "source": "unresolved",
                "error": (
                    "Required action input could not be resolved "
                    "from the available request."
                )
            }

        # 6. Unknown tool.
        return {
            "status": "failed",
            "task_id": task_id,
            "tool": tool_name,
            "input": {},
            "source": "unresolved",
            "error": "Input could not be resolved for the selected tool."
        }
