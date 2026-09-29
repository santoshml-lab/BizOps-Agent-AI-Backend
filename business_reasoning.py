from typing import Any, Dict, List, Tuple


class BusinessReasoning:

    def __init__(self):
        pass

    # =========================================================
    # MAIN REASONING
    # =========================================================

    def reason(
        self,
        aggregated_result: Dict[str, Any],
        user_request: str = "",
    ) -> Dict[str, Any]:

        if not isinstance(aggregated_result, dict):
            return self._failed_result(
                "Aggregated result must be a dictionary."
            )

        user_request = str(user_request or "").strip()
        query_lower = user_request.lower()

        # =====================================================
        # QUERY INTENT
        # =====================================================

        product_intent = any(
            keyword in query_lower
            for keyword in [
                "product",
                "products",
                "item",
                "items",
                "sku",
            ]
        )

        region_intent = any(
            keyword in query_lower
            for keyword in [
                "region",
                "regional",
                "north",
                "south",
                "east",
                "west",
                "territory",
                "location",
            ]
        )

        monthly_intent = any(
            keyword in query_lower
            for keyword in [
                "month",
                "monthly",
                "sales dropped",
                "sales drop",
                "revenue dropped",
                "revenue drop",
                "this month",
                "last month",
                "latest month",
                "trend",
                "trends",
                "month over month",
                "historical",
                "historically",
                "past months",
            ]
        )

        why_intent = any(
            keyword in query_lower
            for keyword in [
                "why",
                "how",
                "factor",
                "factors",
                "reason",
                "reasons",
                "driver",
                "drivers",
                "outperform",
                "underperform",
                "caused",
                "cause",
            ]
        )

        # External research should only become visible when the
        # question actually asks for market/external context.
        external_intent = any(
            keyword in query_lower
            for keyword in [
                "market",
                "external",
                "industry",
                "competition",
                "competitor",
                "customer behavior",
                "consumer behavior",
                "economic",
                "industry trend",
                "market factor",
                "market factors",
            ]
        )

        # =====================================================
        # NORMALIZE ORIGINAL RESULTS
        # =====================================================

        original_results = aggregated_result.get(
            "results",
            aggregated_result.get(
                "execution_results",
                []
            )
        )

        if not isinstance(original_results, list):
            original_results = []

        original_results = self._normalize_results(
            original_results
        )

        # =====================================================
        # NORMALIZE INVESTIGATION RESULTS
        # =====================================================

        investigation_results = aggregated_result.get(
            "investigation_results",
            []
        )

        if not isinstance(investigation_results, list):
            investigation_results = []

        nested_investigation = aggregated_result.get(
            "investigation",
            {}
        )

        if isinstance(nested_investigation, dict):

            nested_results = nested_investigation.get(
                "results",
                []
            )

            if isinstance(nested_results, list):
                investigation_results.extend(
                    nested_results
                )

        investigation_results = self._normalize_results(
            investigation_results
        )

        # =====================================================
        # COMBINED RESULTS
        # =====================================================

        all_results = (
            original_results
            + investigation_results
        )

        # =====================================================
        # COLLECT DATA ANALYSIS OUTPUTS
        # =====================================================

        analysis_outputs = []

        for result in all_results:

            if not isinstance(result, dict):
                continue

            tool_name = str(
                result.get("tool", "")
            ).lower()

            output = result.get(
                "output",
                {}
            )

            if (
                tool_name == "data_analysis"
                and isinstance(output, dict)
                and output.get("status") == "success"
            ):
                analysis_outputs.append(output)

        # =====================================================
        # PRIMARY WEB SOURCES
        # =====================================================

        primary_external_sources = []
        primary_external_evidence = []
        primary_direct_evidence = []

        for result in original_results:

            if not isinstance(result, dict):
                continue

            tool_name = str(
                result.get("tool", "")
            ).lower()

            if tool_name != "web_search":
                continue

            output = result.get(
                "output",
                {}
            )

            sources, evidence, direct = (
                self._collect_web_sources(output)
            )

            primary_external_sources.extend(
                sources
            )

            primary_external_evidence.extend(
                evidence
            )

            primary_direct_evidence.extend(
                direct
            )

        primary_external_sources = (
            self._dedupe_sources(
                primary_external_sources
            )
        )

        primary_external_evidence = (
            self._dedupe_strings(
                primary_external_evidence
            )
        )

        primary_direct_evidence = (
            self._dedupe_strings(
                primary_direct_evidence
            )
        )

        # =====================================================
        # INVESTIGATION WEB SOURCES
        # =====================================================

        investigation_external_sources = []
        investigation_external_evidence = []
        investigation_direct_evidence = []

        for result in investigation_results:

            if not isinstance(result, dict):
                continue

            tool_name = str(
                result.get("tool", "")
            ).lower()

            if tool_name != "web_search":
                continue

            output = result.get(
                "output",
                {}
            )

            sources, evidence, direct = (
                self._collect_web_sources(output)
            )

            investigation_external_sources.extend(
                sources
            )

            investigation_external_evidence.extend(
                evidence
            )

            investigation_direct_evidence.extend(
                direct
            )

        investigation_external_sources = (
            self._dedupe_sources(
                investigation_external_sources
            )
        )

        investigation_external_evidence = (
            self._dedupe_strings(
                investigation_external_evidence
            )
        )

        investigation_direct_evidence = (
            self._dedupe_strings(
                investigation_direct_evidence
            )
        )

        # =====================================================
        # EXTERNAL EVIDENCE
        # =====================================================

        external_evidence = self._dedupe_strings(
            primary_external_evidence
            + primary_direct_evidence
            + investigation_external_evidence
            + investigation_direct_evidence
        )

        primary_web_search_found = bool(
            primary_external_sources
            or primary_external_evidence
            or primary_direct_evidence
        )

        investigation_web_search_found = bool(
            investigation_external_sources
            or investigation_external_evidence
            or investigation_direct_evidence
        )

        web_search_found = (
            primary_web_search_found
            or investigation_web_search_found
        )

        # =====================================================
        # DATA CONTAINERS
        # =====================================================

        product_analysis = {}
        region_analysis = {}
        monthly_analysis = {}
        monthly_change = {}

        strongest_product = None
        weakest_product = None

        for output in analysis_outputs:

            if not product_analysis:

                candidate = output.get(
                    "product_analysis",
                    {}
                )

                if isinstance(candidate, dict):
                    product_analysis = candidate

            if not region_analysis:

                candidate = output.get(
                    "region_analysis",
                    {}
                )

                if isinstance(candidate, dict):
                    region_analysis = candidate

            candidate_monthly = output.get(
                "monthly_analysis",
                {}
            )

            if isinstance(candidate_monthly, dict):

                for month, value in candidate_monthly.items():

                    if month not in monthly_analysis:
                        monthly_analysis[month] = value

            candidate_changes = output.get(
                "monthly_change",
                {}
            )

            if isinstance(candidate_changes, dict):

                for month, value in candidate_changes.items():

                    if month not in monthly_change:
                        monthly_change[month] = value

            if strongest_product is None:

                strongest_product = output.get(
                    "strongest_product"
                )

            if weakest_product is None:

                weakest_product = output.get(
                    "weakest_product"
                )

        # =====================================================
        # FALLBACK PRODUCT CALCULATION
        # =====================================================

        if not strongest_product and product_analysis:

            strongest_product = max(
                product_analysis.items(),
                key=lambda item: self._safe_number(
                    item[1].get("revenue", 0)
                    if isinstance(item[1], dict)
                    else 0
                )
            )[0]

        if not weakest_product and product_analysis:

            weakest_product = min(
                product_analysis.items(),
                key=lambda item: self._safe_number(
                    item[1].get("revenue", 0)
                    if isinstance(item[1], dict)
                    else 0
                )
            )[0]

        # =====================================================
        # RESULT CONTAINERS
        # =====================================================

        insights = []
        recommendations = []
        investigation_required = False
        investigation_questions = []

        # =====================================================
        # INVESTIGATION EVIDENCE EXTRACTION
        # =====================================================

        investigation_analysis_outputs = []

        for result in investigation_results:

            if not isinstance(result, dict):
                continue

            output = result.get(
                "output",
                {}
            )

            if not isinstance(output, dict):
                continue

            investigation = output.get(
                "investigation",
                {}
            )

            if isinstance(investigation, dict):

                investigation_analysis_outputs.append(
                    investigation
                )

        valid_investigation_evidence = bool(
            investigation_analysis_outputs
        )

        completed_investigation_types = set()

        for investigation in investigation_analysis_outputs:

            investigation_type = str(
                investigation.get(
                    "type",
                    ""
                )
            ).lower().strip()

            if investigation_type:
                completed_investigation_types.add(
                    investigation_type
                )

        # =====================================================
        # INVESTIGATION COMPLETION
        # =====================================================

        successful_investigation_results = []

        for result in investigation_results:

            if not isinstance(result, dict):
                continue

            result_status = str(
                result.get(
                    "status",
                    ""
                )
            ).lower().strip()

            output = result.get(
                "output",
                {}
            )

            output_status = ""

            if isinstance(output, dict):

                output_status = str(
                    output.get(
                        "status",
                        ""
                    )
                ).lower().strip()

            if (
                result_status in {
                    "success",
                    "passed"
                }
                or output_status in {
                    "success",
                    "passed"
                }
            ):

                successful_investigation_results.append(
                    result
                )

        investigation_completed = bool(
            valid_investigation_evidence
            or (
                investigation_results
                and len(
                    successful_investigation_results
                )
                == len(
                    investigation_results
                )
            )
        )

        # =====================================================
        # EVIDENCE GAPS
        # =====================================================

        evidence_gaps = []

        if not analysis_outputs:

            evidence_gaps.append(
                "No successful business data analysis was available."
            )

        # =====================================================
        # EXTERNAL MARKET CONTEXT
        # IMPORTANT:
        # Only show this when query actually asks for it.
        # =====================================================

        if external_intent and primary_web_search_found:

            primary_count = len(
                primary_external_sources
            )

            context_themes = (
                self._extract_market_themes(
                    primary_external_evidence
                )
            )

            if context_themes:

                theme_text = ", ".join(
                    context_themes
                )

                insights.append(
                    f"External market research included "
                    f"{primary_count} validated source(s) "
                    f"covering themes such as {theme_text}. "
                    f"These sources provide market context "
                    f"rather than proof of company-specific "
                    f"causation."
                )

            else:

                insights.append(
                    f"External market research included "
                    f"{primary_count} validated source(s). "
                    f"These sources provide market context "
                    f"rather than proof of company-specific "
                    f"causation."
                )

        # =====================================================
        # MONTHLY REASONING
        # IMPORTANT:
        # Only run for monthly/trend questions.
        # =====================================================

        if monthly_intent and (
            monthly_analysis
            or monthly_change
        ):

            combined_monthly_change = {}

            for month, change in monthly_change.items():

                if not isinstance(change, dict):
                    continue

                combined_monthly_change[
                    str(month)
                ] = change

            sorted_months = sorted(
                combined_monthly_change.keys()
            )

            latest_month = (
                sorted_months[-1]
                if sorted_months
                else None
            )

            latest_change = (
                combined_monthly_change.get(
                    latest_month,
                    {}
                )
                if latest_month
                else {}
            )

            if isinstance(latest_change, dict):

                current_revenue = self._safe_number(
                    latest_change.get(
                        "current_revenue",
                        0
                    )
                )

                previous_revenue = self._safe_number(
                    latest_change.get(
                        "previous_revenue",
                        0
                    )
                )

                percentage = self._safe_number(
                    latest_change.get(
                        "change_percentage",
                        0
                    )
                )

                direction = str(
                    latest_change.get(
                        "direction",
                        ""
                    )
                ).lower()

                previous_month = (
                    latest_change.get(
                        "previous_month",
                        ""
                    )
                )

                if direction == "increase":

                    insights.append(
                        f"Revenue increased in the latest "
                        f"observed month ({latest_month}) "
                        f"from {previous_revenue:,.2f} in "
                        f"{previous_month} to "
                        f"{current_revenue:,.2f}, a "
                        f"{abs(percentage):.2f}% increase."
                    )

                elif direction == "decrease":

                    insights.append(
                        f"Revenue decreased in the latest "
                        f"observed month ({latest_month}) "
                        f"from {previous_revenue:,.2f} in "
                        f"{previous_month} to "
                        f"{current_revenue:,.2f}, a "
                        f"{abs(percentage):.2f}% decrease."
                    )

            # -------------------------------------------------
            # HISTORICAL DECLINES
            # -------------------------------------------------

            historical_declines = []

            for month in sorted_months:

                if month == latest_month:
                    continue

                change = combined_monthly_change.get(
                    month,
                    {}
                )

                if not isinstance(change, dict):
                    continue

                direction = str(
                    change.get(
                        "direction",
                        ""
                    )
                ).lower()

                percentage = self._safe_number(
                    change.get(
                        "change_percentage",
                        0
                    )
                )

                if direction == "decrease":

                    historical_declines.append(
                        (
                            month,
                            abs(percentage)
                        )
                    )

            if historical_declines:

                decline_text = ", ".join(
                    f"{month} ({percentage:.2f}% decrease)"
                    for month, percentage
                    in historical_declines
                )

                insights.append(
                    "Historical month-over-month declines "
                    f"were observed in {decline_text}. "
                    "These declines occurred before the "
                    "latest observed month and should be "
                    "analyzed separately from the latest "
                    "movement."
                )

            # -------------------------------------------------
            # HISTORICAL INCREASES
            # -------------------------------------------------

            historical_increases = []

            for month in sorted_months:

                if month == latest_month:
                    continue

                change = combined_monthly_change.get(
                    month,
                    {}
                )

                if not isinstance(change, dict):
                    continue

                direction = str(
                    change.get(
                        "direction",
                        ""
                    )
                ).lower()

                percentage = self._safe_number(
                    change.get(
                        "change_percentage",
                        0
                    )
                )

                if direction == "increase":

                    historical_increases.append(
                        (
                            month,
                            percentage
                        )
                    )

            if historical_increases:

                increase_text = ", ".join(
                    f"{month} ({percentage:.2f}% increase)"
                    for month, percentage
                    in historical_increases
                )

                insights.append(
                    "Historical month-over-month increases "
                    f"were observed in {increase_text}."
                )

            # -------------------------------------------------
            # LATEST MONTH PRODUCT
            # -------------------------------------------------

            if monthly_analysis:

                latest_month_data = (
                    monthly_analysis.get(
                        latest_month,
                        {}
                    )
                )

                if isinstance(
                    latest_month_data,
                    dict
                ):

                    products = (
                        latest_month_data.get(
                            "products",
                            {}
                        )
                    )

                    if (
                        isinstance(products, dict)
                        and products
                    ):

                        product_revenues = []

                        for product_name, data in products.items():

                            if not isinstance(
                                data,
                                dict
                            ):
                                continue

                            revenue = self._safe_number(
                                data.get(
                                    "revenue",
                                    0
                                )
                            )

                            product_revenues.append(
                                (
                                    product_name,
                                    revenue
                                )
                            )

                        if product_revenues:

                            product_revenues.sort(
                                key=lambda item: item[1],
                                reverse=True
                            )

                            top_product = (
                                product_revenues[0]
                            )

                            insights.append(
                                f"In {latest_month}, "
                                f"{top_product[0]} generated "
                                f"the highest product revenue "
                                f"at {top_product[1]:,.2f}."
                            )

            # -------------------------------------------------
            # MONTHLY RECOMMENDATIONS
            # -------------------------------------------------

            if historical_declines:

                recommendations.extend([
                    "Investigate the historical revenue declines at product and regional level before attributing them to external market conditions.",
                    "Compare product and regional movement across the declining months and the latest month to identify the strongest internal drivers.",
                    "Track monthly revenue, units sold, pricing, discounts, and relevant market signals together for earlier detection of future changes.",
                ])

            else:

                recommendations.extend([
                    "Monitor the latest revenue movement at product and regional level.",
                    "Track units sold, pricing, and discounts alongside monthly revenue.",
                    "Combine internal sales metrics with relevant external market indicators.",
                ])

        # =====================================================
        # PRODUCT REASONING
        # IMPORTANT:
        # Product queries should stay product-focused.
        # =====================================================

        if product_analysis and (
            product_intent
            or strongest_product
        ):

            strongest_name = (
                self._resolve_product_name(
                    strongest_product,
                    product_analysis
                )
            )

            weakest_name = (
                self._resolve_product_name(
                    weakest_product,
                    product_analysis
                )
            )

            strongest_data = (
                product_analysis.get(
                    strongest_name,
                    {}
                )
                if strongest_name
                else {}
            )

            weakest_data = (
                product_analysis.get(
                    weakest_name,
                    {}
                )
                if weakest_name
                else {}
            )

            # -------------------------------------------------
            # STRONGEST PRODUCT
            # -------------------------------------------------

            if (
                strongest_name
                and isinstance(
                    strongest_data,
                    dict
                )
            ):

                strongest_revenue = (
                    self._safe_number(
                        strongest_data.get(
                            "revenue",
                            0
                        )
                    )
                )

                insights.append(
                    f"{strongest_name} is the strongest "
                    f"product by total revenue at "
                    f"{strongest_revenue:,.2f}."
                )

            # -------------------------------------------------
            # PRODUCT COMPARISON
            # -------------------------------------------------

            if (
                strongest_name
                and weakest_name
                and strongest_name != weakest_name
                and isinstance(
                    strongest_data,
                    dict
                )
                and isinstance(
                    weakest_data,
                    dict
                )
            ):

                strongest_units = (
                    self._safe_number(
                        strongest_data.get(
                            "units_sold",
                            0
                        )
                    )
                )

                weakest_units = (
                    self._safe_number(
                        weakest_data.get(
                            "units_sold",
                            0
                        )
                    )
                )

                strongest_price = (
                    self._safe_number(
                        strongest_data.get(
                            "average_unit_price",
                            0
                        )
                    )
                )

                weakest_price = (
                    self._safe_number(
                        weakest_data.get(
                            "average_unit_price",
                            0
                        )
                    )
                )

                strongest_discount = (
                    self._safe_number(
                        strongest_data.get(
                            "average_discount",
                            0
                        )
                    )
                )

                weakest_discount = (
                    self._safe_number(
                        weakest_data.get(
                            "average_discount",
                            0
                        )
                    )
                )

                insights.append(
                    f"{strongest_name} versus "
                    f"{weakest_name}: {strongest_name} "
                    f"has {strongest_units:,.0f} units sold "
                    f"at an average unit price of "
                    f"{strongest_price:,.2f} with an average "
                    f"discount of {strongest_discount:.2f}%, "
                    f"while {weakest_name} has "
                    f"{weakest_units:,.0f} units sold at "
                    f"{weakest_price:,.2f} with an average "
                    f"discount of {weakest_discount:.2f}%."
                )

            # -------------------------------------------------
            # WHY PRODUCT INVESTIGATION
            # -------------------------------------------------

            if why_intent and strongest_name:

                investigation_required = True

                investigation_questions.extend([
                    f"Why does {strongest_name} generate more revenue based on units, pricing, and discounts?",
                    f"Is the advantage of {strongest_name} consistent across months?",
                    f"What factors are associated with {strongest_name} having higher revenue?",
                ])

            # -------------------------------------------------
            # PRODUCT RECOMMENDATIONS
            # -------------------------------------------------

            if why_intent and strongest_name:

                recommendations.extend([
                    f"Review {strongest_name}'s unit volume, pricing, and discount profile to identify the main revenue drivers.",
                    f"Compare {strongest_name}'s monthly performance with other products to determine whether its revenue advantage is consistent.",
                    "Use product-level pricing, volume, and discount signals together when planning future product decisions.",
                ])

            elif weakest_name:

                recommendations.extend([
                    f"Investigate {weakest_name}'s unit volume, pricing, and discount pattern against stronger products.",
                    f"Review the monthly performance of {weakest_name} to determine whether the weakness is persistent or recent.",
                    "Test product-level pricing, promotion, and demand signals before changing the broader product strategy.",
                ])

        # =====================================================
        # REGION REASONING
        # IMPORTANT:
        # Only execute for region-focused questions.
        # =====================================================

        if (
            region_intent
            and region_analysis
        ):

            region_revenues = []

            for region_name, data in region_analysis.items():

                if not isinstance(data, dict):
                    continue

                revenue = self._safe_number(
                    data.get(
                        "revenue",
                        0
                    )
                )

                region_revenues.append(
                    (
                        region_name,
                        revenue
                    )
                )

            if region_revenues:

                region_revenues.sort(
                    key=lambda item: item[1],
                    reverse=True
                )

                strongest_region = (
                    region_revenues[0]
                )

                weakest_region = (
                    region_revenues[-1]
                )

                insights.append(
                    f"{strongest_region[0]} is the strongest "
                    f"region by revenue at "
                    f"{strongest_region[1]:,.2f}."
                )

                insights.append(
                    f"{weakest_region[0]} is the weakest "
                    f"region by revenue at "
                    f"{weakest_region[1]:,.2f}."
                )

                if why_intent:

                    investigation_required = True

                    investigation_questions.extend([
                        f"Which products contribute most to {weakest_region[0]}'s revenue?",
                        f"How has {weakest_region[0]}'s revenue changed historically?",
                    ])

                    recommendations.extend([
                        f"Investigate product contribution within {weakest_region[0]}.",
                        f"Compare {weakest_region[0]}'s monthly trend against other regions.",
                        "Track regional product mix together with units, pricing, and discounts.",
                    ])

        # =====================================================
        # PRODUCT INVESTIGATION EVIDENCE
        # =====================================================

        for investigation in investigation_analysis_outputs:

            investigation_type = str(
                investigation.get(
                    "type",
                    ""
                )
            ).lower()

            if investigation_type != "product_performance":
                continue

            target_product = investigation.get(
                "target_product"
            )

            target_data = investigation.get(
                "target_product_data",
                {}
            )

            differences = investigation.get(
                "differences",
                {}
            )

            if target_product:

                if isinstance(
                    target_data,
                    dict
                ):

                    revenue = self._safe_number(
                        target_data.get(
                            "revenue",
                            0
                        )
                    )

                    units = self._safe_number(
                        target_data.get(
                            "units_sold",
                            0
                        )
                    )

                    price = self._safe_number(
                        target_data.get(
                            "average_unit_price",
                            0
                        )
                    )

                    discount = self._safe_number(
                        target_data.get(
                            "average_discount",
                            0
                        )
                    )

                    insights.append(
                        f"Investigation evidence shows "
                        f"{target_product} has "
                        f"{units:,.0f} units sold, "
                        f"{revenue:,.2f} total revenue, "
                        f"an average unit price of "
                        f"{price:,.2f}, and an average "
                        f"discount of {discount:.2f}%."
                    )

                # -------------------------------------------------
                # DIFFERENCE ANALYSIS
                # -------------------------------------------------

                if isinstance(
                    differences,
                    dict
                ):

                    for competitor, values in differences.items():

                        if not isinstance(
                            values,
                            dict
                        ):
                            continue

                        revenue_difference = (
                            self._safe_number(
                                values.get(
                                    "revenue_difference",
                                    0
                                )
                            )
                        )

                        units_difference = (
                            self._safe_number(
                                values.get(
                                    "units_sold_difference",
                                    0
                                )
                            )
                        )

                        price_difference = (
                            self._safe_number(
                                values.get(
                                    "average_unit_price_difference",
                                    0
                                )
                            )
                        )

                        discount_difference = (
                            self._safe_number(
                                values.get(
                                    "average_discount_difference",
                                    0
                                )
                            )
                        )

                        insights.append(
                            f"{target_product} versus "
                            f"{competitor}: revenue difference "
                            f"{revenue_difference:,.2f}, units "
                            f"difference {units_difference:,.0f}, "
                            f"average price difference "
                            f"{price_difference:,.2f}, and average "
                            f"discount difference "
                            f"{discount_difference:.2f} percentage "
                            f"points."
                        )

        # =====================================================
        # PRODUCT HISTORICAL / CONSISTENCY EVIDENCE
        # =====================================================

        for investigation in investigation_analysis_outputs:

            investigation_type = str(
                investigation.get(
                    "type",
                    ""
                )
            ).lower()

            if investigation_type not in (
                "product_historical",
                "product_mix",
                "historical_trend",
                "data_request",
            ):
                continue

            # Historical evidence should only affect a product
            # query when the question actually asks "why/how".
            if not (
                product_intent
                and why_intent
            ):
                continue

            target_product = investigation.get(
                "target_product"
            )

            if not target_product:

                analysis_scope = investigation.get(
                    "analysis_scope",
                    {}
                )

                if isinstance(
                    analysis_scope,
                    dict
                ):

                    target_product = (
                        analysis_scope.get(
                            "product"
                        )
                    )

            if target_product:

                product_monthly = []

                for month in sorted(
                    monthly_analysis.keys()
                ):

                    month_data = (
                        monthly_analysis.get(
                            month,
                            {}
                        )
                    )

                    if not isinstance(
                        month_data,
                        dict
                    ):
                        continue

                    products = (
                        month_data.get(
                            "products",
                            {}
                        )
                    )

                    if not isinstance(
                        products,
                        dict
                    ):
                        continue

                    product_data = (
                        products.get(
                            target_product
                        )
                    )

                    if not isinstance(
                        product_data,
                        dict
                    ):
                        continue

                    revenue = self._safe_number(
                        product_data.get(
                            "revenue",
                            0
                        )
                    )

                    product_monthly.append(
                        (
                            month,
                            revenue
                        )
                    )

                if len(product_monthly) >= 2:

                    increasing = True

                    for index in range(
                        1,
                        len(product_monthly)
                    ):

                        if (
                            product_monthly[index][1]
                            <
                            product_monthly[index - 1][1]
                        ):

                            increasing = False
                            break

                    first_month = product_monthly[0]
                    last_month = product_monthly[-1]

                    if increasing:

                        insights.append(
                            f"Across the available monthly "
                            f"data, {target_product}'s revenue "
                            f"increased from "
                            f"{first_month[1]:,.2f} in "
                            f"{first_month[0]} to "
                            f"{last_month[1]:,.2f} in "
                            f"{last_month[0]}, with no observed "
                            f"month-over-month decline in the "
                            f"available product-level series."
                        )

                    else:

                        insights.append(
                            f"{target_product}'s monthly revenue "
                            f"was not consistently increasing "
                            f"across the available periods, so "
                            f"its performance should be evaluated "
                            f"month by month."
                        )

            historical_monthly = investigation.get(
                "monthly_analysis",
                {}
            )

            if isinstance(
                historical_monthly,
                dict
            ) and historical_monthly:

                historical_revenues = []

                for month, data in historical_monthly.items():

                    if not isinstance(
                        data,
                        dict
                    ):
                        continue

                    revenue = self._safe_number(
                        data.get(
                            "revenue",
                            0
                        )
                    )

                    historical_revenues.append(
                        (
                            str(month),
                            revenue
                        )
                    )

                historical_revenues.sort(
                    key=lambda item: item[0]
                )

                if len(historical_revenues) >= 2:

                    first = historical_revenues[0]
                    last = historical_revenues[-1]

                    insights.append(
                        f"Historical investigation shows "
                        f"revenue moving from "
                        f"{first[1]:,.2f} in {first[0]} "
                        f"to {last[1]:,.2f} in {last[0]} "
                        f"across the available periods."
                    )

        # =====================================================
        # REGION INVESTIGATION EVIDENCE
        # =====================================================

        for investigation in investigation_analysis_outputs:

            investigation_type = str(
                investigation.get(
                    "type",
                    ""
                )
            ).lower()

            if not region_intent:
                continue

            if investigation_type == (
                "regional_product_contribution"
            ):

                target_region = (
                    investigation.get(
                        "target_region"
                    )
                    or
                    investigation.get(
                        "region"
                    )
                )

                contribution = (
                    investigation.get(
                        "product_contribution"
                    )
                    or
                    investigation.get(
                        "product_analysis"
                    )
                )

                if target_region:

                    if (
                        isinstance(
                            contribution,
                            dict
                        )
                        and contribution
                    ):

                        contribution_items = []

                        for product_name, value in (
                            contribution.items()
                        ):

                            if isinstance(
                                value,
                                dict
                            ):

                                revenue = (
                                    self._safe_number(
                                        value.get(
                                            "revenue",
                                            0
                                        )
                                    )
                                )

                            else:

                                revenue = (
                                    self._safe_number(
                                        value
                                    )
                                )

                            contribution_items.append(
                                (
                                    product_name,
                                    revenue
                                )
                            )

                        contribution_items.sort(
                            key=lambda item: item[1],
                            reverse=True
                        )

                        if contribution_items:

                            top_product = (
                                contribution_items[0]
                            )

                            insights.append(
                                f"Investigation evidence for "
                                f"{target_region} shows "
                                f"{top_product[0]} as the largest "
                                f"product revenue contributor at "
                                f"{top_product[1]:,.2f}."
                            )

            elif investigation_type in (
                "regional_historical_trend",
                "historical_trend",
            ):

                target_region = (
                    investigation.get(
                        "target_region"
                    )
                    or
                    investigation.get(
                        "region"
                    )
                )

                historical_monthly = (
                    investigation.get(
                        "monthly_analysis",
                        {}
                    )
                )

                if (
                    target_region
                    and isinstance(
                        historical_monthly,
                        dict
                    )
                    and historical_monthly
                ):

                    historical_revenues = []

                    for month, data in (
                        historical_monthly.items()
                    ):

                        if not isinstance(
                            data,
                            dict
                        ):
                            continue

                        revenue = (
                            self._safe_number(
                                data.get(
                                    "revenue",
                                    0
                                )
                            )
                        )

                        historical_revenues.append(
                            (
                                str(month),
                                revenue
                            )
                        )

                    historical_revenues.sort(
                        key=lambda item: item[0]
                    )

                    if len(
                        historical_revenues
                    ) >= 2:

                        first = (
                            historical_revenues[0]
                        )

                        last = (
                            historical_revenues[-1]
                        )

                        insights.append(
                            f"Historical evidence for "
                            f"{target_region} shows revenue "
                            f"moving from "
                            f"{first[1]:,.2f} in {first[0]} "
                            f"to {last[1]:,.2f} in "
                            f"{last[0]}."
                        )

        # =====================================================
        # EXTERNAL INVESTIGATION EVIDENCE
        # Only visible when external context was requested.
        # =====================================================

        if (
            external_intent
            and investigation_external_sources
        ):

            investigation_count = len(
                investigation_external_sources
            )

            themes = (
                self._extract_market_themes(
                    investigation_external_evidence
                )
            )

            if themes:

                theme_text = ", ".join(
                    themes
                )

                insights.append(
                    "Investigation-stage external research "
                    f"validated {investigation_count} source(s) "
                    f"and reinforced market themes around "
                    f"{theme_text}. The evidence is contextual "
                    "and does not establish direct causation "
                    "for this business."
                )

            else:

                insights.append(
                    "Investigation-stage external research "
                    f"validated {investigation_count} source(s) "
                    "for additional market context."
                )

        # =====================================================
        # CAUSALITY LIMITATION
        # Only when external evidence is relevant.
        # =====================================================

        if (
            external_intent
            and web_search_found
        ):

            insights.append(
                "External market factors may help explain "
                "business movements, but the available evidence "
                "does not establish that these factors caused "
                "the observed changes in this business."
            )

        # =====================================================
        # GENERAL BUSINESS REASONING
        # =====================================================

        if (
            not monthly_analysis
            and not product_analysis
            and not region_analysis
        ):

            if analysis_outputs:

                insights.append(
                    "Business analysis was completed using "
                    "the available validated data."
                )

            else:

                insights.append(
                    "Insufficient internal business data was "
                    "available to generate detailed business reasoning."
                )

        # =====================================================
        # FINAL INVESTIGATION STATUS
        # =====================================================

        if investigation_completed:
            investigation_required = False

        investigation_pending = (
            investigation_required
            and not investigation_completed
        )

        if investigation_pending:

            evidence_gaps.append(
                "Additional investigation is required "
                "to support the requested explanation."
            )

        # =====================================================
        # DEDUPLICATE
        # =====================================================

        insights = self._dedupe_strings(
            insights
        )

        recommendations = self._dedupe_strings(
            recommendations
        )

        # Maximum 3 recommendations
        recommendations = (
            recommendations[:3]
        )

        # =====================================================
        # EXTERNAL SOURCE VISIBILITY
        #
        # For internal product/region questions, do not show
        # unrelated external sources even if planner executed
        # a web-search task.
        # =====================================================

        if external_intent:

            external_sources = (
                primary_external_sources
            )

        else:

            external_sources = []

        primary_source_count = len(
            external_sources
        )

        investigation_source_count = (
            len(
                investigation_external_sources
            )
            if external_intent
            else 0
        )

       
                        
