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

            calculator_input = (
                self._resolve_calculator_input(
                    previous_results
                )
            )

            if calculator_input:

                return {
                    "status": "success",
                    "task_id": task_id,
                    "tool": tool_name,
                    "input": calculator_input,
                    "source": "previous_results"
                }

            # ---------------------------------
            # CALCULATOR INPUT NOT AVAILABLE
            # ---------------------------------

            return {
                "status": "failed",
                "task_id": task_id,
                "tool": tool_name,
                "input": {},
                "source": "unresolved",
                "error": (
                    "Calculator expression could not "
                    "be resolved from previous task results."
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

    # =========================================================
    # CALCULATOR INPUT RESOLUTION
    # =========================================================

    def _resolve_calculator_input(
        self,
        previous_results: list
    ) -> Dict[str, Any]:

        if not isinstance(
            previous_results,
            list
        ):
            return {}

        # -----------------------------------------------------
        # SEARCH PREVIOUS TASK RESULTS
        # -----------------------------------------------------

        for result in previous_results:

            if not isinstance(
                result,
                dict
            ):
                continue

            output = result.get(
                "output",
                {}
            )

            if not isinstance(
                output,
                dict
            ):
                continue

            # -------------------------------------------------
            # MONTHLY CHANGE ALREADY AVAILABLE
            # -------------------------------------------------

            monthly_change = output.get(
                "monthly_change",
                {}
            )

            if (
                isinstance(
                    monthly_change,
                    dict
                )
                and monthly_change
            ):

                latest_month = self._get_latest_month(
                    monthly_change
                )

                if not latest_month:
                    continue

                latest_data = monthly_change.get(
                    latest_month,
                    {}
                )

                if not isinstance(
                    latest_data,
                    dict
                ):
                    continue

                previous_revenue = (
                    self._safe_number(
                        latest_data.get(
                            "previous_revenue"
                        )
                    )
                )

                current_revenue = (
                    self._safe_number(
                        latest_data.get(
                            "current_revenue"
                        )
                    )
                )

                if (
                    previous_revenue is not None
                    and current_revenue is not None
                    and previous_revenue != 0
                ):

                    expression = (
                        f"({current_revenue} - "
                        f"{previous_revenue}) / "
                        f"{previous_revenue} * 100"
                    )

                    return {
                        "expression": expression
                    }

            # -------------------------------------------------
            # FALLBACK: MONTHLY ANALYSIS
            # -------------------------------------------------

            monthly_analysis = output.get(
                "monthly_analysis",
                {}
            )

            if (
                isinstance(
                    monthly_analysis,
                    dict
                )
                and len(monthly_analysis) >= 2
            ):

                months = sorted(
                    monthly_analysis.keys()
                )

                previous_month = months[-2]
                current_month = months[-1]

                previous_data = (
                    monthly_analysis.get(
                        previous_month,
                        {}
                    )
                )

                current_data = (
                    monthly_analysis.get(
                        current_month,
                        {}
                    )
                )

                if not isinstance(
                    previous_data,
                    dict
                ):
                    continue

                if not isinstance(
                    current_data,
                    dict
                ):
                    continue

                previous_revenue = (
                    self._safe_number(
                        previous_data.get(
                            "revenue"
                        )
                    )
                )

                current_revenue = (
                    self._safe_number(
                        current_data.get(
                            "revenue"
                        )
                    )
                )

                if (
                    previous_revenue is not None
                    and current_revenue is not None
                    and previous_revenue != 0
                ):

                    expression = (
                        f"({current_revenue} - "
                        f"{previous_revenue}) / "
                        f"{previous_revenue} * 100"
                    )

                    return {
                        "expression": expression
                    }

        return {}

    # =========================================================
    # GET LATEST MONTH
    # =========================================================

    def _get_latest_month(
        self,
        monthly_change: Dict[str, Any]
    ) -> str:

        if not isinstance(
            monthly_change,
            dict
        ):
            return ""

        valid_months = []

        for month in monthly_change.keys():

            if month is None:
                continue

            month_text = str(
                month
            ).strip()

            if month_text:
                valid_months.append(
                    month_text
                )

        if not valid_months:
            return ""

        return sorted(
            valid_months
        )[-1]

    # =========================================================
    # SAFE NUMBER
    # =========================================================

    def _safe_number(
        self,
        value: Any
    ) -> Any:

        try:

            if value is None:
                return None

            return float(value)

        except (
            TypeError,
            ValueError
        ):

            return None0
