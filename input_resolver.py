from typing import Any, Dict


class InputResolver:

    def resolve(
        self,
        task: Dict[str, Any],
        user_request: str,
        task_inputs: Dict[str, Dict[str, Any]],
        previous_results: list
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

            request_lower = user_request.lower()

            if any(
                phrase in request_lower
                for phrase in [
                    "sales dropped",
                    "sales drop",
                    "sales declined",
                    "sales decline",
                    "revenue dropped",
                    "revenue decline",
                    "revenue decreased",
                    "sales slowdown",
                ]
            ):
                search_query = (
                    "external factors that can affect business sales "
                    "and revenue competitor pricing market demand "
                    "industry trends customer behavior 2026"
                )

            elif any(
                phrase in request_lower
                for phrase in [
                    "competitor",
                    "competition",
                    "market trends",
                    "market trend",
                    "industry trends",
                    "industry trend",
                ]
            ):
                search_query = (
                    "business market trends competitor pricing "
                    "customer demand industry trends 2026"
                )

            else:
                search_query = (
                    "business market factors competitor pricing "
                    "customer demand industry trends 2026"
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
