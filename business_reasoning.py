from typing import Any, Dict, List


class BusinessReasoning:

    def reason(
        self,
        aggregated_result: Dict[str, Any],
        user_request: str = ""
    ) -> Dict[str, Any]:

        # =================================================
        # BASIC VALIDATION
        # =================================================

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

        results = aggregated_result.get("results", [])

        insights: List[str] = []
        recommendations: List[str] = []
        evidence_gaps: List[str] = []
        issues: List[str] = []

        investigation = {
            "required": False,
            "reason": None,
            "questions": []
        }

        business_concern = None

        # =================================================
        # QUERY INTENT
        # =================================================

        request = (user_request or "").lower()

        product_keywords = [
            "product",
            "products",
            "item",
            "items"
        ]

        region_keywords = [
            "region",
            "regions",
            "area",
            "areas",
            "location",
            "locations"
        ]

        monthly_keywords = [
            "month",
            "monthly",
            "sales dropped",
            "sales drop",
            "sales declined",
            "sales decline",
            "revenue dropped",
            "revenue decline",
            "revenue decreased",
            "decrease",
            "decline",
            "declined",
            "slowdown",
            "latest sales",
            "latest revenue",
            "trend",
            "trends"
        ]

        product_query = any(
            keyword in request
            for keyword in product_keywords
        )

        region_query = any(
            keyword in request
            for keyword in region_keywords
        )

        monthly_query = any(
            keyword in request
            for keyword in monthly_keywords
        )

        if product_query:
            query_intent = "product"

        elif region_query:
            query_intent = "region"

        elif monthly_query:
            query_intent = "monthly"

        else:
            query_intent = "general"

        # =================================================
        # FLAGS
        # =================================================

        data_analysis_found = False
        web_search_found = False

        historical_trend_available = False
        product_comparison_available = False

        region_analysis_available = False

        regional_product_investigation_available = False
        regional_trend_investigation_available = False

        # =================================================
        # WEB EVIDENCE
        # =================================================

        external_evidence: List[str] = []

        for result in results:

            if result.get("status") != "success":
                continue

            if result.get("tool") != "web_search":
                continue

            web_search_found = True

            output = result.get("output") or {}

            search_results = []

            if isinstance(output, list):
                search_results = output

            elif isinstance(output, dict):
                search_results = (
                    output.get("results")
                    or output.get("search_results")
                    or output.get("items")
                    or []
                )

            if isinstance(search_results, list):

                for item in search_results:

                    if not isinstance(item, dict):
                        continue

                    title = (
                        item.get("title")
                        or item.get("name")
                    )

                    snippet = (
                        item.get("snippet")
                        or item.get("description")
                        or item.get("content")
                        or item.get("text")
                    )

                    if title and snippet:
                        external_evidence.append(
                            f"{title}: {snippet}"
                        )

                    elif snippet:
                        external_evidence.append(
                            str(snippet)
                        )

            if not external_evidence and isinstance(
                output,
                dict
            ):

                direct_text = (
                    output.get("content")
                    or output.get("answer")
                    or output.get("text")
                )

                if direct_text:
                    external_evidence.append(
                        str(direct_text)
                    )

        # =================================================
        # FIND DATA ANALYSIS OUTPUTS
        # =================================================

        analysis_outputs = []

        for result in results:

            if (
                result.get("status") == "success"
                and result.get("tool") == "data_analysis"
            ):

                data_analysis_found = True

                output = result.get("output") or {}

                if isinstance(output, dict):
                    analysis_outputs.append(output)

        # =================================================
        # DETECT INVESTIGATION EVIDENCE
        # =================================================

        for output in analysis_outputs:

            investigation_output = output.get(
                "investigation",
                {}
            )

            if not isinstance(
                investigation_output,
                dict
            ):
                continue

            investigation_type = (
                investigation_output.get("type")
            )

            if investigation_type == "historical_trend":
                historical_trend_available = True

            if investigation_type == "product_comparison":
                product_comparison_available = True

            if investigation_type == (
                "regional_product_contribution"
            ):
                regional_product_investigation_available = True

            if investigation_type == (
                "regional_historical_trend"
            ):
                regional_trend_investigation_available = True

        # =================================================
        # EXTERNAL MARKET CONTEXT
        # =================================================

        if web_search_found and external_evidence:

            insights.append(
                "External market research provides "
                "context on pricing, customer demand, "
                "competition, consumer behavior, and "
                "broader market conditions. These sources "
                "do not by themselves prove which factor "
                "caused the company's observed performance."
            )

            evidence_gaps.append(
                "Business-specific external market causality"
            )

        # =================================================
        # PRODUCT REASONING
        # =================================================

        if query_intent == "product":

            for output in analysis_outputs:

                product_analysis = output.get(
                    "product_analysis",
                    {}
                )

                if not isinstance(
                    product_analysis,
                    dict
                ) or not product_analysis:
                    continue

                requested_products = []

                for product_name in product_analysis:

                    if product_name.lower() in request:
                        requested_products.append(
                            product_name
                        )

                # -----------------------------------------
                # EXPLICIT COMPARISON
                # -----------------------------------------

                if len(requested_products) >= 2:

                    first_product = requested_products[0]
                    second_product = requested_products[1]

                    first = product_analysis.get(
                        first_product,
                        {}
                    )

                    second = product_analysis.get(
                        second_product,
                        {}
                    )

                    if first and second:

                        revenue_difference = (
                            first.get("revenue", 0)
                            - second.get("revenue", 0)
                        )

                        units_difference = (
                            first.get("units_sold", 0)
                            - second.get("units_sold", 0)
                        )

                        price_difference = (
                            first.get(
                                "average_unit_price",
                                0
                            )
                            - second.get(
                                "average_unit_price",
                                0
                            )
                        )

                        discount_difference = (
                            first.get(
                                "average_discount",
                                0
                            )
                            - second.get(
                                "average_discount",
                                0
                            )
                        )

                        insights.append(
                            f"{first_product} generated "
                            f"{first.get('revenue', 0):,.2f} "
                            f"in recorded revenue compared "
                            f"with {second_product}'s "
                            f"{second.get('revenue', 0):,.2f}."
                        )

                        insights.append(
                            f"The revenue difference between "
                            f"{first_product} and "
                            f"{second_product} is "
                            f"{revenue_difference:,.2f}."
                        )

                        insights.append(
                            f"{first_product} sold "
                            f"{first.get('units_sold', 0)} units "
                            f"versus "
                            f"{second_product}'s "
                            f"{second.get('units_sold', 0)} units, "
                            f"a difference of "
                            f"{units_difference} units."
                        )

                        insights.append(
                            f"The average unit price difference "
                            f"between {first_product} and "
                            f"{second_product} is "
                            f"{price_difference:,.2f}."
                        )

                        insights.append(
                            f"The average discount difference "
                            f"between {first_product} and "
                            f"{second_product} is "
                            f"{discount_difference:,.2f} "
                            f"percentage points."
                        )

                        business_concern = (
                            f"The observed performance gap "
                            f"between {first_product} and "
                            f"{second_product} should be "
                            f"examined through unit sales, "
                            f"pricing, discounts, and demand."
                        )

                        recommendations.extend([
                            f"Compare the pricing and discount "
                            f"strategy of {first_product} and "
                            f"{second_product}.",

                            f"Analyze monthly unit sales of "
                            f"{first_product} and {second_product} "
                            f"to identify when the performance "
                            f"gap expanded or narrowed.",

                            f"Review regional and customer-level "
                            f"performance for {first_product} and "
                            f"{second_product}."
                        ])

                        break

                # -----------------------------------------
                # GENERAL PRODUCT QUESTION
                # -----------------------------------------

                else:

                    strongest = output.get(
                        "strongest_product"
                    )

                    weakest = output.get(
                        "weakest_product"
                    )

                    if strongest and weakest:

                        strongest_name = strongest.get(
                            "product"
                        )

                        weakest_name = weakest.get(
                            "product"
                        )

                        insights.append(
                            f"{strongest_name} is the strongest "
                            f"product by recorded revenue at "
                            f"{strongest.get('revenue', 0):,.2f}."
                        )

                        insights.append(
                            f"{weakest_name} is the weakest "
                            f"product by recorded revenue at "
                            f"{weakest.get('revenue', 0):,.2f}."
                        )

                        business_concern = (
                            f"The main product performance gap "
                            f"is between {strongest_name} and "
                            f"{weakest_name}."
                        )

                        recommendations.extend([
                            "Compare pricing and discount "
                            "strategy across products.",

                            "Review unit-sales trends to identify "
                            "products with weakening demand.",

                            "Analyze regional performance to find "
                            "where weaker products have the "
                            "largest growth opportunity."
                        ])

                        break

        # =================================================
        # REGION REASONING
        # =================================================

        elif query_intent == "region":

            # -------------------------------------------------
            # INITIAL REGIONAL ANALYSIS
            # -------------------------------------------------

            for output in analysis_outputs:

                region_analysis = output.get(
                    "region_analysis",
                    {}
                )

                if not isinstance(
                    region_analysis,
                    dict
                ) or not region_analysis:
                    continue

                region_analysis_available = True

                weakest_region = min(
                    region_analysis.items(),
                    key=lambda item: item[1].get(
                        "revenue",
                        0
                    )
                )

                strongest_region = max(
                    region_analysis.items(),
                    key=lambda item: item[1].get(
                        "revenue",
                        0
                    )
                )

                weakest_name = weakest_region[0]
                weakest_data = weakest_region[1]

                strongest_name = strongest_region[0]
                strongest_data = strongest_region[1]

                revenue_gap = (
                    strongest_data.get("revenue", 0)
                    - weakest_data.get("revenue", 0)
                )

                units_gap = (
                    strongest_data.get("units_sold", 0)
                    - weakest_data.get("units_sold", 0)
                )

                insights.append(
                    f"{weakest_name} is the weakest region "
                    f"by recorded revenue at "
                    f"{weakest_data.get('revenue', 0):,.2f}."
                )

                insights.append(
                    f"{strongest_name} has the highest recorded "
                    f"regional revenue at "
                    f"{strongest_data.get('revenue', 0):,.2f}."
                )

                insights.append(
                    f"The revenue gap between "
                    f"{strongest_name} and {weakest_name} "
                    f"is {revenue_gap:,.2f}."
                )

                insights.append(
                    f"{weakest_name} recorded "
                    f"{weakest_data.get('units_sold', 0)} "
                    f"units sold compared with "
                    f"{strongest_name}'s "
                    f"{strongest_data.get('units_sold', 0)} "
                    f"units."
                )

                insights.append(
                    f"The unit-sales difference between "
                    f"{strongest_name} and {weakest_name} "
                    f"is {units_gap} units."
                )

                business_concern = (
                    f"{weakest_name} is the weakest recorded "
                    f"region and requires analysis of its "
                    f"product mix, unit sales, pricing, and "
                    f"customer demand."
                )

                investigation["required"] = True

                investigation["reason"] = (
                    f"{weakest_name} has the lowest recorded "
                    f"regional revenue. Additional regional "
                    f"and product-level evidence is needed "
                    f"to understand the performance gap."
                )

                investigation["questions"].extend([
                    f"Which products contribute most to "
                    f"{weakest_name}'s performance?",

                    f"Is {weakest_name}'s weaker performance "
                    f"consistent across the observed months?"
                ])

                recommendations.extend([
                    f"Break down {weakest_name} revenue by "
                    f"product to identify its weakest product mix.",

                    f"Compare unit sales, pricing, and discounts "
                    f"in {weakest_name} with stronger regions.",

                    f"Review monthly performance of "
                    f"{weakest_name} to identify periods of "
                    f"decline or weak demand."
                ])

                break

            # -------------------------------------------------
            # INVESTIGATION EVIDENCE
            # -------------------------------------------------

            for output in analysis_outputs:

                investigation_data = output.get(
                    "investigation",
                    {}
                )

                if not isinstance(
                    investigation_data,
                    dict
                ):
                    continue

                investigation_type = investigation_data.get(
                    "type"
                )

                # ---------------------------------------------
                # REGIONAL PRODUCT CONTRIBUTION
                # ---------------------------------------------

                if (
                    investigation_type
                    == "regional_product_contribution"
                ):

                    region = investigation_data.get(
                        "region"
                    )

                    product_analysis = investigation_data.get(
                        "product_analysis",
                        {}
                    )

                    if not isinstance(
                        product_analysis,
                        dict
                    ) or not product_analysis:
                        continue

                    ranked_products = sorted(
                        product_analysis.items(),
                        key=lambda item: item[1].get(
                            "revenue",
                            0
                        ),
                        reverse=True
                    )

                    top_product_name = ranked_products[0][0]
                    top_product_data = ranked_products[0][1]

                    total_revenue = sum(
                        product_data.get(
                            "revenue",
                            0
                        )
                        for _, product_data
                        in ranked_products
                    )

                    top_revenue = top_product_data.get(
                        "revenue",
                        0
                    )

                    top_share = (
                        top_revenue / total_revenue * 100
                        if total_revenue
                        else 0
                    )

                    insights.append(
                        f"In {region}, "
                        f"{top_product_name} contributes the "
                        f"most recorded revenue at "
                        f"{top_revenue:,.2f}, representing "
                        f"approximately {top_share:.2f}% of "
                        f"the region's recorded revenue."
                    )

                    if len(ranked_products) >= 2:

                        second_name = ranked_products[1][0]
                        second_data = ranked_products[1][1]

                        insights.append(
                            f"{second_name} contributes "
                            f"{second_data.get('revenue', 0):,.2f} "
                            f"in recorded revenue in {region}, "
                            f"while the lowest contributing product "
                            f"generates "
                            f"{ranked_products[-1][1].get('revenue', 0):,.2f}."
                        )

                    business_concern = (
                        f"{region}'s performance is concentrated "
                        f"across its product mix, with "
                        f"{top_product_name} being the largest "
                        f"recorded revenue contributor."
                    )

                # ---------------------------------------------
                # REGIONAL HISTORICAL TREND
                # ---------------------------------------------

                elif (
                    investigation_type
                    == "regional_historical_trend"
                ):

                    region = investigation_data.get(
                        "region"
                    )

                    monthly_analysis = investigation_data.get(
                        "monthly_analysis",
                        {}
                    )

                    monthly_change = investigation_data.get(
                        "monthly_change",
                        {}
                    )

                    if not isinstance(
                        monthly_analysis,
                        dict
                    ):
                        continue

                    if monthly_analysis:

                        ordered_months = sorted(
                            monthly_analysis.keys()
                        )

                        first_month = ordered_months[0]
                        last_month = ordered_months[-1]

                        first_revenue = monthly_analysis[
                            first_month
                        ].get(
                            "revenue",
                            0
                        )

                        last_revenue = monthly_analysis[
                            last_month
                        ].get(
                            "revenue",
                            0
                        )

                        insights.append(
                            f"For {region}, recorded monthly "
                            f"revenue ranged from "
                            f"{first_revenue:,.2f} in "
                            f"{first_month} to "
                            f"{last_revenue:,.2f} in "
                            f"{last_month} over the available "
                            f"observations."
                        )

                    decrease_months = []

                    if isinstance(
                        monthly_change,
                        dict
                    ):

                        for month, change_data in (
                            monthly_change.items()
                        ):

                            if (
                                isinstance(
                                    change_data,
                                    dict
                                )
                                and change_data.get(
                                    "direction"
                                ) == "decrease"
                            ):

                                decrease_months.append(
                                    (
                                        month,
                                        change_data.get(
                                            "change_percentage",
                                            0
                                        )
                                    )
                                )

                    if decrease_months:

                        decrease_text = ", ".join(
                            f"{month} ({abs(change):.2f}% decrease)"
                            for month, change
                            in decrease_months
                        )

                        insights.append(
                            f"{region} recorded month-over-month "
                            f"revenue decreases in "
                            f"{decrease_text}."
                        )

                        business_concern = (
                            f"{region} shows periods of recorded "
                            f"revenue decline that should be "
                            f"examined alongside product mix, "
                            f"pricing, discounts, and demand."
                        )

                    else:

                        insights.append(
                            f"No month-over-month revenue "
                            f"decreases were observed for "
                            f"{region} in the available data."
                        )

            # -------------------------------------------------
            # INVESTIGATION-BASED RECOMMENDATIONS
            # -------------------------------------------------

            if (
                regional_product_investigation_available
                or regional_trend_investigation_available
            ):

                recommendations.extend([
                    "Review the strongest and weakest products "
                    "within the weakest region and identify "
                    "product-specific demand opportunities.",

                    "Compare the weakest region's pricing, "
                    "discounts, and unit sales with stronger "
                    "regions.",

                    "Investigate the months showing revenue "
                    "declines to determine whether the pattern "
                    "is associated with product mix or demand."
                ])

        # =================================================
        # MONTHLY REASONING
        # =================================================

        elif query_intent == "monthly":

            for output in analysis_outputs:

                monthly_change = output.get(
                    "monthly_change",
                    {}
                )

                if not isinstance(
                    monthly_change,
                    dict
                ) or not monthly_change:
                    continue

                sorted_months = sorted(
                    monthly_change.keys()
                )

                latest_month = sorted_months[-1]

                latest = monthly_change.get(
                    latest_month,
                    {}
                )

                direction = latest.get(
                    "direction"
                )

                change = latest.get(
                    "change_percentage"
                )

                previous_month = latest.get(
                    "previous_month"
                )

                current_revenue = latest.get(
                    "current_revenue"
                )

                previous_revenue = latest.get(
                    "previous_revenue"
                )

                if direction == "increase":

                    insights.append(
                        f"Revenue increased in the latest "
                        f"observed month ({latest_month}) "
                        f"from {previous_revenue:,.2f} in "
                        f"{previous_month} to "
                        f"{current_revenue:,.2f}, a "
                        f"{change:.2f}% increase."
                    )

                    business_concern = (
                        "The latest observed month shows "
                        "revenue growth rather than a decline."
                    )

                elif direction == "decrease":

                    insights.append(
                        f"Revenue decreased in the latest "
                        f"observed month ({latest_month}) "
                        f"by {abs(change):.2f}% compared "
                        f"with {previous_month}."
                    )

                    business_concern = (
                        "The latest observed month shows "
                        "a revenue decline requiring "
                        "further investigation."
                    )

                else:

                    insights.append(
                        f"Revenue was stable in the latest "
                        f"observed month ({latest_month}) "
                        f"compared with {previous_month}."
                    )

                recommendations.extend([
                    "Identify which products contributed "
                    "most to the latest monthly movement.",

                    "Compare regional performance during "
                    "the declining or changing months.",

                    "Monitor monthly revenue, units sold, "
                    "pricing, and discounts for early "
                    "detection of future changes."
                ])

                break

        # =================================================
        # GENERAL REASONING
        # =================================================

        else:

            for output in analysis_outputs:

                strongest = output.get(
                    "strongest_product"
                )

                weakest = output.get(
                    "weakest_product"
                )

                if strongest and weakest:

                    insights.append(
                        f"{strongest.get('product')} is the "
                        f"strongest product by recorded revenue "
                        f"at {strongest.get('revenue', 0):,.2f}."
                    )

                    insights.append(
                        f"{weakest.get('product')} is the "
                        f"weakest product by recorded revenue "
                        f"at {weakest.get('revenue', 0):,.2f}."
                    )

                    break

        # =================================================
        # EXTERNAL EVIDENCE
        # =================================================

        if web_search_found and external_evidence:

            if query_intent == "monthly":

                evidence_gaps.append(
                    "Business-specific external market causality"
                )

                if any(
                    "decrease" in str(
                        output.get(
                            "monthly_change",
                            {}
                        )
                    ).lower()
                    for output in analysis_outputs
                ):

                    investigation["required"] = True

                    investigation["questions"].append(
                        "Which external market factors, if any, "
                        "are supported by business-specific evidence?"
                    )

            else:

                evidence_gaps = [
                    gap
                    for gap in evidence_gaps
                    if gap != (
                        "Business-specific external market causality"
                    )
                ]

        # =================================================
        # REMOVE UNNECESSARY INVESTIGATION
        # =================================================

        if query_intent == "product":
            pass

        elif query_intent == "region":

            investigation["questions"] = [
                question
                for question in investigation["questions"]
                if "Product A" not in question
                and "Product C" not in question
            ]

        # =================================================
        # DEDUPLICATION
        # =================================================

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
                investigation["questions"]
            )
        )

        # =================================================
        # MAX 3 RECOMMENDATIONS
        # =================================================

        recommendations = recommendations[:3]

        # =================================================
        # FINAL INVESTIGATION STATE
        # =================================================

        if not investigation["questions"]:
            investigation["required"] = False
            investigation["reason"] = None

        # =================================================
        # FALLBACK
        # =================================================

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
