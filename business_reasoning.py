from typing import Any, Dict, List


class BusinessReasoning:

    def reason(
        self,
        aggregated_result: Dict[str, Any]
    ) -> Dict[str, Any]:

        if not aggregated_result:
            return {
                "status": "failed",
                "insights": [],
                "recommendations": [],
                "issues": ["Aggregated result is empty."]
            }

        if aggregated_result.get("status") != "success":
            return {
                "status": "failed",
                "insights": [],
                "recommendations": [],
                "issues": [
                    "Aggregated result is not valid."
                ]
            }

        results = aggregated_result.get(
            "results",
            []
        )

        insights: List[str] = []
        recommendations: List[str] = []
        issues: List[str] = []

        data_analysis_found = False
        web_search_found = False

        for result in results:

            if result.get("status") != "success":
                continue

            tool = result.get("tool")
            output = result.get("output") or {}

            if tool == "data_analysis":

                data_analysis_found = True

                numeric_summary = output.get(
                    "numeric_summary",
                    {}
                )

                for column, summary in numeric_summary.items():

                    total = summary.get("sum")
                    average = summary.get("average")
                    minimum = summary.get("minimum")
                    maximum = summary.get("maximum")

                    if all(
                        value is not None
                        for value in [
                            total,
                            average,
                            minimum,
                            maximum
                        ]
                    ):
                        insights.append(
                            f"{column.capitalize()} has a total "
                            f"of {total}, an average of "
                            f"{average}, a minimum of "
                            f"{minimum}, and a maximum of "
                            f"{maximum}."
                        )

                row_count = output.get("row_count")

                if row_count is not None and row_count < 5:
                    insights.append(
                        "The available dataset is small, "
                        "so strong business trend conclusions "
                        "should be treated cautiously."
                    )

            elif tool == "web_search":

                web_search_found = True

                search_results = output.get(
                    "results",
                    []
                )

                if search_results:
                    insights.append(
                        f"External research returned "
                        f"{len(search_results)} results "
                        "relevant to the business request."
                    )

        if data_analysis_found and web_search_found:

            recommendations.append(
                "Combine the internal sales metrics with "
                "time-based and market-level data before "
                "making strategic decisions."
            )

        if not insights:
            issues.append(
                "No actionable business insight could be "
                "derived from the available results."
            )

        status = "success" if not issues else "partial"

        return {
            "status": status,
            "insights": insights,
            "recommendations": recommendations,
            "issues": issues
        }
