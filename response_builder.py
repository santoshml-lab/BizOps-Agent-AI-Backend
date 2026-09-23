from typing import Any, Dict, List


class ResponseBuilder:

    def build(
        self,
        user_request: str,
        plan: Dict[str, Any],
        execution_results: List[Dict[str, Any]],
        memory_context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        insights = []

        for result in execution_results:

            if result.get("status") != "success":
                continue

            tool = result.get("tool")
            output = result.get("output", {})

            if tool == "data_analysis":

                numeric_summary = output.get(
                    "numeric_summary",
                    {}
                )

                for column, summary in numeric_summary.items():

                    total = summary.get("sum")
                    average = summary.get("average")
                    minimum = summary.get("minimum")
                    maximum = summary.get("maximum")

                    insights.append(
                        f"{column.capitalize()} total is {total}, "
                        f"with an average of {average}. "
                        f"The minimum is {minimum} and "
                        f"the maximum is {maximum}."
                    )

            elif tool == "calculator":

                if "result" in output:

                    insights.append(
                        f"The calculated result is "
                        f"{output['result']}."
                    )

            elif tool == "web_search":

                results = output.get(
                    "results",
                    []
                )

                if results:

                    insights.append(
                        f"The web search returned "
                        f"{len(results)} relevant results."
                    )

        business_goals = [
            memory.get("value")
            for memory in memory_context
            if memory.get("key") == "business_goal"
        ]

        recommendations = []

        if business_goals and insights:

            recommendations.append(
                "The analysis should be evaluated against "
                f"the stored business goal: {business_goals[0]}."
            )

        if not insights:

            insights.append(
                "The agent completed the requested tasks "
                "but no business insight was generated."
            )

        final_response = " ".join(insights)

        if recommendations:
            final_response += " " + " ".join(
                recommendations
            )

        return {
            "status": "success",
            "user_request": user_request,
            "insights": insights,
            "recommendations": recommendations,
            "final_response": final_response
        }
