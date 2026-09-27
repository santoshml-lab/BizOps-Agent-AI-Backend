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

        # =================================================
        # RESULT SOURCE NORMALIZATION
        # =================================================

        original_results = aggregated_result.get(
            "results",
            []
        )

        if not isinstance(original_results, list):
            original_results = []

        investigation_results = aggregated_result.get(
            "investigation_results",
            []
        )

        if not isinstance(investigation_results, list):
            investigation_results = []

        # Some aggregators may wrap original results
        # inside another object.
        if isinstance(
            aggregated_result.get("original_results"),
            dict
        ):

            original_container = (
                aggregated_result.get(
                    "original_results"
                )
            )

            original_results = (
                original_container.get(
                    "results",
                    []
                )
            )

            if not isinstance(
                original_results,
                list
            ):
                original_results = []

        # =================================================
        # COMBINED RESULT COLLECTION
        # =================================================

        all_results: List[Dict[str, Any]] = []

        for result in original_results:

            if isinstance(result, dict):
                all_results.append(result)

        for result in investigation_results:

            if isinstance(result, dict):
                all_results.append(result)

        # =================================================
        # OUTPUT COLLECTION
        # =================================================

        analysis_outputs: List[Dict[str, Any]] = []

        data_analysis_found = False
        web_search_found = False

        # -------------------------------------------------
        # External source metadata
        # -------------------------------------------------

        external_sources: List[Dict[str, str]] = []

        external_source_keys = set()

        # Separate evidence text from source count.
        # This prevents snippets/direct text from
        # accidentally increasing source count.
        external_evidence: List[str] = []

        # Track whether evidence came from investigation.
        investigation_external_sources: List[
            Dict[str, str]
        ] = []

        # =================================================
        # RESULT EXTRACTION
        # =================================================

        for result in all_results:

            if not isinstance(result, dict):
                continue

            if result.get("status") != "success":
                continue

            tool_name = result.get("tool")

            output = result.get("output") or {}

            # -------------------------------------------------
            # DATA ANALYSIS
            # -------------------------------------------------

            if tool_name == "data_analysis":

                data_analysis_found = True

                if isinstance(output, dict):

                    analysis_outputs.append(
                        output
                    )

            # -------------------------------------------------
            # WEB SEARCH
            # -------------------------------------------------

            elif tool_name == "web_search":

                web_search_found = True

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

                # Determine whether this web result
                # belongs to an investigation task.
                is_investigation_result = (
                    result in investigation_results
                )

                if isinstance(search_results, list):

                    for item in search_results:

                        if not isinstance(item, dict):
                            continue

                        title = (
                            item.get("title")
                            or item.get("name")
                            or ""
                        )

                        snippet = (
                            item.get("snippet")
                            or item.get("description")
                            or item.get("content")
                            or item.get("text")
                            or ""
                        )

                        url = (
                            item.get("url")
                            or item.get("link")
                            or item.get("source")
                            or ""
                        )

                        title = str(title).strip()
                        snippet = str(snippet).strip()
                        url = str(url).strip()

                        # -----------------------------------------
                        # UNIQUE SOURCE KEY
                        # -----------------------------------------

                        source_key = (
                            url.lower()
                            if url
                            else title.lower()
                        )

                        if not source_key:

                            source_key = (
                                title.lower()
                                + "|"
                                + snippet.lower()[:200]
                            )

                        # -----------------------------------------
                        # ADD UNIQUE SOURCE
                        # -----------------------------------------

                        if source_key not in external_source_keys:

                            external_source_keys.add(
                                source_key
                            )

                            source_record = {
                                "title": title,
                                "url": url,
                                "snippet": snippet
                            }

                            external_sources.append(
                                source_record
                            )

                            if is_investigation_result:

                                investigation_external_sources.append(
                                    source_record
                                )

                        # -----------------------------------------
                        # STORE EVIDENCE TEXT
                        # -----------------------------------------

                        if title and snippet:

                            external_evidence.append(
                                f"{title}: {snippet}"
                            )

                        elif snippet:

                            external_evidence.append(
                                snippet
                            )

                # -------------------------------------------------
                # DIRECT TEXT OUTPUT
                # -------------------------------------------------

                if isinstance(output, dict):

                    direct_text = (
                        output.get("content")
                        or output.get("answer")
                        or output.get("text")
                    )

                    if direct_text:

                        direct_text = str(
                            direct_text
                        ).strip()

                        if direct_text:

                            external_evidence.append(
                                direct_text
                            )

        # =================================================
        # BASIC OUTPUT STRUCTURES
        # =================================================

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
        # INVESTIGATION FLAGS
        # =================================================

        region_analysis_available = False

        regional_product_investigation_available = False

        regional_trend_investigation_available = False

        product_performance_investigations = []

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
                investigation_output.get(
                    "type"
                )
            )

            if investigation_type == (
                "regional_product_contribution"
            ):

                regional_product_investigation_available = True

            elif investigation_type == (
                "regional_historical_trend"
            ):

                regional_trend_investigation_available = True

            elif investigation_type == (
                "product_performance"
            ):

                product_performance_investigations.append(
                    investigation_output
                )

        # =================================================
        # EXTERNAL MARKET CONTEXT
        # =================================================

        if (
            web_search_found
            and external_sources
        ):

            source_count = len(
                external_sources
            )

            insights.append(
                f"External market research provided "
                f"{source_count} unique source(s) covering "
                f"context such as pricing pressure, changing "
                f"customer behavior, competition, and broader "
                f"market conditions. These sources provide "
                f"market context rather than proof of "
                f"company-specific causation."
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

                # =================================================
                # EXPLICIT PRODUCT COMPARISON
                # =================================================

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

                        insights.extend([

                            f"{first_product} generated "
                            f"{first.get('revenue', 0):,.2f} "
                            f"in recorded revenue compared "
                            f"with {second_product}'s "
                            f"{second.get('revenue', 0):,.2f}.",

                            f"The revenue difference between "
                            f"{first_product} and "
                            f"{second_product} is "
                            f"{revenue_difference:,.2f}.",

                            f"{first_product} sold "
                            f"{first.get('units_sold', 0)} units "
                            f"versus "
                            f"{second_product}'s "
                            f"{second.get('units_sold', 0)} units, "
                            f"a difference of "
                            f"{units_difference} units.",

                            f"The average unit price difference "
                            f"between {first_product} and "
                            f"{second_product} is "
                            f"{price_difference:,.2f}.",

                            f"The average discount difference "
                            f"between {first_product} and "
                            f"{second_product} is "
                            f"{discount_difference:,.2f} "
                            f"percentage points."
                        ])

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

                # =================================================
                # GENERAL PRODUCT QUESTION
                # =================================================

                else:

                    strongest = output.get(
                        "strongest_product"
                    )

                    weakest = output.get(
                        "weakest_product"
                    )

                    # -------------------------------------------------
                    # STRONGEST
                    # -------------------------------------------------

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

                    # -------------------------------------------------
                    # WEAKEST
                    # -------------------------------------------------

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

                        insights.extend([

                            f"{strongest_name} is the strongest "
                            f"product by recorded revenue at "
                            f"{strongest_revenue:,.2f}.",

                            f"{weakest_name} is the weakest "
                            f"product by recorded revenue at "
                            f"{weakest_revenue:,.2f}."
                        ])

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

                            investigation["required"] = True

                            investigation["reason"] = (
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

                            investigation["questions"].extend([

                                f"Why does {strongest_name} "
                                f"generate more revenue than "
                                f"the other products based "
                                f"on units sold, pricing, "
                                f"and discounts?",

                                f"Is {strongest_name}'s revenue "
                                f"advantage consistent across "
                                f"the observed months?",

                                f"What factors are associated "
                                f"with {strongest_name}'s "
                                f"higher revenue performance?"
                            ])

                        break

        # =================================================
        # REGION REASONING
        # =================================================

        elif query_intent == "region":

            weakest_region = None

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
                    strongest_data.get("revenue", 0)
                    - weakest_data.get("revenue", 0)
                )

                units_gap = (
                    strongest_data.get("units_sold", 0)
                    - weakest_data.get("units_sold", 0)
                )

                insights.extend([

                    f"{weakest_name} is the weakest region "
                    f"by recorded revenue at "
                    f"{weakest_data.get('revenue', 0):,.2f}.",

                    f"{strongest_name} has the highest "
                    f"recorded regional revenue at "
                    f"{strongest_data.get('revenue', 0):,.2f}.",

                    f"The revenue gap between "
                    f"{strongest_name} and "
                    f"{weakest_name} is "
                    f"{revenue_gap:,.2f}.",

                    f"{weakest_name} recorded "
                    f"{weakest_data.get('units_sold', 0)} "
                    f"units sold compared with "
                    f"{strongest_name}'s "
                    f"{strongest_data.get('units_sold', 0)} "
                    f"units.",

                    f"The unit-sales difference between "
                    f"{strongest_name} and "
                    f"{weakest_name} is "
                    f"{units_gap} units."
                ])

                business_concern = (
                    f"{weakest_name} is the weakest "
                    f"recorded region and requires "
                    f"analysis of its product mix, "
                    f"unit sales, pricing, and "
                    f"customer demand."
                )

                investigation["required"] = True

                investigation["reason"] = (
                    f"{weakest_name} has the lowest "
                    f"recorded regional revenue. "
                    f"Additional regional and "
                    f"product-level evidence is needed "
                    f"to understand the performance gap."
                )

                investigation["questions"].extend([

                    f"Which products contribute most "
                    f"to {weakest_name}'s performance?",

                    f"Is {weakest_name}'s weaker "
                    f"performance consistent across "
                    f"the observed months?"
                ])

                break

            # =================================================
            # REGIONAL INVESTIGATION EVIDENCE
            # =================================================

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

                # -------------------------------------------------
                # PRODUCT CONTRIBUTION
                # -------------------------------------------------

                if (
                    investigation_type
                    == "regional_product_contribution"
                ):

                    region = investigation_data.get(
                        "region"
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
                        ) in ranked_products
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

                    if len(ranked_products) >= 2:

                        second_name = ranked_products[1][0]
                        second_data = ranked_products[1][1]

                        lowest_name = ranked_products[-1][0]
                        lowest_data = ranked_products[-1][1]

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

                # -------------------------------------------------
                # HISTORICAL REGIONAL TREND
                # -------------------------------------------------

                elif (
                    investigation_type
                    == "regional_historical_trend"
                ):

                    region = investigation_data.get(
                        "region"
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

                        first_month = ordered_months[0]
                        last_month = ordered_months[-1]

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

                    decrease_months = {}

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

                                decrease_months[month] = (
                                    change_data.get(
                                        "change_percentage",
                                        0
                                    )
                                )

                    if decrease_months:

                        decrease_text = ", ".join(
                            f"{month} "
                            f"({abs(change):.2f}% decrease)"
                            for (
                                month,
                                change
                            ) in sorted(
                                decrease_months.items()
                            )
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

            # =================================================
            # REGION RECOMMENDATIONS
            # =================================================

            if (
                region_analysis_available
                and weakest_region
            ):

                weakest_name = weakest_region[0]

                if (
                    regional_product_investigation_available
                    or regional_trend_investigation_available
                ):

                    if regional_product_investigation_available:

                        recommendations.append(
                            f"Compare {weakest_name}'s "
                            f"Product A, Product B, and "
                            f"Product C unit sales, pricing, "
                            f"and discounts with the same "
                            f"products in stronger regions."
                        )

                    if regional_trend_investigation_available:

                        recommendations.append(
                            f"Investigate the revenue "
                            f"declines in the observed "
                            f"weak months by examining "
                            f"unit sales and product-level "
                            f"contribution."
                        )

                    recommendations.append(
                        f"Monitor {weakest_name}'s next "
                        f"monthly revenue and unit-sales "
                        f"performance to determine whether "
                        f"the observed weakness persists."
                    )

                else:

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

        # =================================================
        # MONTHLY REASONING
        # =================================================

        elif query_intent == "monthly":

            monthly_outputs = []

            for output in analysis_outputs:

                monthly_change = (
                    output.get(
                        "monthly_change",
                        {}
                    )
                )

                if (
                    isinstance(
                        monthly_change,
                        dict
                    )
                    and monthly_change
                ):

                    monthly_outputs.append(
                        monthly_change
                    )

            latest_month = None
            latest = None

            # -------------------------------------------------
            # COMBINE MONTHLY RESULTS WITHOUT DUPLICATES
            # -------------------------------------------------

            combined_monthly_change = {}

            for monthly_change in monthly_outputs:

                for (
                    month,
                    change_data
                ) in monthly_change.items():

                    if not isinstance(
                        change_data,
                        dict
                    ):
                        continue

                    if month not in combined_monthly_change:

                        combined_monthly_change[
                            month
                        ] = change_data

            sorted_months = sorted(
                combined_monthly_change.keys()
            )

            if sorted_months:

                latest_month = sorted_months[-1]

                latest = (
                    combined_monthly_change.get(
                        latest_month,
                        {}
                    )
                )

            # -------------------------------------------------
            # LATEST MONTH EVIDENCE
            # -------------------------------------------------

            if isinstance(latest, dict):

                direction = latest.get(
                    "direction"
                )

                change = latest.get(
                    "change_percentage",
                    0
                )

                previous_month = latest.get(
                    "previous_month"
                )

                current_revenue = latest.get(
                    "current_revenue",
                    0
                )

                previous_revenue = latest.get(
                    "previous_revenue",
                    0
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
                        "shows revenue growth rather "
                        "than a decline."
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
                        "requiring further investigation."
                    )

                else:

                    insights.append(
                        f"Revenue was stable in the "
                        f"latest observed month "
                        f"({latest_month}) compared "
                        f"with {previous_month}."
                    )

            # -------------------------------------------------
            # HISTORICAL MONTHLY EVIDENCE
            # -------------------------------------------------

            historical_declines = {}
            historical_increases = {}

            for (
                month,
                change_data
            ) in combined_monthly_change.items():

                direction = change_data.get(
                    "direction"
                )

                percentage = change_data.get(
                    "change_percentage",
                    0
                )

                if (
                    direction == "decrease"
                    and month != latest_month
                ):

                    historical_declines[
                        month
                    ] = percentage

                elif (
                    direction == "increase"
                    and month != latest_month
                ):

                    historical_increases[
                        month
                    ] = percentage

            # -------------------------------------------------
            # HISTORICAL DECLINES
            # -------------------------------------------------

            if historical_declines:

                decline_text = ", ".join(
                    f"{month} "
                    f"({abs(change):.2f}% decrease)"
                    for (
                        month,
                        change
                    ) in sorted(
                        historical_declines.items()
                    )
                )

                insights.append(
                    f"Historical month-over-month "
                    f"declines were observed in "
                    f"{decline_text}. These declines "
                    f"occurred before the latest observed "
                    f"month and should be analyzed "
                    f"separately from the latest movement."
                )

            # -------------------------------------------------
            # HISTORICAL INCREASES
            # -------------------------------------------------

            if historical_increases:

                increase_text = ", ".join(
                    f"{month} "
                    f"({abs(change):.2f}% increase)"
                    for (
                        month,
                        change
                    ) in sorted(
                        historical_increases.items()
                    )
                )

                insights.append(
                    f"Historical month-over-month "
                    f"increases were observed in "
                    f"{increase_text}."
                )

            # -------------------------------------------------
            # MONTHLY PRODUCT CONTRIBUTION
            # -------------------------------------------------

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

                latest_product_values = []

                for (
                    product_name,
                    product_data
                ) in product_analysis.items():

                    if not isinstance(
                        product_data,
                        dict
                    ):
                        continue

                    monthly_data = (
                        product_data.get(
                            "monthly_analysis"
                        )
                    )

                    if not isinstance(
                        monthly_data,
                        dict
                    ):
                        continue

                    if latest_month not in monthly_data:
                        continue

                    month_data = monthly_data.get(
                        latest_month,
                        {}
                    )

                    if not isinstance(
                        month_data,
                        dict
                    ):
                        continue

                    revenue = month_data.get(
                        "revenue",
                        0
                    )

                    latest_product_values.append(
                        (
                            product_name,
                            revenue
                        )
                    )

                if latest_product_values:

                    latest_product_values.sort(
                        key=lambda item: item[1],
                        reverse=True
                    )

                    top_product = (
                        latest_product_values[0]
                    )

                    insights.append(
                        f"In {latest_month}, "
                        f"{top_product[0]} contributed "
                        f"the highest recorded product "
                        f"revenue at "
                        f"{top_product[1]:,.2f}."
                    )

                    break

            # =================================================
            # EXTERNAL INVESTIGATION MERGE
            # =================================================

            if (
                web_search_found
                and external_sources
            ):

                source_count = len(
                    external_sources
                )

                # IMPORTANT:
                # Count sources, not evidence snippets.
                insights.append(
                    f"External research included "
                    f"{source_count} unique market-context "
                    f"source(s) for contextual analysis."
                )

                # -------------------------------------------------
                # INVESTIGATION EVIDENCE
                # -------------------------------------------------

                investigation_source_count = len(
                    investigation_external_sources
                )

                if (
                    investigation_source_count > 0
                ):

                    insights.append(
                        f"The investigation stage added "
                        f"{investigation_source_count} "
                        f"additional validated external "
                        f"source(s) to the evidence review."
                    )

                    insights.append(
                        "The external investigation supports "
                        "market-level context around factors "
                        "such as customer behavior, pricing, "
                        "competition, and broader business "
                        "conditions. These findings are "
                        "contextual and do not establish "
                        "company-specific causation."
                    )

                # -------------------------------------------------
                # CAUSALITY LIMITATION
                # -------------------------------------------------

                insights.append(
                    "External market factors may help explain "
                    "historical revenue movements, but the "
                    "available evidence does not establish "
                    "that these factors caused the observed "
                    "changes in this business."
                )

                investigation["required"] = True

                if not investigation["reason"]:

                    investigation["reason"] = (
                        "External market research is "
                        "available, but company-specific "
                        "evidence is required before "
                        "attributing observed revenue "
                        "changes to external factors."
                    )

                external_question = (
                    "Which external market factors, "
                    "if any, are supported by "
                    "business-specific evidence?"
                )

                if external_question not in (
                    investigation["questions"]
                ):

                    investigation["questions"].append(
                        external_question
                    )

            # -------------------------------------------------
            # MONTHLY RECOMMENDATIONS
            # -------------------------------------------------

            recommendations = [

                "Investigate the historical revenue "
                "declines at product and regional level "
                "before attributing them to external "
                "market conditions.",

                "Compare product and regional movement "
                "across the declining months and the "
                "latest month to identify the strongest "
                "internal drivers.",

                "Track monthly revenue, units sold, "
                "pricing, discounts, and relevant market "
                "signals together for earlier detection "
                "of future changes."
            ]

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

                # -------------------------------------------------
                # STRONGEST
                # -------------------------------------------------

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

                # -------------------------------------------------
                # WEAKEST
                # -------------------------------------------------

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

                    insights.extend([

                        f"{strongest_name} is the strongest "
                        f"product by recorded revenue at "
                        f"{strongest_revenue:,.2f}.",

                        f"{weakest_name} is the weakest "
                        f"product by recorded revenue at "
                        f"{weakest_revenue:,.2f}."
                    ])

                    break

        # =================================================
        # PRODUCT INVESTIGATION EVIDENCE
        # =================================================

        if (
            query_intent == "product"
            and product_performance_investigations
        ):

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

            is_why_query = any(
                keyword in request
                for keyword in why_keywords
            )

            if is_why_query:

                recommendations = []

            for investigation_data in (
                product_performance_investigations
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

                comparison = (
                    investigation_data.get(
                        "comparison",
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
                    not target_product
                    or not isinstance(
                        target_data,
                        dict
                    )
                ):
                    continue

                target_units = target_data.get(
                    "units_sold",
                    0
                )

                target_price = target_data.get(
                    "average_unit_price",
                    0
                )

                target_discount = target_data.get(
                    "average_discount",
                    0
                )

                target_revenue = target_data.get(
                    "revenue",
                    0
                )

                target_orders = target_data.get(
                    "orders",
                    0
                )

                insights.extend([

                    f"Investigation found that "
                    f"{target_product} generated "
                    f"{target_revenue:,.2f} in recorded "
                    f"revenue across {target_orders} orders "
                    f"and sold {target_units} units.",

                    f"{target_product} had an average unit "
                    f"price of {target_price:,.2f} and an "
                    f"average discount of "
                    f"{target_discount:.2f}%."
                ])

                if isinstance(
                    comparison,
                    dict
                ):

                    for (
                        comparison_product,
                        comparison_data
                    ) in comparison.items():

                        if (
                            comparison_product
                            == target_product
                        ):
                            continue

                        if not isinstance(
                            comparison_data,
                            dict
                        ):
                            continue

                        comparison_units = (
                            comparison_data.get(
                                "units_sold",
                                0
                            )
                        )

                        comparison_price = (
                            comparison_data.get(
                                "average_unit_price",
                                0
                            )
                        )

                        comparison_discount = (
                            comparison_data.get(
                                "average_discount",
                                0
                            )
                        )

                        unit_difference = (
                            target_units
                            - comparison_units
                        )

                        price_difference = (
                            target_price
                            - comparison_price
                        )

                        discount_difference = (
                            target_discount
                            - comparison_discount
                        )

                        insights.append(
                            f"Compared with "
                            f"{comparison_product}, "
                            f"{target_product} sold "
                            f"{unit_difference} more units, "
                            f"had an average unit price "
                            f"difference of "
                            f"{price_difference:,.2f}, "
                            f"and an average discount "
                            f"difference of "
                            f"{discount_difference:.2f} "
                            f"percentage points."
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

                        revenue_difference = (
                            difference_data.get(
                                "revenue_difference",
                                0
                            )
                        )

                        units_difference = (
                            difference_data.get(
                                "units_sold_difference",
                                0
                            )
                        )

                        price_difference = (
                            difference_data.get(
                                "average_unit_price_difference",
                                0
                            )
                        )

                        discount_difference = (
                            difference_data.get(
                                "average_discount_difference",
                                0
                            )
                        )

                        insights.append(
                            f"Against {comparison_product}, "
                            f"{target_product} had a "
                            f"{revenue_difference:,.2f} "
                            f"revenue advantage, "
                            f"{units_difference} more units "
                            f"sold, a "
                            f"{price_difference:,.2f} average "
                            f"price difference, and a "
                            f"{discount_difference:.2f} "
                            f"percentage-point discount "
                            f"difference."
                        )

                business_concern = (
                    f"{target_product}'s higher recorded "
                    f"revenue is associated with differences "
                    f"in unit volume, pricing, and discounts. "
                    f"The available evidence shows these "
                    f"factors occurring alongside the revenue "
                    f"difference, but it does not establish "
                    f"that any single factor caused the "
                    f"higher revenue."
                )

                recommendations.extend([

                    f"Prioritize analysis of "
                    f"{target_product}'s volume drivers "
                    f"because its {target_units} recorded "
                    f"units are a major observed "
                    f"differentiator.",

                    f"Compare {target_product}'s pricing "
                    f"and discount structure with the "
                    f"other products to determine whether "
                    f"the observed combination is "
                    f"sustainable.",

                    f"Break down {target_product}'s monthly "
                    f"and regional performance before "
                    f"attributing its revenue advantage "
                    f"to any single factor."
                ])

                break

        # =================================================
        # PRODUCT COMPARISON / HISTORICAL INVESTIGATION
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

                # -------------------------------------------------
                # PRODUCT COMPARISON
                # -------------------------------------------------

                if (
                    investigation_type
                    == "product_comparison"
                ):

                    product_1 = investigation_data.get(
                        "product_1"
                    )

                    product_2 = investigation_data.get(
                        "product_2"
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

                # -------------------------------------------------
                # PRODUCT HISTORICAL TREND
                # -------------------------------------------------

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

                        first_month = ordered_months[0]
                        last_month = ordered_months[-1]

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

                        decreases = {}

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

                                decreases[month] = (
                                    change_data.get(
                                        "change_percentage",
                                        0
                                    )
                                )

                        if decreases:

                            decrease_text = ", ".join(
                                f"{month} "
                                f"({abs(change):.2f}% decrease)"
                                for (
                                    month,
                                    change
                                ) in sorted(
                                    decreases.items()
                                )
                            )

                            insights.append(
                                f"{target_product} recorded "
                                f"month-over-month revenue "
                                f"decreases in "
                                f"{decrease_text}."
                            )

        # =================================================
        # EXTERNAL EVIDENCE FINAL HANDLING
        # =================================================

        if (
            web_search_found
            and external_sources
            and query_intent == "monthly"
        ):

            causality_gap = (
                "Business-specific external market causality"
            )

            if causality_gap not in evidence_gaps:

                evidence_gaps.append(
                    causality_gap
                )

            investigation["required"] = True

            if not investigation["reason"]:

                investigation["reason"] = (
                    "External market research is "
                    "available, but business-specific "
                    "evidence is required before "
                    "attributing revenue changes "
                    "to external factors."
                )

            external_question = (
                "Which external market factors, "
                "if any, are supported by "
                "business-specific evidence?"
            )

            if external_question not in (
                investigation["questions"]
            ):

                investigation["questions"].append(
                    external_question
                )

        # =================================================
        # FINAL CLEANUP
        # =================================================

        # -------------------------------------------------
        # UNIQUE INSIGHTS
        # -------------------------------------------------

        unique_insights = []

        seen_insight_keys = set()

        for insight in insights:

            if not insight:
                continue

            normalized = (
                " ".join(
                    str(insight)
                    .lower()
                    .split()
                )
            )

            if normalized in seen_insight_keys:
                continue

            seen_insight_keys.add(
                normalized
            )

            unique_insights.append(
                insight
            )

        insights = unique_insights

        # -------------------------------------------------
        # UNIQUE RECOMMENDATIONS
        # -------------------------------------------------

        unique_recommendations = []

        seen_recommendation_keys = set()

        for recommendation in recommendations:

            if not recommendation:
                continue

            normalized = (
                " ".join(
                    str(recommendation)
                    .lower()
                    .split()
                )
            )

            if normalized in seen_recommendation_keys:
                continue

            seen_recommendation_keys.add(
                normalized
            )

            unique_recommendations.append(
                recommendation
            )

        recommendations = (
            unique_recommendations[:3]
        )

        # -------------------------------------------------
        # UNIQUE EVIDENCE GAPS
        # -------------------------------------------------

        evidence_gaps = list(
            dict.fromkeys(
                evidence_gaps
            )
        )

        # -------------------------------------------------
        # UNIQUE INVESTIGATION QUESTIONS
        # -------------------------------------------------

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
                        
