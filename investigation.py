from typing import Any, Dict, List


class InvestigationPlanner:

    def create_tasks(
        self,
        investigation: Dict[str, Any]
    ) -> Dict[str, Any]:

        if not investigation:
            return {
                "status": "failed",
                "tasks": [],
                "issues": [
                    "Investigation data is missing."
                ]
            }

        if not investigation.get("required"):
            return {
                "status": "not_required",
                "tasks": [],
                "issues": []
            }

        questions = investigation.get(
            "questions",
            []
        )

        if not questions:
            return {
                "status": "failed",
                "tasks": [],
                "issues": [
                    "Investigation is required but no questions were provided."
                ]
            }

        tasks: List[Dict[str, Any]] = []

        for index, question in enumerate(
            questions,
            start=1
        ):

            question_lower = str(question).lower().strip()

            # -------------------------------------------------
            # 1. PRODUCT PERFORMANCE / WHY INVESTIGATION
            # -------------------------------------------------
            # This MUST come before historical classification.
            # Otherwise questions containing "why" or "factors"
            # can be incorrectly classified.
            # -------------------------------------------------

            if any(
                phrase in question_lower
                for phrase in [
                    "why does",
                    "why is",
                    "why are",
                    "why did",
                    "why does this product",
                    "why is this product",
                    "why does the top",
                    "why is the top",
                    "why does it outperform",
                    "why is it outperforming",
                    "why does it generate",
                    "why is it generating",
                    "why did it outperform",
                    "factors driving",
                    "factors behind",
                    "factors are most strongly associated",
                    "factors most strongly associated",
                    "product-level factors",
                    "product level factors",
                    "reasons behind",
                    "reason behind",
                    "what factors",
                    "what drives",
                    "what is driving",
                    "driving revenue",
                    "revenue drivers",
                    "performance drivers",
                    "outperforms other products",
                    "outperforms others",
                    "outperform other products",
                    "outperform others"
                ]
            ):

                tasks.append({
                    "task_id": f"investigation_{index}",
                    "description": question,
                    "type": "product_performance",
                    "tool": "data_analysis",
                    "status": "pending"
                })

            # -------------------------------------------------
            # 2. HISTORICAL / MONTHLY TREND INVESTIGATION
            # -------------------------------------------------
            # Questions about consistency, months, trends,
            # historical movement, or persistence.
            # -------------------------------------------------

            elif any(
                phrase in question_lower
                for phrase in [
                    "persistent or temporary",
                    "historical",
                    "historically",
                    "historical sales",
                    "historical product",
                    "historical trend",
                    "historical trends",
                    "over time",
                    "past months",
                    "previous months",
                    "previous month",
                    "monthly trend",
                    "monthly trends",
                    "monthly performance",
                    "revenue changed",
                    "revenue change",
                    "revenue trend",
                    "revenue trends",
                    "sales changed",
                    "sales change",
                    "sales trend",
                    "sales trends",
                    "persistent over time",
                    "persistent across months",
                    "consistent across",
                    "consistent over",
                    "consistent across months",
                    "across the observed months",
                    "across months",
                    "across the months",
                    "month over month",
                    "month-to-month",
                    "month on month",
                    "from month to month",
                    "monthly"
                ]
            ):

                tasks.append({
                    "task_id": f"investigation_{index}",
                    "description": question,
                    "type": "historical_trend",
                    "tool": "data_analysis",
                    "status": "pending"
                })

            # -------------------------------------------------
            # 3. PRODUCT / PRODUCT MIX INVESTIGATION
            # -------------------------------------------------

            elif any(
                phrase in question_lower
                for phrase in [
                    "which products contribute",
                    "product mix",
                    "products contribute",
                    "product contribution",
                    "product contributions",
                    "by product",
                    "product performance",
                    "compare products",
                    "compare product",
                    "product comparison"
                ]
            ):

                tasks.append({
                    "task_id": f"investigation_{index}",
                    "description": question,
                    "type": "data_request",
                    "tool": "data_analysis",
                    "status": "pending"
                })

            # -------------------------------------------------
            # 4. EXTERNAL MARKET / COMPETITOR INVESTIGATION
            # -------------------------------------------------

            elif any(
                phrase in question_lower
                for phrase in [
                    "market",
                    "competitor",
                    "competitors",
                    "competitive",
                    "competition",
                    "industry",
                    "external",
                    "market trend",
                    "industry trend",
                    "market demand",
                    "competitor trend"
                ]
            ):

                tasks.append({
                    "task_id": f"investigation_{index}",
                    "description": question,
                    "type": "external_research",
                    "tool": "web_search",
                    "status": "pending"
                })

            # -------------------------------------------------
            # 5. BUSINESS PERFORMANCE INVESTIGATION
            # -------------------------------------------------

            elif any(
                phrase in question_lower
                for phrase in [
                    "underperforming",
                    "underperformance",
                    "performance gap",
                    "performing worse",
                    "performing better",
                    "weak performance",
                    "strong performance",
                    "business performance"
                ]
            ):

                tasks.append({
                    "task_id": f"investigation_{index}",
                    "description": question,
                    "type": "data_request",
                    "tool": "data_analysis",
                    "status": "pending"
                })

            # -------------------------------------------------
            # 6. UNKNOWN INVESTIGATION TYPE
            # -------------------------------------------------

            else:

                tasks.append({
                    "task_id": f"investigation_{index}",
                    "description": question,
                    "type": "unknown",
                    "tool": "none",
                    "status": "pending"
                })

        return {
            "status": "success",
            "task_count": len(tasks),
            "tasks": tasks,
            "issues": []
                }
        

