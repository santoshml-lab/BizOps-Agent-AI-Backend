from typing import Any, Dict, List
import re


class ResponseBuilder:

    def build(
        self,
        user_request: str,
        plan: Dict[str, Any],
        execution_results: List[Dict[str, Any]],
        memory_context: List[Dict[str, Any]],
        reasoning_result: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:

        insights = []
        recommendations = []
        evidence_gaps = []
        business_concern = None
        external_sources = []

        # ============================================================
        # 1. Use Business Reasoning results when available
        # ============================================================

        if reasoning_result:

            insights.extend(
                reasoning_result.get(
                    "insights",
                    []
                )
            )

            recommendations.extend(
                reasoning_result.get(
                    "recommendations",
                    []
                )
            )

            evidence_gaps.extend(
                reasoning_result.get(
                    "evidence_gaps",
                    []
                )
            )

            business_concern = reasoning_result.get(
                "business_concern"
            )

        # ============================================================
        # 2. Extract external web sources
        # ============================================================

        for result in execution_results:

            if not isinstance(result, dict):
                continue

            if result.get("status") != "success":
                continue

            if result.get("tool") != "web_search":
                continue

            output = result.get(
                "output",
                {}
            )

            if not isinstance(output, dict):
                continue

            web_results = output.get(
                "results",
                []
            )

            if not isinstance(web_results, list):
                continue

            for item in web_results:

                if not isinstance(item, dict):
                    continue

                title = item.get("title")
                url = item.get("url")
                content = item.get("content")

                if not title and not url:
                    continue

                source = {
                    "title": title,
                    "url": url,
                    "content": content
                }

                external_sources.append(
                    source
                )

        # ============================================================
        # 3. Remove duplicate external sources
        # ============================================================

        unique_sources = []
        seen_urls = set()

        for source in external_sources:

            url = source.get("url")

            if url and url in seen_urls:
                continue

            if url:
                seen_urls.add(url)

            unique_sources.append(source)

        external_sources = unique_sources

        actual_source_count = len(
            external_sources
        )

        # ============================================================
        # 4. Detect completed investigation
        #
        # Business reasoning may still contain a stale evidence gap
        # even after validated investigation results are available.
        # ============================================================

        investigation_completed = False

        if reasoning_result:

            investigation = reasoning_result.get(
                "investigation",
                {}
            )

            if isinstance(
                investigation,
                dict
            ):
                investigation_completed = (
                    investigation.get(
                        "completed",
                        False
                    )
                    is True
                )

        # Remove stale investigation-pending messages when
        # investigation has actually completed.
        if investigation_completed:

            evidence_gaps = [
                gap
                for gap in evidence_gaps
                if not any(
                    phrase in str(gap).lower()
                    for phrase in [
                        "additional investigation is required",
                        "business-specific investigation evidence is not yet available",
                        "investigation is required",
                        "investigation evidence is not yet available"
                    ]
                )
            ]

        # ============================================================
        # 5. Normalize source-count insight
        #
        # BusinessReasoning may have generated an outdated source
        # count. The ResponseBuilder has the actual final source list,
        # so use that count as the canonical value.
        # ============================================================

        normalized_insights = []

        for insight in insights:

            if not isinstance(insight, str):
                normalized_insights.append(
                    insight
                )
                continue

            lower_insight = insight.lower()

            if (
                "validated source" in lower_insight
                or "validated sources" in lower_insight
            ):

                insight = re.sub(
                    r"\b\d+\s+validated\s+source\(s\)",
                    f"{actual_source_count} validated source(s)",
                    insight,
                    flags=re.IGNORECASE
                )

            normalized_insights.append(
                insight
            )

        insights = normalized_insights

        # ============================================================
        # 6. Fallback to execution-level insights
        #    if Business Reasoning produced nothing
        # ============================================================

        if not insights:

            for result in execution_results:

                if not isinstance(result, dict):
                    continue

                if result.get("status") != "success":
                    continue

                tool = result.get("tool")

                output = result.get(
                    "output",
                    {}
                )

                if not isinstance(output, dict):
                    continue

                # ----------------------------------------------------
                # DATA ANALYSIS
                # ----------------------------------------------------

                if tool == "data_analysis":

                    numeric_summary = output.get(
                        "numeric_summary",
                        {}
                    )

                    if not isinstance(
                        numeric_summary,
                        dict
                    ):
                        continue

                    for column, summary in numeric_summary.items():

                        if not isinstance(
                            summary,
                            dict
                        ):
                            continue

                        total = summary.get("sum")
                        average = summary.get("average")
                        minimum = summary.get("minimum")
                        maximum = summary.get("maximum")

                        insights.append(
                            f"{column.capitalize()} total is {total}, "
                            f"with an average of {average}. "
                            f"The minimum is {minimum} and "
                            f"the maximum is {maximum}."
                        )

                # ----------------------------------------------------
                # CALCULATOR
                # ----------------------------------------------------

                elif tool == "calculator":

                    if "result" in output:

                        insights.append(
                            f"The calculated result is "
                            f"{output['result']}."
                        )

                # ----------------------------------------------------
                # WEB SEARCH
                # ----------------------------------------------------

                elif tool == "web_search":

                    results = output.get(
                        "results",
                        []
                    )

                    if results:

                        insights.append(
                            f"The web search returned "
                            f"{len(results)} relevant external sources."
                        )

        # ============================================================
        # 7. Use stored business goal as additional context
        # ============================================================

        business_goals = [
            memory.get("value")
            for memory in memory_context
            if isinstance(memory, dict)
            and memory.get("key") == "business_goal"
        ]

        if business_goals and insights:

            recommendations.append(
                "Evaluate these findings against "
                f"the stored business goal: {business_goals[0]}."
            )

        # ============================================================
        # 8. Final fallback
        # ============================================================

        if not insights:

            insights.append(
                "The agent completed the requested tasks "
                "but no business insight was generated."
            )

        # ============================================================
        # 9. Build final response
        # ============================================================

        final_response = " ".join(
            str(insight)
            for insight in insights
        )

        if business_concern:

            final_response += (
                " Main business concern: "
                + str(business_concern)
            )

        if evidence_gaps:

            final_response += (
                " Evidence gaps: "
                + "; ".join(
                    str(gap)
                    for gap in evidence_gaps
                )
                + "."
            )

        if recommendations:

            final_response += (
                " Recommended next steps: "
                + " ".join(
                    str(recommendation)
                    for recommendation in recommendations
                )
            )

        # ============================================================
        # 10. Add external research context
        # ============================================================

        if external_sources:

            final_response += (
                f" External market research included "
                f"{actual_source_count} sources for contextual analysis."
            )

        # ============================================================
        # 11. Return structured agent response
        # ============================================================

        return {
            "status": "success",
            "user_request": user_request,

            # Company/internal reasoning
            "insights": insights,

            "business_concern": business_concern,

            "evidence_gaps": evidence_gaps,

            "recommendations": recommendations,

            # External evidence
            "external_sources": external_sources,

            # Human-readable response
            "final_response": final_response
        }
