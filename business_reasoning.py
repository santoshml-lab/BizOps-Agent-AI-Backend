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

        # -----------------------------------------------------
        # Normalize original execution results
        # -----------------------------------------------------

        original_results = aggregated_result.get(
            "results",
            aggregated_result.get(
                "execution_results",
                []
            )
        )

        if not isinstance(original_results, list):
            original_results = []

        # -----------------------------------------------------
        # Normalize investigation results
        # -----------------------------------------------------

        investigation_results = aggregated_result.get(
            "investigation_results",
            []
        )

        if not isinstance(investigation_results, list):
            investigation_results = []

        # Some orchestrator versions may store investigation
        # results inside nested original_results.
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

        # -----------------------------------------------------
        # Normalize nested original results
        # -----------------------------------------------------

        normalized_original_results = []

        for result in original_results:

            if not isinstance(result, dict):
                continue

            normalized_original_results.append(result)

            nested = result.get(
                "original_results",
                []
            )

            if isinstance(nested, list):

                for nested_result in nested:

                    if isinstance(nested_result, dict):
                        normalized_original_results.append(
                            nested_result
                        )

        original_results = normalized_original_results

        # -----------------------------------------------------
        # Normalize investigation result nesting
        # -----------------------------------------------------

        normalized_investigation_results = []

        for result in investigation_results:

            if not isinstance(result, dict):
                continue

            normalized_investigation_results.append(
                result
            )

            nested = result.get(
                "original_results",
                []
            )

            if isinstance(nested, list):

                for nested_result in nested:

                    if isinstance(nested_result, dict):
                        normalized_investigation_results.append(
                            nested_result
                        )

        investigation_results = (
            normalized_investigation_results
        )

        # -----------------------------------------------------
        # Combined results for reasoning
        # -----------------------------------------------------

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
        # COMBINED EXTERNAL EVIDENCE
        # =====================================================

        external_evidence = self._dedupe_strings(
            primary_external_evidence
            + primary_direct_evidence
            + investigation_external_evidence
            + investigation_direct_evidence
        )

        # =====================================================
        # BASIC FLAGS
        # =====================================================

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
        # QUERY INTENT
        # =====================================================

        query_lower = user_request.lower()

        product_intent = any(
            keyword in query_lower
            for keyword in [
                "product",
                "products",
                "item",
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
                "trend",
                "trends",
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

        if (
            not strongest_product
            and product_analysis
        ):

            strongest_product = max(
                product_analysis.items(),
                key=lambda item: self._safe_number(
                    item[1].get("revenue", 0)
                    if isinstance(item[1], dict)
                    else 0
                )
            )[0]

        if (
            not weakest_product
            and product_analysis
        ):

            weakest_product = min(
                product_analysis.items(),
                key=lambda item: self._safe_number(
                    item[1].get("revenue", 0)
                    if isinstance(item[1], dict)
                    else 0
                )
            )[0]

        # =====================================================
        # VALIDATION
        # =====================================================

        evidence_gaps = []

        if not analysis_outputs:
            evidence_gaps.append(
                "No successful business data analysis was available."
            )

        if (
            why_intent
            and web_search_found
            and not investigation_results
        ):
            evidence_gaps.append(
                "External evidence exists, but business-specific "
                "investigation evidence is not available."
            )

        # =====================================================
        # RESULT CONTAINERS
        # =====================================================

        insights: List[str] = []
        recommendations: List[str] = []

        investigation_required = False
        investigation_questions = []

        # =====================================================
        # EXTERNAL MARKET CONTEXT
        # =====================================================

        if primary_web_search_found:

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
                    f"Primary external market research included "
                    f"{primary_count} validated source(s) covering "
                    f"themes such as {theme_text}. These sources "
                    f"provide market context rather than proof of "
                    f"company-specific causation."
                )

            else:

                insights.append(
                    f"Primary external market research included "
                    f"{primary_count} validated source(s). These "
                    f"sources provide market context rather than "
                    f"proof of company-specific causation."
                )

        # =====================================================
        # MONTHLY REASONING
        # =====================================================

        if monthly_analysis or monthly_change:

            # -------------------------------------------------
            # Deduplicate monthly changes by month
            # -------------------------------------------------

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

            # -------------------------------------------------
            # Latest movement
            # -------------------------------------------------

            if isinstance(
                latest_change,
                dict
            ):

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

                previous_month = latest_change.get(
                    "previous_month",
                    ""
                )

                if direction == "increase":

                    insights.append(
                        f"Revenue increased in the latest "
                        f"observed month ({latest_month}) from "
                        f"{previous_revenue:,.2f} in "
                        f"{previous_month} to "
                        f"{current_revenue:,.2f}, a "
                        f"{abs(percentage):.2f}% increase."
                    )

                elif direction == "decrease":

                    insights.append(
                        f"Revenue decreased in the latest "
                        f"observed month ({latest_month}) from "
                        f"{previous_revenue:,.2f} in "
                        f"{previous_month} to "
                        f"{current_revenue:,.2f}, a "
                        f"{abs(percentage):.2f}% decrease."
                    )

            # -------------------------------------------------
            # Historical declines
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
                    f"were observed in {decline_text}. These "
                    "declines occurred before the latest observed "
                    "month and should be analyzed separately from "
                    "the latest movement."
                )

            # -------------------------------------------------
            # Historical increases
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
            # Monthly product contribution
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

                    products = latest_month_data.get(
                        "products",
                        {}
                    )

                    if isinstance(
                        products,
                        dict
                    ) and products:

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
            # Monthly investigation requirement
            # -------------------------------------------------

            if (
                why_intent
                and primary_web_search_found
                and not investigation_results
            ):

                investigation_required = True

                investigation_questions.append(
                    "Which external market factors, if any, "
                    "are supported by business-specific evidence?"
                )

            # -------------------------------------------------
            # Investigation-stage evidence
            # -------------------------------------------------

            if investigation_external_sources:

                investigation_count = len(
                    investigation_external_sources
                )

                investigation_themes = (
                    self._extract_market_themes(
                        investigation_external_evidence
                    )
                )

                if investigation_themes:

                    theme_text = ", ".join(
                        investigation_themes
                    )

                    insights.append(
                        "Investigation-stage market research "
                        f"cross-checked the external context using "
                        f"{investigation_count} additional validated "
                        f"source(s), reinforcing themes around "
                        f"{theme_text}. This strengthens contextual "
                        "evidence but does not establish that these "
                        "factors caused the company's revenue movement."
                    )

                else:

                    insights.append(
                        "Investigation-stage market research "
                        f"added {investigation_count} additional "
                        "validated source(s) for cross-checking "
                        "external market context. These sources do "
                        "not establish company-specific causation."
                    )

            # -------------------------------------------------
            # Monthly recommendations
            # -------------------------------------------------

            if historical_declines:

                recommendations.extend(
                    [
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
                        "of future changes.",
                    ]
                )

            else:

                recommendations.extend(
                    [
                        "Monitor the latest revenue movement "
                        "at product and regional level.",

                        "Track units sold, pricing, and discounts "
                        "alongside monthly revenue.",

                        "Combine internal sales metrics with "
                        "relevant external market indicators."
                    ]
                )

        # =====================================================
        # PRODUCT REASONING
        # =====================================================

        if (
            product_analysis
            and (
                product_intent
                or strongest_product
                or weakest_product
            )
        ):

            strongest_name = self._resolve_product_name(
                strongest_product,
                product_analysis
            )

            weakest_name = self._resolve_product_name(
                weakest_product,
                product_analysis
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

            if (
                strongest_name
                and isinstance(
                    strongest_data,
                    dict
                )
            ):

                strongest_revenue = self._safe_number(
                    strongest_data.get(
                        "revenue",
                        0
                    )
                )

                insights.append(
                    f"{strongest_name} is the strongest "
                    f"product by total revenue at "
                    f"{strongest_revenue:,.2f}."
                )

            if (
                weakest_name
                and isinstance(
                    weakest_data,
                    dict
                )
            ):

                weakest_revenue = self._safe_number(
                    weakest_data.get(
                        "revenue",
                        0
                    )
                )

                insights.append(
                    f"{weakest_name} is the weakest "
                    f"product by total revenue at "
                    f"{weakest_revenue:,.2f}."
                )

            # -------------------------------------------------
            # Product comparison
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

                strongest_units = self._safe_number(
                    strongest_data.get(
                        "units_sold",
                        0
                    )
                )

                weakest_units = self._safe_number(
                    weakest_data.get(
                        "units_sold",
                        0
                    )
                )

                strongest_price = self._safe_number(
                    strongest_data.get(
                        "average_unit_price",
                        0
                    )
                )

                weakest_price = self._safe_number(
                    weakest_data.get(
                        "average_unit_price",
                        0
                    )
                )

                strongest_discount = self._safe_number(
                    strongest_data.get(
                        "average_discount",
                        0
                    )
                )

                weakest_discount = self._safe_number(
                    weakest_data.get(
                        "average_discount",
                        0
                    )
                )

                if (
                    strongest_name
                    and weakest_name
                ):

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
            # Product WHY investigation
            # -------------------------------------------------

            if why_intent:

                investigation_required = True

                investigation_questions.extend(
                    [
                        (
                            f"Why does {strongest_name or 'the strongest product'} "
                            "generate more revenue based on units, "
                            "pricing, and discounts?"
                        ),
                        (
                            f"Is the advantage of "
                            f"{strongest_name or 'the strongest product'} "
                            "consistent across months?"
                        ),
                        (
                            f"What factors are associated with "
                            f"{strongest_name or 'the strongest product'} "
                            "having higher revenue?"
                        ),
                    ]
                )

            # -------------------------------------------------
            # Product recommendations
            # -------------------------------------------------

            if weakest_name:

                recommendations.extend(
                    [
                        (
                            f"Investigate {weakest_name}'s unit "
                            "volume, pricing, and discount pattern "
                            "against stronger products."
                        ),
                        (
                            f"Review the monthly performance of "
                            f"{weakest_name} to determine whether "
                            "the weakness is persistent or recent."
                        ),
                        (
                            "Test product-level pricing, promotion, "
                            "and demand signals before changing "
                            "the broader product strategy."
                        ),
                    ]
                )

        # =====================================================
        # REGION REASONING
        # =====================================================

        if region_analysis:

            region_revenues = []

            for region_name, data in region_analysis.items():

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

                if (
                    region_intent
                    or why_intent
                ):

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

                    investigation_questions.extend(
                        [
                            (
                                f"Which products contribute most "
                                f"to {weakest_region[0]}'s revenue?"
                            ),
                            (
                                f"How has {weakest_region[0]}'s "
                                "revenue changed historically?"
                            ),
                        ]
                    )

                recommendations.extend(
                    [
                        (
                            f"Investigate product contribution "
                            f"within {weakest_region[0]}."
                        ),
                        (
                            f"Compare {weakest_region[0]}'s monthly "
                            "trend against other regions."
                        ),
                        (
                            "Track regional product mix together "
                            "with units, pricing, and discounts."
                        ),
                    ]
                )

        # =====================================================
        # INVESTIGATION DATA ANALYSIS EVIDENCE
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

            investigation_analysis = (
                output.get(
                    "investigation",
                    {}
                )
            )

            if isinstance(
                investigation_analysis,
                dict
            ):

                investigation_analysis_outputs.append(
                    investigation_analysis
                )

        # -----------------------------------------------------
        # Product investigation evidence
        # -----------------------------------------------------

        for investigation in (
            investigation_analysis_outputs
        ):

            investigation_type = str(
                investigation.get(
                    "type",
                    ""
                )
            ).lower()

            if investigation_type == "product_performance":

                target_product = investigation.get(
                    "target_product"
                )

                target_data = investigation.get(
                    "target_product_data",
                    {}
                )

                comparison = investigation.get(
                    "comparison",
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

                        insights.append(
                            f"Investigation evidence shows "
                            f"{target_product} has "
                            f"{units:,.0f} units sold and "
                            f"{revenue:,.2f} total revenue."
                        )

                    if isinstance(
                        differences,
                        dict
                    ):

                        difference_text = []

                        for key, value in differences.items():

                            if isinstance(
                                value,
                                (int, float)
                            ):

                                difference_text.append(
                                    f"{key}: {value:,.2f}"
                                )

                        if difference_text:

                            insights.append(
                                "Product investigation identified "
                                "the following measurable differences: "
                                + ", ".join(
                                    difference_text
                                )
                                + "."
                            )

            elif investigation_type in (
                "product_historical",
                "product_mix",
            ):

                insights.append(
                    "Investigation-stage product evidence was "
                    "used to cross-check the product performance "
                    "pattern across the available periods."
                )

        # -----------------------------------------------------
        # Region investigation evidence
        # -----------------------------------------------------

        for investigation in (
            investigation_analysis_outputs
        ):

            investigation_type = str(
                investigation.get(
                    "type",
                    ""
                )
            ).lower()

            if investigation_type == (
                "regional_product_contribution"
            ):

                target_region = investigation.get(
                    "target_region"
                )

                contribution = investigation.get(
                    "product_contribution",
                    {}
                )

                if target_region:

                    if isinstance(
                        contribution,
                        dict
                    ) and contribution:

                        contribution_items = []

                        for product_name, value in (
                            contribution.items()
                        ):

                            if isinstance(
                                value,
                                dict
                            ):

                                revenue = self._safe_number(
                                    value.get(
                                        "revenue",
                                        0
                                    )
                                )

                            else:

                                revenue = self._safe_number(
                                    value
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

            elif investigation_type == (
                "regional_historical_trend"
            ):

                target_region = investigation.get(
                    "target_region"
                )

                if target_region:

                    insights.append(
                        f"Investigation-stage historical evidence "
                        f"was used to evaluate the revenue trend "
                        f"for {target_region}."
                    )

        # =====================================================
        # EXTERNAL INVESTIGATION EVIDENCE
        # =====================================================

        if investigation_external_sources:

            investigation_count = len(
                investigation_external_sources
            )

            themes = self._extract_market_themes(
                investigation_external_evidence
            )

            if themes:

                theme_text = ", ".join(
                    themes
                )

                investigation_insight = (
                    "Investigation-stage external research "
                    f"validated {investigation_count} source(s) "
                    f"and reinforced market themes around "
                    f"{theme_text}. The evidence is contextual "
                    "and does not establish direct causation "
                    "for this business."
                )

            else:

                investigation_insight = (
                    "Investigation-stage external research "
                    f"validated {investigation_count} source(s) "
                    "for additional market context. The evidence "
                    "does not establish direct causation for "
                    "this business."
                )

            insights.append(
                investigation_insight
            )

        # =====================================================
        # CAUSALITY LIMITATION
        # =====================================================

        if web_search_found:

            insights.append(
                "External market factors may help explain "
                "historical revenue movements, but the available "
                "evidence does not establish that these factors "
                "caused the observed changes in this business."
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
                    "available to generate detailed business "
                    "reasoning."
                )

        # =====================================================
        # INVESTIGATION STATUS
        # =====================================================

        if investigation_required:

            if not investigation_results:

                evidence_gaps.append(
                    "Additional investigation is required "
                    "to support the requested causal explanation."
                )

        # =====================================================
        # DEDUPLICATE INSIGHTS
        # =====================================================

        insights = self._dedupe_strings(
            insights
        )

        # =====================================================
        # DEDUPLICATE RECOMMENDATIONS
        # =====================================================

        recommendations = self._dedupe_strings(
            recommendations
        )

        # =====================================================
        # MAX 3 RECOMMENDATIONS
        # =====================================================

        recommendations = recommendations[:3]

        # =====================================================
        # PRIMARY EXTERNAL SOURCES ONLY
        #
        # IMPORTANT:
        # This is what ResponseBuilder should expose as the
        # main external_sources collection.
        #
        # Investigation sources are intentionally NOT merged
        # here. They are handled separately above.
        # =====================================================

        external_sources = primary_external_sources

        # =====================================================
        # FINAL RESULT
        # =====================================================

        return {
            "status": "success",

            "insights": insights,

            "recommendations": recommendations,

            "evidence_gaps": self._dedupe_strings(
                evidence_gaps
            ),

            "investigation": {
                "required": investigation_required,
                "questions": self._dedupe_strings(
                    investigation_questions
                ),
                "primary_external_source_count": len(
                    primary_external_sources
                ),
                "investigation_external_source_count": len(
                    investigation_external_sources
                ),
                "investigation_sources_available": bool(
                    investigation_external_sources
                ),
            },

            "external_sources": external_sources,

            "external_evidence": external_evidence,

            "primary_external_evidence": (
                primary_external_evidence
            ),

            "investigation_external_evidence": (
                investigation_external_evidence
            ),

            "reasoning_metadata": {
                "primary_external_source_count": len(
                    primary_external_sources
                ),
                "investigation_external_source_count": len(
                    investigation_external_sources
                ),
                "combined_external_evidence_count": len(
                    external_evidence
                ),
                "analysis_output_count": len(
                    analysis_outputs
                ),
                "investigation_result_count": len(
                    investigation_results
                ),
            },
        }

    # =========================================================
    # WEB SOURCE COLLECTION
    # =========================================================

    def _collect_web_sources(
        self,
        output: Any,
    ) -> Tuple[
        List[Dict[str, Any]],
        List[str],
        List[str],
    ]:

        sources = []
        evidence = []
        direct_evidence = []

        if not isinstance(
            output,
            dict
        ):
            return (
                sources,
                evidence,
                direct_evidence,
            )

        results = output.get(
            "results",
            []
        )

        if isinstance(
            results,
            list
        ):

            for item in results:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                title = str(
                    item.get(
                        "title",
                        ""
                    )
                    or ""
                ).strip()

                url = str(
                    item.get(
                        "url",
                        ""
                    )
                    or ""
                ).strip()

                content = str(
                    item.get(
                        "content",
                        item.get(
                            "snippet",
                            ""
                        )
                    )
                    or ""
                ).strip()

                if not (
                    title
                    or url
                    or content
                ):
                    continue

                sources.append(
                    {
                        "title": title,
                        "url": url,
                        "content": content,
                    }
                )

                if title and content:

                    evidence.append(
                        f"{title}: {content}"
                    )

                elif content:

                    evidence.append(
                        content
                    )

        # -----------------------------------------------------
        # Some web-search implementations may return direct
        # text/context in addition to structured sources.
        #
        # This is evidence, NOT a source count.
        # -----------------------------------------------------

        for key in [
            "summary",
            "answer",
            "text",
            "content",
            "context",
        ]:

            value = output.get(
                key
            )

            if isinstance(
                value,
                str
            ) and value.strip():

                direct_evidence.append(
                    value.strip()
                )

        return (
            sources,
            evidence,
            direct_evidence,
        )

    # =========================================================
    # MARKET THEME EXTRACTION
    # =========================================================

    def _extract_market_themes(
        self,
        evidence: List[str],
    ) -> List[str]:

        combined_text = " ".join(
            evidence
        ).lower()

        themes = []

        theme_groups = {
            "pricing pressure": [
                "pricing",
                "price sensitive",
                "price",
                "discount",
                "cost",
                "margin",
                "tariff",
                "inflation",
            ],

            "changing customer behavior": [
                "consumer behavior",
                "customer behavior",
                "buyer",
                "buyers",
                "consumer",
                "customer",
                "demand",
                "shopping",
                "purchasing",
            ],

            "competition": [
                "competition",
                "competitor",
                "competitive",
                "market share",
            ],

            "digital sales and personalization": [
                "personalization",
                "personalized",
                "digital",
                "online sales",
                "ai",
                "technology",
                "recommendation",
                "user-generated",
            ],

            "broader market conditions": [
                "economic",
                "economy",
                "market conditions",
                "industry",
                "macroeconomic",
                "uncertain",
            ],
        }

        for theme, keywords in (
            theme_groups.items()
        ):

            if any(
                keyword in combined_text
                for keyword in keywords
            ):

                themes.append(
                    theme
                )

        return themes[:5]

    # =========================================================
    # PRODUCT NAME RESOLUTION
    # =========================================================

    def _resolve_product_name(
        self,
        product_value: Any,
        product_analysis: Dict[str, Any],
    ) -> str:

        if isinstance(
            product_value,
            str
        ):

            if product_value in product_analysis:
                return product_value

        if isinstance(
            product_value,
            dict
        ):

            name = (
                product_value.get(
                    "name"
                )
                or product_value.get(
                    "product"
                )
            )

            if name:
                return str(
                    name
                )

        if isinstance(
            product_value,
            str
        ):

            return product_value

        return ""

    # =========================================================
    # SAFE NUMBER
    # =========================================================

    def _safe_number(
        self,
        value: Any,
    ) -> float:

        try:

            if value is None:
                return 0.0

            if isinstance(
                value,
                bool
            ):
                return float(value)

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return 0.0

    # =========================================================
    # SOURCE DEDUPLICATION
    # =========================================================

    def _dedupe_sources(
        self,
        sources: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        unique = []
        seen = set()

        for source in sources:

            if not isinstance(
                source,
                dict
            ):
                continue

            title = str(
                source.get(
                    "title",
                    ""
                )
                or ""
            ).strip()

            url = str(
                source.get(
                    "url",
                    ""
                )
                or ""
            ).strip()

            content = str(
                source.get(
                    "content",
                    ""
                )
                or ""
            ).strip()

            key = (
                url.lower()
                if url
                else title.lower()
            )

            if not key:

                key = content[:200].lower()

            if not key:
                continue

            if key in seen:
                continue

            seen.add(
                key
            )

            unique.append(
                {
                    "title": title,
                    "url": url,
                    "content": content,
                }
            )

        return unique

    # =========================================================
    # STRING DEDUPLICATION
    # =========================================================

    def _dedupe_strings(
        self,
        values: List[Any],
    ) -> List[str]:

        unique = []
        seen = set()

        for value in values:

            if value is None:
                continue

            text = str(
                value
            ).strip()

            if not text:
                continue

            key = (
                " ".join(
                    text.lower().split()
                )
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            unique.append(
                text
            )

        return unique

    # =========================================================
    # FAILED RESULT
    # =========================================================

    def _failed_result(
        self,
        message: str,
    ) -> Dict[str, Any]:

        return {
            "status": "failed",
            "insights": [],
            "recommendations": [],
            "evidence_gaps": [
                message
            ],
            "investigation": {
                "required": False,
                "questions": [],
                "primary_external_source_count": 0,
                "investigation_external_source_count": 0,
                "investigation_sources_available": False,
            },
            "external_sources": [],
            "external_evidence": [],
            "primary_external_evidence": [],
            "investigation_external_evidence": [],
            "reasoning_metadata": {
                "primary_external_source_count": 0,
                "investigation_external_source_count": 0,
                "combined_external_evidence_count": 0,
                "analysis_output_count": 0,
                "investigation_result_count": 0,
            },
                }
                        
