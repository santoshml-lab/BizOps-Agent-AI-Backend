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

        if not isinstance(aggregated_result, dict):
            return self._failed_result(
                "Aggregated result is invalid."
            )

        if aggregated_result.get("status") != "success":
            return self._failed_result(
                "Aggregated result is not valid."
            )

        results = aggregated_result.get("results", [])

        if not isinstance(results, list):
            results = []

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

        request = (
            user_request or ""
        ).lower().strip()

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

        product_why_investigation_available = False
        product_historical_investigation_available = False

        # =================================================
        # WEB EVIDENCE
        # =================================================

        external_evidence: List[str] = []

        for result in results:

            if not isinstance(result, dict):
                continue

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

            if (
                not external_evidence
                and isinstance(output, dict)
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

            if not isinstance(result, dict):
                continue

            if (
                result.get("status") == "success"
                and result.get("tool") == "data_analysis"
            ):

                data_analysis_found = True

                output = (
                    result.get("output")
                    or {}
                )

                if isinstance(output, dict):

                    analysis_outputs.append(
                        output
                    )

        # =================================================
        # DETECT INVESTIGATION EVIDENCE
        # =================================================

        for output in analysis_outputs:

            investigation_output = (
                output.get(
                    "investigation",
                    {}
                )
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

                product_historical_investigation_available = True

            elif investigation_type == "product_comparison":

                product_comparison_available = True

                product_why_investigation_available = True

            elif investigation_type == "product_performance":

                product_why_investigation_available = True

            elif (
                investigation_type
                == "regional_product_contribution"
            ):

                regional_product_investigation_available = True

            elif (
                investigation_type
                == "regional_historical_trend"
            ):

                regional_trend_investigation_available = True

        # =================================================
        # EXTERNAL MARKET CONTEXT
        # =================================================

        if (
            web_search_found
            and external_evidence
        ):

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

                product_analysis = (
                    output.get(
                        "product_analysis",
                        {}
                    )
                )

                if (
                    not isinstance(
                        product_analysis,
                        dict
                    )
                    or not product_analysis
                ):
                    continue

                requested_products = []

                for product_name in product_analysis:

                    if not isinstance(
                        product_name,
                        str
                    ):
                        continue

                    if (
                        product_name.lower()
                        in request
                    ):

                        requested_products.append(
                            product_name
                        )

                # -----------------------------------------
                # EXPLICIT PRODUCT COMPARISON
                # -----------------------------------------

                if len(requested_products) >= 2:

                    first_product = (
                        requested_products[0]
                    )

                    second_product = (
                        requested_products[1]
                    )

                    first = (
                        product_analysis.get(
                            first_product,
                            {}
                        )
                    )

                    second = (
                        product_analysis.get(
                            second_product,
                            {}
                        )
                    )

                    if (
                        isinstance(first, dict)
                        and isinstance(second, dict)
                    ):

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
                            f"{first_product} and "
                            f"{second_product} to identify "
                            f"when the performance gap "
                            f"expanded or narrowed.",

                            f"Review regional and customer-level "
                            f"performance for "
                            f"{first_product} and "
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

                    # -------------------------------------
                    # STRONGEST PRODUCT
                    # -------------------------------------

                    if isinstance(
                        strongest,
                        dict
                    ):

                        strongest_name = (
                            strongest.get("product")
                            or strongest.get("name")
                        )

                        strongest_revenue = (
                            strongest.get(
                                "revenue",
                                0
                            )
                        )

                    else:

                        strongest_name = (
                            str(strongest)
                            if strongest
                            else None
                        )

                        strongest_data = (
                            product_analysis.get(
                                strongest_name,
                                {}
                            )
                            if strongest_name
                            else {}
                        )

                        strongest_revenue = (
                            strongest_data.get(
                                "revenue",
                                0
                            )
                            if isinstance(
                                strongest_data,
                                dict
                            )
                            else 0
                        )

                    # -------------------------------------
                    # WEAKEST PRODUCT
                    # -------------------------------------

                    if isinstance(
                        weakest,
                        dict
                    ):

                        weakest_name = (
                            weakest.get("product")
                            or weakest.get("name")
                        )

                        weakest_revenue = (
                            weakest.get(
                                "revenue",
                                0
                            )
                        )

                    else:

                        weakest_name = (
                            str(weakest)
                            if weakest
                            else None
                        )

                        weakest_data = (
                            product_analysis.get(
                                weakest_name,
                                {}
                            )
                            if weakest_name
                            else {}
                        )

                        weakest_revenue = (
                            weakest_data.get(
                                "revenue",
                                0
                            )
                            if isinstance(
                                weakest_data,
                                dict
                            )
                            else 0
                        )

                    if (
                        strongest_name
                        and weakest_name
                    ):

                        insights.append(
                            f"{strongest_name} is the strongest "
                            f"product by recorded revenue at "
                            f"{strongest_revenue:,.2f}."
                        )

                        insights.append(
                            f"{weakest_name} is the weakest "
                            f"product by recorded revenue at "
                            f"{weakest_revenue:,.2f}."
                        )

                        business_concern = (
                            f"The main product performance "
                            f"gap is between "
                            f"{strongest_name} and "
                            f"{weakest_name}."
                        )

                        recommendations.extend([
                            "Compare pricing and discount "
                            "strategy across products.",

                            "Review unit-sales trends to "
                            "identify products with "
                            "weakening demand.",

                            "Analyze regional performance "
                            "to find where weaker products "
                            "have the largest growth "
                            "opportunity."
                        ])

                        # ---------------------------------
                        # PRODUCT WHY INVESTIGATION
                        # ---------------------------------

                        why_keywords = [
                            "why",
                            "how",
                            "factor",
                            "factors",
                            "reason",
                            "reasons",
                            "driver",
                            "drivers",
                            "outperform",
                            "outperforms"
                        ]

                        if any(
                            keyword in request
                            for keyword in why_keywords
                        ):

                            investigation[
                                "required"
                            ] = True

                            investigation[
                                "reason"
                            ] = (
                                f"The query asks why "
                                f"{strongest_name} generates "
                                f"the highest recorded "
                                f"revenue. Additional "
                                f"product-level evidence "
                                f"is needed to examine "
                                f"units sold, pricing, "
                                f"discounts, and historical "
                                f"performance."
                            )

                            investigation[
                                "questions"
                            ].extend([

                                f"Why does "
                                f"{strongest_name} generate "
                                f"more revenue than the "
                                f"other products based on "
                                f"units sold, pricing, and "
                                f"discounts?",

                                f"Is "
                                f"{strongest_name}'s revenue "
                                f"advantage consistent "
                                f"across the observed "
                                f"months?",

                                f"What factors are associated "
                                f"with "
                                f"{strongest_name}'s higher "
                                f"revenue performance?"
                            ])

                        break

        # =================================================
        # REGION REASONING
        # =================================================

        elif query_intent == "region":

            weakest_region = None

            # -------------------------------------------------
            # INITIAL REGIONAL ANALYSIS
            # -------------------------------------------------

            for output in analysis_outputs:

                region_analysis = (
                    output.get(
                        "region_analysis",
                        {}
                    )
                )

                if (
                    not isinstance(
                        region_analysis,
                        dict
                    )
                    or not region_analysis
                ):
                    continue

                region_analysis_available = True

                valid_regions = []

                for (
                    region_name,
                    region_data
                ) in region_analysis.items():

                    if isinstance(
                        region_data,
                        dict
                    ):

                        valid_regions.append(
                            (
                                region_name,
                                region_data
                            )
                        )

                if not valid_regions:
                    continue

                weakest_region = min(
                    valid_regions,
                    key=lambda item:
                    item[1].get(
                        "revenue",
                        0
                    )
                )

                strongest_region = max(
                    valid_regions,
                    key=lambda item:
                    item[1].get(
                        "revenue",
                        0
                    )
                )

                weakest_name = weakest_region[0]
                weakest_data = weakest_region[1]

                strongest_name = strongest_region[0]
                strongest_data = strongest_region[1]

                revenue_gap = (
                    strongest_data.get(
                        "revenue",
                        0
                    )
                    - weakest_data.get(
                        "revenue",
                        0
                    )
                )

                units_gap = (
                    strongest_data.get(
                        "units_sold",
                        0
                    )
                    - weakest_data.get(
                        "units_sold",
                        0
                    )
                )

                insights.append(
                    f"{weakest_name} is the weakest region "
                    f"by recorded revenue at "
                    f"{weakest_data.get('revenue', 0):,.2f}."
                )

                insights.append(
                    f"{strongest_name} has the highest "
                    f"recorded regional revenue at "
                    f"{strongest_data.get('revenue', 0):,.2f}."
                )

                insights.append(
                    f"The revenue gap between "
                    f"{strongest_name} and "
                    f"{weakest_name} is "
                    f"{revenue_gap:,.2f}."
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
                    f"{strongest_name} and "
                    f"{weakest_name} is "
                    f"{units_gap} units."
                )

                business_concern = (
                    f"{weakest_name} is the weakest "
                    f"recorded region and requires "
                    f"analysis of its product mix, "
                    f"unit sales, pricing, and "
                    f"customer demand."
                )

                investigation[
                    "required"
                ] = True

                investigation[
                    "reason"
                ] = (
                    f"{weakest_name} has the lowest "
                    f"recorded regional revenue. "
                    f"Additional regional and "
                    f"product-level evidence is needed "
                    f"to understand the performance gap."
                )

                investigation[
                    "questions"
                ].extend([

                    f"Which products contribute most "
                    f"to {weakest_name}'s performance?",

                    f"Is {weakest_name}'s weaker "
                    f"performance consistent across "
                    f"the observed months?"
                ])

                break

            # -------------------------------------------------
            # REGIONAL INVESTIGATION EVIDENCE
            # -------------------------------------------------

            for output in analysis_outputs:

                investigation_data = (
                    output.get(
                        "investigation",
                        {}
                    )
                )

                if not isinstance(
                    investigation_data,
                    dict
                ):
                    continue

                investigation_type = (
                    investigation_data.get(
                        "type"
                    )
                )

                # ---------------------------------------------
                # REGIONAL PRODUCT CONTRIBUTION
                # ---------------------------------------------

                if (
                    investigation_type
                    == "regional_product_contribution"
                ):

                    region = (
                        investigation_data.get(
                            "region"
                        )
                    )

                    product_analysis = (
                        investigation_data.get(
                            "product_analysis",
                            {}
                        )
                    )

                    if (
                        not isinstance(
                            product_analysis,
                            dict
                        )
                        or not product_analysis
                    ):
                        continue

                    ranked_products = []

                    for (
                        product_name,
                        product_data
                    ) in product_analysis.items():

                        if isinstance(
                            product_data,
                            dict
                        ):

                            ranked_products.append(
                                (
                                    product_name,
                                    product_data
                                )
                            )

                    ranked_products.sort(
                        key=lambda item:
                        item[1].get(
                            "revenue",
                            0
                        ),
                        reverse=True
                    )

                    if not ranked_products:
                        continue

                    top_product_name = (
                        ranked_products[0][0]
                    )

                    top_product_data = (
                        ranked_products[0][1]
                    )

                    total_revenue = sum(
                        product_data.get(
                            "revenue",
                            0
                        )
                        for (
                            _,
                            product_data
                        )
                        in ranked_products
                    )

                    top_revenue = (
                        top_product_data.get(
                            "revenue",
                            0
                        )
                    )

                    top_share = (
                        top_revenue
                        / total_revenue
                        * 100
                        if total_revenue
                        else 0
                    )

                    insights.append(
                        f"In {region}, "
                        f"{top_product_name} contributes "
                        f"the most recorded revenue at "
                        f"{top_revenue:,.2f}, representing "
                        f"approximately {top_share:.2f}% "
                        f"of the region's recorded revenue."
                    )

                    if len(
                        ranked_products
                    ) >= 2:

                        second_name = (
                            ranked_products[1][0]
                        )

                        second_data = (
                            ranked_products[1][1]
                        )

                        lowest_name = (
                            ranked_products[-1][0]
                        )

                        lowest_data = (
                            ranked_products[-1][1]
                        )

                        insights.append(
                            f"{second_name} contributes "
                            f"{second_data.get('revenue', 0):,.2f} "
                            f"in recorded revenue in "
                            f"{region}, while "
                            f"{lowest_name} contributes "
                            f"{lowest_data.get('revenue', 0):,.2f}."
                        )

                    business_concern = (
                        f"{region}'s performance is "
                        f"distributed across its product "
                        f"mix, with "
                        f"{top_product_name} being the "
                        f"largest recorded revenue "
                        f"contributor."
                    )

                # ---------------------------------------------
                # REGIONAL HISTORICAL TREND
                # ---------------------------------------------

                elif (
                    investigation_type
                    == "regional_historical_trend"
                ):

                    region = (
                        investigation_data.get(
                            "region"
                        )
                    )

                    monthly_analysis = (
                        investigation_data.get(
                            "monthly_analysis",
                            {}
                        )
                    )

                    monthly_change = (
                        investigation_data.get(
                            "monthly_change",
                            {}
                        )
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

                        first_month = (
                            ordered_months[0]
                        )

                        last_month = (
                            ordered_months[-1]
                        )

                        first_data = (
                            monthly_analysis.get(
                                first_month,
                                {}
                            )
                        )

                        last_data = (
                            monthly_analysis.get(
                                last_month,
                                {}
                            )
                        )

                        first_revenue = (
                            first_data.get(
                                "revenue",
                                0
                            )
                            if isinstance(
                                first_data,
                                dict
                            )
                            else 0
                        )

                        last_revenue = (
                            last_data.get(
                                "revenue",
                                0
                            )
                            if isinstance(
                                last_data,
                                dict
                            )
                            else 0
                        )

                        insights.append(
                            f"For {region}, recorded "
                            f"monthly revenue ranged "
                            f"from {first_revenue:,.2f} "
                            f"in {first_month} to "
                            f"{last_revenue:,.2f} in "
                            f"{last_month} over the "
                            f"available observations."
                        )

                    decrease_months = []

                    if isinstance(
                        monthly_change,
                        dict
                    ):

                        for (
                            month,
                            change_data
                        ) in monthly_change.items():

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
                            f"{month} "
                            f"({abs(change):.2f}% decrease)"
                            for (
                                month,
                                change
                            ) in decrease_months
                        )

                        insights.append(
                            f"{region} recorded "
                            f"month-over-month "
                            f"revenue decreases in "
                            f"{decrease_text}."
                        )

                        business_concern = (
                            f"{region} shows periods "
                            f"of recorded revenue decline "
                            f"that should be examined "
                            f"alongside product mix, "
                            f"pricing, discounts, and "
                            f"demand."
                        )

                    else:

                        insights.append(
                            f"No month-over-month revenue "
                            f"decreases were observed "
                            f"for {region} in the "
                            f"available data."
                        )

            # -------------------------------------------------
            # REGION RECOMMENDATIONS
            # -------------------------------------------------

            if not (
                regional_product_investigation_available
                or regional_trend_investigation_available
            ):

                if (
                    region_analysis_available
                    and weakest_region
                ):

                    weakest_name = (
                        weakest_region[0]
                    )

                    recommendations.extend([

                        f"Break down {weakest_name} "
                        f"revenue by product to identify "
                        f"its weakest product mix.",

                        f"Compare unit sales, pricing, "
                        f"and discounts in {weakest_name} "
                        f"with stronger regions.",

                        f"Review monthly performance of "
                        f"{weakest_name} to identify "
                        f"periods of decline or weak "
                        f"demand."
                    ])

            else:

                if (
                    regional_product_investigation_available
                    and weakest_region
                ):

                    weakest_name = (
                        weakest_region[0]
                    )

                    recommendations.append(
                        f"Compare {weakest_name}'s "
                        f"Product A, Product B, and "
                        f"Product C unit sales, pricing, "
                        f"and discounts with the same "
                        f"products in stronger regions."
                    )

                if (
                    regional_trend_investigation_available
                    and weakest_region
                ):

                    weakest_name = (
                        weakest_region[0]
                    )

                    declining_months = []

                    for output in analysis_outputs:

                        investigation_data = (
                            output.get(
                                "investigation",
                                {}
                            )
                        )

                        if not isinstance(
                            investigation_data,
                            dict
                        ):
                            continue

                        if (
                            investigation_data.get(
                                "type"
                            )
                            !=
                            "regional_historical_trend"
                        ):
                            continue

                        monthly_change = (
                            investigation_data.get(
                                "monthly_change",
                                {}
                            )
                        )

                        if not isinstance(
                            monthly_change,
                            dict
                        ):
                            continue

                        for (
                            month,
                            change_data
                        ) in monthly_change.items():

                            if (
                                isinstance(
                                    change_data,
                                    dict
                                )
                                and change_data.get(
                                    "direction"
                                ) == "decrease"
                            ):

                                declining_months.append(
                                    month
                                )

                    declining_months = list(
                        dict.fromkeys(
                            declining_months
                        )
                    )

                    if declining_months:

                        decline_text = ", ".join(
                            declining_months
                        )

                        recommendations.append(
                            f"Investigate the revenue "
                            f"declines in {decline_text} "
                            f"by examining changes in "
                            f"unit sales and product-level "
                            f"contribution."
                        )

                    else:

                        recommendations.append(
                            f"Monitor {weakest_name}'s "
                            f"monthly revenue and "
                            f"unit-sales performance "
                            f"to determine whether "
                            f"the observed weakness "
                            f"persists."
                        )

                if weakest_region:

                    weakest_name = (
                        weakest_region[0]
                    )

                    recommendations.append(
                        f"Monitor {weakest_name}'s next "
                        f"monthly revenue and unit-sales "
                        f"performance to determine whether "
                        f"the observed weakness persists."
                    )

        # =================================================
        # MONTHLY REASONING
        # =================================================

        elif query_intent == "monthly":

            for output in analysis_outputs:

                monthly_change = (
                    output.get(
                        "monthly_change",
                        {}
                    )
                )

                if (
                    not isinstance(
                        monthly_change,
                        dict
                    )
                    or not monthly_change
                ):
                    continue

                sorted_months = sorted(
                    monthly_change.keys()
                )

                latest_month = (
                    sorted_months[-1]
                )

                latest = (
                    monthly_change.get(
                        latest_month,
                        {}
                    )
                )

                if not isinstance(
                    latest,
                    dict
                ):
                    continue

                direction = (
                    latest.get("direction")
                )

                change = (
                    latest.get(
                        "change_percentage",
                        0
                    )
                )

                previous_month = (
                    latest.get(
                        "previous_month"
                    )
                )

                current_revenue = (
                    latest.get(
                        "current_revenue",
                        0
                    )
                )

                previous_revenue = (
                    latest.get(
                        "previous_revenue",
                        0
                    )
                )

                if direction == "increase":

                    insights.append(
                        f"Revenue increased in the "
                        f"latest observed month "
                        f"({latest_month}) from "
                        f"{previous_revenue:,.2f} in "
                        f"{previous_month} to "
                        f"{current_revenue:,.2f}, "
                        f"a {change:.2f}% increase."
                    )

                    business_concern = (
                        "The latest observed month "
                        "shows revenue growth "
                        "rather than a decline."
                    )

                elif direction == "decrease":

                    insights.append(
                        f"Revenue decreased in the "
                        f"latest observed month "
                        f"({latest_month}) by "
                        f"{abs(change):.2f}% compared "
                        f"with {previous_month}."
                    )

                    business_concern = (
                        "The latest observed month "
                        "shows a revenue decline "
                        "requiring further "
                        "investigation."
                    )

                else:

                    insights.append(
                        f"Revenue was stable in the "
                        f"latest observed month "
                        f"({latest_month}) compared "
                        f"with {previous_month}."
                    )

                recommendations.extend([

                    "Identify which products "
                    "contributed most to the latest "
                    "monthly movement.",

                    "Compare regional performance "
                    "during the declining or "
                    "changing months.",

                    "Monitor monthly revenue, units "
                    "sold, pricing, and discounts "
                    "for early detection of future "
                    "changes."
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

                if not strongest or not weakest:
                    continue

                product_analysis = (
                    output.get(
                        "product_analysis",
                        {}
                    )
                )

                if not isinstance(
                    product_analysis,
                    dict
                ):
                    product_analysis = {}

                # -----------------------------------------
                # STRONGEST
                # -----------------------------------------

                if isinstance(
                    strongest,
                    dict
                ):

                    strongest_name = (
                        strongest.get(
                            "product"
                        )
                        or strongest.get(
                            "name"
                        )
                    )

                    strongest_revenue = (
                        strongest.get(
                            "revenue",
                            0
                        )
                    )

                else:

                    strongest_name = str(
                        strongest
                    )

                    strongest_data = (
                        product_analysis.get(
                            strongest_name,
                            {}
                        )
                    )

                    strongest_revenue = (
                        strongest_data.get(
                            "revenue",
                            0
                        )
                        if isinstance(
                            strongest_data,
                            dict
                        )
                        else 0
                    )

                # -----------------------------------------
                # WEAKEST
                # -----------------------------------------

                if isinstance(
                    weakest,
                    dict
                ):

                    weakest_name = (
                        weakest.get(
                            "product"
                        )
                        or weakest.get(
                            "name"
                        )
                    )

                    weakest_revenue = (
                        weakest.get(
                            "revenue",
                            0
                        )
                    )

                else:

                    weakest_name = str(
                        weakest
                    )

                    weakest_data = (
                        product_analysis.get(
                            weakest_name,
                            {}
                        )
                    )

                    weakest_revenue = (
                        weakest_data.get(
                            "revenue",
                            0
                        )
                        if isinstance(
                            weakest_data,
                            dict
                        )
                        else 0
                    )

                if (
                    strongest_name
                    and weakest_name
                ):

                    insights.append(
                        f"{strongest_name} is the strongest "
                        f"product by recorded revenue at "
                        f"{strongest_revenue:,.2f}."
                    )

                    insights.append(
                        f"{weakest_name} is the weakest "
                        f"product by recorded revenue at "
                        f"{weakest_revenue:,.2f}."
                    )

                    break

        # =================================================
        # PRODUCT INVESTIGATION EVIDENCE
        # =================================================

        if query_intent == "product":

            for output in analysis_outputs:

                investigation_data = (
                    output.get(
                        "investigation",
                        {}
                    )
                )

                if not isinstance(
                    investigation_data,
                    dict
                ):
                    continue

                investigation_type = (
                    investigation_data.get(
                        "type"
                    )
                )

                # -----------------------------------------
                # PRODUCT PERFORMANCE
                # -----------------------------------------

                if (
                    investigation_type
                    == "product_performance"
                ):

                    target_product = (
                        investigation_data.get(
                            "target_product"
                        )
                    )

                    target_data = (
                        investigation_data.get(
                            "target_product_data",
                            {}
                        )
                    )

                    differences = (
                        investigation_data.get(
                            "differences",
                            {}
                        )
                    )

                    if (
                        target_product
                        and isinstance(
                            target_data,
                            dict
                        )
                    ):

                        insights.append(
                            f"{target_product} recorded "
                            f"{target_data.get('revenue', 0):,.2f} "
                            f"in revenue across "
                            f"{target_data.get('orders', 0)} "
                            f"orders and "
                            f"{target_data.get('units_sold', 0)} "
                            f"units."
                        )

                        insights.append(
                            f"{target_product}'s average "
                            f"unit price was "
                            f"{target_data.get('average_unit_price', 0):,.2f} "
                            f"with an average discount of "
                            f"{target_data.get('average_discount', 0):.2f}%."
                        )

                        if isinstance(
                            differences,
                            dict
                        ):

                            for (
                                comparison_product,
                                difference_data
                            ) in differences.items():

                                if not isinstance(
                                    difference_data,
                                    dict
                                ):
                                    continue

                                insights.append(
                                    f"Compared with "
                                    f"{comparison_product}, "
                                    f"{target_product} had a "
                                    f"{difference_data.get('revenue_difference', 0):,.2f} "
                                    f"revenue difference, "
                                    f"{difference_data.get('units_sold_difference', 0)} "
                                    f"unit difference, a "
                                    f"{difference_data.get('average_unit_price_difference', 0):,.2f} "
                                    f"average price difference, "
                                    f"and a "
                                    f"{difference_data.get('average_discount_difference', 0):.2f} "
                                    f"percentage-point "
                                    f"discount difference."
                                )

                        business_concern = (
                            f"{target_product}'s higher "
                            f"recorded revenue is associated "
                            f"with differences in unit volume, "
                            f"pricing, and discounts. These "
                            f"observed factors should be "
                            f"validated against monthly and "
                            f"regional evidence before "
                            f"attributing causality."
                        )

                # -----------------------------------------
                # PRODUCT COMPARISON
                # -----------------------------------------

                elif (
                    investigation_type
                    == "product_comparison"
                ):

                    product_1 = (
                        investigation_data.get(
                            "product_1"
                        )
                    )

                    product_2 = (
                        investigation_data.get(
                            "product_2"
                        )
                    )

                    product_1_data = (
                        investigation_data.get(
                            "product_1_data",
                            {}
                        )
                    )

                    product_2_data = (
                        investigation_data.get(
                            "product_2_data",
                            {}
                        )
                    )

                    if (
                        product_1
                        and product_2
                        and isinstance(
                            product_1_data,
                            dict
                        )
                        and isinstance(
                            product_2_data,
                            dict
                        )
                    ):

                        insights.append(
                            f"Investigation confirms "
                            f"{product_1} recorded "
                            f"{product_1_data.get('revenue', 0):,.2f} "
                            f"in revenue compared with "
                            f"{product_2}'s "
                            f"{product_2_data.get('revenue', 0):,.2f}."
                        )

                        business_concern = (
                            f"The performance difference "
                            f"between {product_1} and "
                            f"{product_2} should be evaluated "
                            f"through volume, pricing, "
                            f"discounts, and regional demand."
                        )

                # -----------------------------------------
                # HISTORICAL TREND
                # -----------------------------------------

                elif (
                    investigation_type
                    == "historical_trend"
                ):

                    target_product = (
                        investigation_data.get(
                            "target_product"
                        )
                    )

                    monthly_analysis = (
                        investigation_data.get(
                            "monthly_analysis",
                            {}
                        )
                    )

                    monthly_change = (
                        investigation_data.get(
                            "monthly_change",
                            {}
                        )
                    )

                    if (
                        target_product
                        and isinstance(
                            monthly_analysis,
                            dict
                        )
                        and monthly_analysis
                    ):

                        ordered_months = sorted(
                            monthly_analysis.keys()
                        )

                        first_month = (
                            ordered_months[0]
                        )

                        last_month = (
                            ordered_months[-1]
                        )

                        first_data = (
                            monthly_analysis.get(
                                first_month,
                                {}
                            )
                        )

                        last_data = (
                            monthly_analysis.get(
                                last_month,
                                {}
                            )
                        )

                        first_revenue = (
                            first_data.get(
                                "revenue",
                                0
                            )
                            if isinstance(
                                first_data,
                                dict
                            )
                            else 0
                        )

                        last_revenue = (
                            last_data.get(
                                "revenue",
                                0
                            )
                            if isinstance(
                                last_data,
                                dict
                            )
                            else 0
                        )

                        insights.append(
                            f"{target_product}'s recorded "
                            f"monthly revenue ranged from "
                            f"{first_revenue:,.2f} in "
                            f"{first_month} to "
                            f"{last_revenue:,.2f} in "
                            f"{last_month} over the "
                            f"available observations."
                        )

                    if isinstance(
                        monthly_change,
                        dict
                    ):

                        decreases = []

                        for (
                            month,
                            change_data
                        ) in monthly_change.items():

                            if (
                                isinstance(
                                    change_data,
                                    dict
                                )
                                and change_data.get(
                                    "direction"
                                ) == "decrease"
                            ):

                                decreases.append(
                                    (
                                        month,
                                        change_data.get(
                                            "change_percentage",
                                            0
                                        )
                                    )
                                )

                        if decreases:

                            decrease_text = ", ".join(
                                f"{month} "
                                f"({abs(change):.2f}% decrease)"
                                for (
                                    month,
                                    change
                                ) in decreases
                            )

                            insights.append(
                                f"{target_product} recorded "
                                f"month-over-month revenue "
                                f"decreases in "
                                f"{decrease_text}."
                            )

        # =================================================
        # EXTERNAL EVIDENCE HANDLING
        # =================================================

        if (
            web_search_found
            and external_evidence
        ):

            if query_intent == "monthly":

                if (
                    "Business-specific external "
                    "market causality"
                    not in evidence_gaps
                ):

                    evidence_gaps.append(
                        "Business-specific external "
                        "market causality"
                    )

                has_decline = False

                for output in analysis_outputs:

                    monthly_change = (
                        output.get(
                            "monthly_change",
                            {}
                        )
                    )

                    if not isinstance(
                        monthly_change,
                        dict
                    ):
                        continue

                    for change_data in (
                        monthly_change.values()
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

                            has_decline = True
                            break

                    if has_decline:
                        break

                if has_decline:

                    investigation[
                        "required"
                    ] = True

                    investigation[
                        "questions"
                    ].append(
                        "Which external market factors, "
                        "if any, are supported by "
                        "business-specific evidence?"
                    )

            else:

                evidence_gaps = [
                    gap
                    for gap in evidence_gaps
                    if gap != (
                        "Business-specific external "
                        "market causality"
                    )
                ]

        # =================================================
        # FINAL CLEANUP
        # =================================================

        unique_insights = []

        for insight in insights:

            if not insight:
                continue

            if insight not in unique_insights:

                unique_insights.append(
                    insight
                )

        insights = unique_insights

        unique_recommendations = []

        for recommendation in recommendations:

            if not recommendation:
                continue

            if recommendation not in unique_recommendations:

                unique_recommendations.append(
                    recommendation
                )

        recommendations = (
            unique_recommendations[:3]
        )

        evidence_gaps = list(
            dict.fromkeys(
                evidence_gaps
            )
        )

        if not isinstance(
            investigation.get("questions"),
            list
        ):

            investigation["questions"] = []

        investigation["questions"] = list(
            dict.fromkeys(
                investigation["questions"]
            )
        )

        # =================================================
        # FINAL RESULT
        # =================================================

        return {
            "status": "success",
            "insights": insights,
            "business_concern": business_concern,
            "evidence_gaps": evidence_gaps,
            "investigation": investigation,
            "recommendations": recommendations,
            "issues": issues
        }

    # =====================================================
    # FAILED RESULT HELPER
    # =====================================================

    def _failed_result(
        self,
        message: str
    ) -> Dict[str, Any]:

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
                message
            ]
                            }
