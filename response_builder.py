from typing import Any, Dict, List

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

    # Remove duplicate sources
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

    # ============================================================
    # 3. Fallback to execution-level insights
    #    if Business Reasoning produced nothing
    # ============================================================

    if not insights:

        for result in execution_results:

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
    # 4. Use stored business goal as additional context
    # ============================================================

    business_goals = [
        memory.get("value")
        for memory in memory_context
        if memory.get("key") == "business_goal"
    ]

    if business_goals and insights:

        recommendations.append(
            "Evaluate these findings against "
            f"the stored business goal: {business_goals[0]}."
        )

    # ============================================================
    # 5. Final fallback
    # ============================================================

    if not insights:

        insights.append(
            "The agent completed the requested tasks "
            "but no business insight was generated."
        )

    # ============================================================
    # 6. Build final response
    # ============================================================

    final_response = " ".join(
        insights
    )

    if business_concern:

        final_response += (
            " Main business concern: "
            + business_concern
        )

    if evidence_gaps:

        final_response += (
            " Evidence gaps: "
            + "; ".join(evidence_gaps)
            + "."
        )

    if recommendations:

        final_response += (
            " Recommended next steps: "
            + " ".join(recommendations)
        )

    # ============================================================
    # 7. Add external research context
    # ============================================================

    if external_sources:

        final_response += (
            f" External market research included "
            f"{len(external_sources)} sources for contextual analysis."
        )

    # ============================================================
    # 8. Return structured agent response
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
