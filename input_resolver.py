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

        # ---------------------------------
        # PROVIDED INPUT
        # ---------------------------------

        if task_id in task_inputs:

            return {
                "status": "success",
                "task_id": task_id,
                "tool": tool_name,
                "input": task_inputs[task_id],
                "source": "provided"
            }

        # ---------------------------------
        # WEB SEARCH
        # ---------------------------------

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

        # ---------------------------------
        # DATA ANALYSIS
        # ---------------------------------

        if tool_name == "data_analysis":

            return {
                "status": "success",
                "task_id": task_id,
                "tool": tool_name,
                "input": {},
                "source": "supabase"
            }

        # ---------------------------------
        # CALCULATOR
        # ---------------------------------

        if tool_name == "calculator":

            return {
                "status": "failed",
                "task_id": task_id,
                "tool": tool_name,
                "input": {},
                "source": "unresolved",
                "error": (
                    "Calculator expression could not "
                    "be resolved."
                )
            }

        # ---------------------------------
        # HIGH-IMPACT ACTIONS
        # ---------------------------------

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
                    "Required action input could not "
                    "be resolved from the available request."
                )
            }

        # ---------------------------------
        # FALLBACK
        # ---------------------------------

        return {
            "status": "failed",
            "task_id": task_id,
            "tool": tool_name,
            "input": {},
            "source": "unresolved",
            "error": (
                "Input could not be resolved for "
                "the selected tool."
            )
        }
