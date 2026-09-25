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
        # DETECT AVAILABLE INVESTIGATION EVIDENCE
        # -------------------------------------------------

        historical_trend_available = False
        product_comparison_available = False

        for result in results:

            if result.get("status") != "success":
                continue

            if result.get("tool") != "data_analysis":
                continue

            output = result.get("output") or {}

            investigation_output = output.get(
                "investigation",
                {}
            )

            if not isinstance(
                investigation_output,
                dict
            ):
                continue

            investigation_type = investigation_output.get(
                "type"
            )

            if investigation_type == "historical_trend":
                historical_trend_available = True

            if investigation_type == "product_comparison":
                product_comparison_available = True

        # -------------------------------------------------
        # PROCESS RESULTS
        # -------------------------------------------------

        for result in results:

            if result.get("status") != "success":
                continue

            tool = result.get("tool")
            output = result.get("output") or {}

            # =================================================
            # DATA ANALYSIS
            # =================================================

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

                    # -------------------------------------------------
                    # CORE BUSINESS INSIGHTS
                    # -------------------------------------------------

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

                    business_concern = (
                        f"{weakest_name} is underperforming "
                        f"{strongest_name} in recorded revenue. "
                        f"The key business question is why the "
                        f"performance gap exists."
                    )

                    # -------------------------------------------------
                    # HISTORICAL TREND EVIDENCE
                    # -------------------------------------------------

                    if historical_trend_available:

                        historical_investigation = (
                            output.get(
                                "investigation",
                                {}
                            )
                        )

                        monthly_analysis = (
                            historical_investigation.get(
                                "monthly_analysis",
                                {}
                            )
                        )

                        if monthly_analysis:

                            weakest_months = 0
                            strongest_months = 0
                            comparison_months = 0

                            for month_data in (
                                monthly_analysis.values()
                            ):

                                weakest_data = (
                                    month_data.get(
                                        weakest_name
                                    )
                                )

                                strongest_data = (
                                    month_data.get(
                                        strongest_name
                                    )
                                )

                                if (
                                    weakest_data
                                    and strongest_data
                                ):

                                    comparison_months += 1

                                    weakest_revenue_month = (
                                        weakest_data.get(
                                            "revenue",
                                            0
                                        )
                                    )

                                    strongest_revenue_month = (
                                        strongest_data.get(
                                            "revenue",
                                            0
                                        )
                                    )

                                    if (
                                        weakest_revenue_month
                                        < strongest_revenue_month
                                    ):
                                        weakest_months += 1

                                    if (
                                        strongest_revenue_month
                                        > weakest_revenue_month
                                    ):
                                        strongest_months += 1

                            if comparison_months > 0:

                                if (
                                    weakest_months
                                    == comparison_months
                                ):

                                    insights.append(
                                        f"{weakest_name} generated "
                                        f"lower revenue than "
                                        f"{strongest_name} in all "
                                        f"{comparison_months} observed "
                                        f"months, indicating that the "
                                        f"performance gap is persistent "
                                        f"across the available historical "
                                        f"period."
                                    )

                                else:

                                    insights.append(
                                        f"{weakest_name} generated "
                                        f"lower revenue than "
                                        f"{strongest_name} in "
                                        f"{weakest_months} of "
                                        f"{comparison_months} observed "
                                        f"months."
                                    )

                        # Historical evidence has resolved
                        # the original evidence gap.

                        evidence_gaps = [
                            gap
                            for gap in evidence_gaps
                            if gap != (
                                "Product-level historical trend"
                            )
                        ]

                    else:

                        # Historical evidence is still missing.

                        evidence_gaps.append(
                            "Product-level historical trend"
                        )

                        investigation["required"] = True

                        investigation["reason"] = (
                            f"Current data identifies "
                            f"{weakest_name} as the weakest "
                            f"product, but additional historical "
                            f"and market evidence is needed to "
                            f"determine whether this performance "
                            f"gap is persistent and what is "
                            f"causing it."
                        )

                        investigation["questions"].append(
                            f"Why is {weakest_name} "
                            f"underperforming "
                            f"{strongest_name}?"
                        )

                        investigation["questions"].append(
                            f"Is the performance gap between "
                            f"{strongest_name} and "
                            f"{weakest_name} persistent "
                            f"over time?"
                        )

                        recommendations.append(
                            f"Investigate the historical sales "
                            f"trend of {weakest_name} and "
                            f"compare it with {strongest_name} "
                            f"over the last 6–12 months."
                        )

                    # -------------------------------------------------
                    # PRODUCT COMPARISON EVIDENCE
                    # -------------------------------------------------

                    if product_comparison_available:

                        comparison_data = output.get(
                            "investigation",
                            {}
                        )

                        comparison = comparison_data.get(
                            "comparison",
                            {}
                        )

                        strongest_comparison = (
                            comparison.get(
                                strongest_name,
                                {}
                            )
                        )

                        weakest_comparison = (
                            comparison.get(
                                weakest_name,
                                {}
                            )
                        )

                        if (
                            strongest_comparison
                            and weakest_comparison
                        ):

                            price_difference = (
                                strongest_comparison.get(
                                    "average_unit_price",
                                    0
                                )
                                -
                                weakest_comparison.get(
                                    "average_unit_price",
                                    0
                                )
                            )

                            discount_difference = (
                                strongest_comparison.get(
                                    "average_discount",
                                    0
                                )
                                -
                                weakest_comparison.get(
                                    "average_discount",
                                    0
                                )
                            )

                            insights.append(
                                f"{strongest_name} has an average "
                                f"unit price that is "
                                f"{price_difference} higher than "
                                f"{weakest_name}."
                            )

                            insights.append(
                                f"The average discount difference "
                                f"between {strongest_name} and "
                                f"{weakest_name} is "
                                f"{discount_difference} percentage "
                                f"points."
                            )

                # -------------------------------------------------
                # NUMERIC SUMMARY FALLBACK
                # -------------------------------------------------

        if data_analysis_found and not any(
            result.get(
                "output",
                {}
            ).get(
                "product_analysis"
            )
            for result in results
            if (
                result.get("tool") == "data_analysis"
                and result.get("status") == "success"
            )
        ):

            numeric_summary = {}

            for result in results:

                if result.get(
                    "tool"
                ) != "data_analysis":
                    continue

                output = result.get(
                    "output"
                ) or {}

                numeric_summary = output.get(
                    "numeric_summary",
                    {}
                )

            for column, summary in (
                numeric_summary.items()
            ):

                total = summary.get(
                    "sum"
                )

                average = summary.get(
                    "average"
                )

                minimum = summary.get(
                    "minimum"
                )

                maximum = summary.get(
                    "maximum"
                )

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
        # ADD GENERAL RECOMMENDATION ONLY IF INVESTIGATION
        # IS STILL REQUIRED
        # -------------------------------------------------

        if investigation["required"]:

            recommendations.append(
                "Collect historical product-level sales "
                "data and compare the trend with relevant "
                "market and competitor evidence."
            )

        # -------------------------------------------------
        # IF HISTORICAL EVIDENCE IS AVAILABLE,
        # DO NOT KEEP OLD GAP
        # -------------------------------------------------

        if historical_trend_available:

            evidence_gaps = [
                gap
                for gap in evidence_gaps
                if gap != (
                    "Product-level historical trend"
                )
            ]

            # Historical evidence is already available,
            # so the old investigation question does not
            # need to trigger another investigation.

            investigation["questions"] = [
                question
                for question in investigation[
                    "questions"
                ]
                if "persistent over time" not in (
                    question.lower()
                )
            ]

        # -------------------------------------------------
        # IF ALL CURRENT EVIDENCE GAPS ARE RESOLVED
        # -------------------------------------------------

        if not evidence_gaps:

            investigation["required"] = False

            investigation["reason"] = None

            investigation["questions"] = []

        # -------------------------------------------------
        # DEDUPLICATION
        # -------------------------------------------------

        insights = list(
            dict.fromkeys(
                insights
            )
        )

        recommendations = list(
            dict.fromkeys(
                recommendations
            )
        )

        evidence_gaps = list(
            dict.fromkeys(
                evidence_gaps
            )
        )

        investigation["questions"] = list(
            dict.fromkeys(
                investigation[
                    "questions"
                ]
            )
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
