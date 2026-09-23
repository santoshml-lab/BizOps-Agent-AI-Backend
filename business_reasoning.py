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
                "business_concern": None,
                "evidence_gaps": [],
                "recommendations": [],
                "issues": [
                    "Aggregated result is empty."
                ]
            }

        if aggregated_result.get("status") != "success":
            return {
                "status": "failed",
                "insights": [],
                "business_concern": None,
                "evidence_gaps": [],
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
        evidence_gaps: List[str] = []
        issues: List[str] = []

        data_analysis_found = False
        web_search_found = False

        business_concern = None

        for result in results:

            if result.get("status") != "success":
                continue

            tool = result.get("tool")
            output = result.get("output") or {}

            # ---------------------------------
            # DATA ANALYSIS REASONING
            # ---------------------------------

            if tool == "data_analysis":

                data_analysis_found = True

                numeric_summary = output.get(
                    "numeric_summary",
                    {}
                )

                sales_summary = numeric_summary.get(
                    "sales"
                )

                if sales_summary:

                    total = sales_summary.get("sum")
                    average = sales_summary.get("average")
                    minimum = sales_summary.get("minimum")
                    maximum = sales_summary.get("maximum")
                    count = sales_summary.get("count")

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
                            f"Recorded sales total {total}, "
                            f"with an average of {average}, "
                            f"ranging from {minimum} to {maximum}."
                        )

                    # Identify product-level spread.
                    if (
                        minimum is not None
                        and maximum is not None
                        and maximum > minimum
                    ):

                        spread = maximum - minimum

                        insights.append(
                            f"The gap between the highest "
                            f"and lowest recorded sales is "
                            f"{spread} units."
                        )

                    # Detect limited observations.
                    if count is not None and count < 5:

                        insights.append(
                            "The available sales dataset contains "
                            "few observations, so persistent "
                            "performance trends cannot yet be established."
                        )

                        evidence_gaps.append(
                            "Historical sales by product"
                        )

                        business_concern = (
                            "The available sales data is insufficient "
                            "to determine whether the observed product "
                            "performance gap is persistent or temporary."
                        )

            # ---------------------------------
            # WEB SEARCH REASONING
            # ---------------------------------

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

        # ---------------------------------
        # NEXT INVESTIGATION
        # ---------------------------------

        if data_analysis_found:

            recommendations.append(
                "Investigate historical product-level sales "
                "over the last 6–12 months to determine whether "
                "the observed performance gap is persistent, "
                "improving, or declining."
            )

        # ---------------------------------
        # MARKET CONTEXT
        # ---------------------------------

        if data_analysis_found and web_search_found:

            evidence_gaps.append(
                "Product-specific market and competitive data"
            )

            recommendations.append(
                "Compare the internal product performance "
                "with product-specific market and competitor "
                "data before making strategic decisions."
            )

        # ---------------------------------
        # FALLBACK
        # ---------------------------------

        if not insights:

            issues.append(
                "No actionable business insight could be "
                "derived from the available results."
            )

        status = "success" if not issues else "partial"

        return {
            "status": status,
            "insights": insights,
            "business_concern": business_concern,
            "evidence_gaps": evidence_gaps,
            "recommendations": recommendations,
            "issues": issues
        }
