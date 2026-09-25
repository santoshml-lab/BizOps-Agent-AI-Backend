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

        business_concern = None

        investigation = {
            "required": False,
            "reason": None,
            "questions": []
        }

        # -------------------------------------------------
        # PROCESS ANALYSIS RESULTS
        # -------------------------------------------------

        for result in results:

            if result.get("status") != "success":
                continue

            tool = result.get("tool")
            output = result.get("output") or {}

            # -------------------------------------------------
            # DATA ANALYSIS
            # -------------------------------------------------

            if tool == "data_analysis":

                data_analysis_found = True

                product_analysis = output.get(
                    "product_analysis",
                    {}
                )

                strongest_product = output.get(
                    "strongest_product"
                )

                weakest_product = output.get(
                    "weakest_product"
                )

                # -------------------------------------------------
                # PRODUCT PERFORMANCE
                # -------------------------------------------------

                if (
                    product_analysis
                    and strongest_product
                    and weakest_product
                ):

                    strongest_name = strongest_product.get(
                        "product"
                    )

                    weakest_name = weakest_product.get(
                        "product"
                    )

                    strongest_revenue = strongest_product.get(
                        "revenue",
                        0
                    )

                    weakest_revenue = weakest_product.get(
                        "revenue",
                        0
                    )

                    strongest_units = strongest_product.get(
                        "units_sold",
                        0
                    )

                    weakest_units = weakest_product.get(
                        "units_sold",
                        0
                    )

                    revenue_gap = (
                        strongest_revenue
                        - weakest_revenue
                    )

                    units_gap = (
                        strongest_units
                        - weakest_units
                    )

                    insights.append(
                        f"{strongest_name} is the strongest "
                        f"product by recorded revenue at "
                        f"{strongest_revenue}."
                    )

                    insights.append(
                        f"{weakest_name} is the weakest "
                        f"product by recorded revenue at "
                        f"{weakest_revenue}."
                    )

                    insights.append(
                        f"The revenue gap between the strongest "
                        f"and weakest products is "
                        f"{revenue_gap}."
                    )

                    insights.append(
                        f"{strongest_name} sold "
                        f"{strongest_units} units, while "
                        f"{weakest_name} sold "
                        f"{weakest_units} units, "
                        f"a difference of {units_gap} units."
                    )

                    # -------------------------------------------------
                    # BUSINESS CONCERN
                    # -------------------------------------------------

                    business_concern = (
                        f"{weakest_name} is underperforming "
                        f"{strongest_name} in recorded revenue. "
                        f"The key business question is why the "
                        f"performance gap exists."
                    )

                    evidence_gaps.append(
                        "Product-level historical trend"
                    )

                    investigation["required"] = True

                    investigation["reason"] = (
                        f"Current data identifies {weakest_name} "
                        f"as the weakest product, but additional "
                        f"historical and market evidence is needed "
                        f"to determine whether this performance gap "
                        f"is persistent and what is causing it."
                    )

                    investigation["questions"].append(
                        f"Why is {weakest_name} underperforming "
                        f"{strongest_name}?"
                    )

                    investigation["questions"].append(
                        f"Is the performance gap between "
                        f"{strongest_name} and {weakest_name} "
                        f"persistent over time?"
                    )

                    recommendations.append(
                        f"Investigate the historical sales trend "
                        f"of {weakest_name} and compare it with "
                        f"{strongest_name} over the last 6–12 months."
                    )

        # -------------------------------------------------
        # FALLBACK NUMERIC INSIGHTS
        # -------------------------------------------------

        if data_analysis_found and not product_analysis:

            numeric_summary = {}

            for result in results:

                if result.get("tool") != "data_analysis":
                    continue

                output = result.get("output") or {}

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
                        f"{column} total is {total}, "
                        f"with an average of {average}. "
                        f"The minimum is {minimum} and "
                        f"the maximum is {maximum}."
                    )

        # -------------------------------------------------
        # INVESTIGATION RECOMMENDATION
        # -------------------------------------------------

        if investigation["required"]:

            recommendations.append(
                "Collect historical product-level sales data "
                "and compare the trend with relevant market "
                "and competitor evidence."
            )

        # -------------------------------------------------
        # FINAL STATUS
        # -------------------------------------------------

        if not insights:

            issues.append(
                "No actionable business insight could be "
                "derived from the available results."
            )

        status = (
            "success"
            if not issues
            else "partial"
        )

        return {
            "status": status,
            "insights": insights,
            "business_concern": business_concern,
            "evidence_gaps": evidence_gaps,
            "investigation": investigation,
            "recommendations": recommendations,
            "issues": issues
                    }
