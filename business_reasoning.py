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
                "investigation": {
                    "required": False,
                    "reason": None,
                    "questions": []
                },
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
                "investigation": {
                    "required": False,
                    "reason": None,
                    "questions": []
                },
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

        # ---------------------------------
        # INVESTIGATION STATE
        # ---------------------------------

        investigation = {
            "required": False,
            "reason": None,
            "questions": []
        }

        # ---------------------------------
        # PROCESS TOOL RESULTS
        # ---------------------------------

        for result in results:

            if result.get("status") != "success":
                continue

            tool = result.get("tool")
            output = result.get("output") or {}

            # ---------------------------------
            # DATA ANALYSIS
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

                    # Product performance spread
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

                    # Small dataset detection
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
                        # INVESTIGATION DECISION
                        # ---------------------------------

                        investigation["required"] = True

                        investigation["reason"] = (
                            "Historical product-level sales data "
                            "is missing, so the persistence of the "
                            "observed performance gap cannot be established."
                        )

                        investigation["questions"].append(
                            "Is the product performance gap persistent "
                            "or temporary?"
                        )

            # ---------------------------------
            # WEB SEARCH
            # ---------------------------------

            elif tool == "web_search":

                web_search_found = True

                search_results = output.get(
                    "results",
                    []
                )
           elif tool == "investigation":

                investigation_output = output or {}

                investigation_results = investigation_output.get(
                    "results",
                    []
                )

                if investigation_results:

                    insights.append(
                        f"Investigation returned "
                        f"{len(investigation_results)} "
                        "external evidence sources."
                    )

                    insights.append(
                        "External research provides additional "
                        "market context, but it does not establish "
                        "whether the observed product sales gap "
                        "is persistent."
                    )

                    evidence_gaps.append(
                        "Historical product-level sales data"
                    )

                    business_concern = (
                        "The available evidence provides market context, "
                        "but historical product-level sales data is still "
                        "required to determine whether the sales gap is "
                        "persistent or temporary."
                    )

                    recommendations.append(
                        "Collect historical product-level sales data "
                        "over the last 6–12 months and compare the "
                        "trend with the external market evidence."
                    )


                
                            

                

                

                if search_results:

                    insights.append(
                        f"External research returned "
                        f"{len(search_results)} results "
                        "relevant to the business request."
                    )

        # ---------------------------------
        # MARKET / COMPETITOR EVIDENCE GAP
        # ---------------------------------

        if data_analysis_found and web_search_found:

            evidence_gaps.append(
                "Product-specific market and competitive data"
            )

            investigation["questions"].append(
                "How does each product's performance compare "
                "with relevant market or competitor trends?"
            )

        # ---------------------------------
        # NEXT INVESTIGATION RECOMMENDATIONS
        # ---------------------------------

        if investigation["required"]:

            recommendations.append(
                "Investigate historical product-level sales "
                "over the last 6–12 months to determine whether "
                "the observed performance gap is persistent, "
                "improving, or declining."
            )

        if data_analysis_found and web_search_found:

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
            "investigation": investigation,
            "recommendations": recommendations,
            "issues": issues
        }
