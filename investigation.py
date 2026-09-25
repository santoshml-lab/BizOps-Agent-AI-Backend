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

            question_lower = question.lower()

            # -------------------------------------------------
            # INTERNAL BUSINESS DATA INVESTIGATION
            # -------------------------------------------------

            if any(
                phrase in question_lower
                for phrase in [
                    "persistent or temporary",
                    "historical sales",
                    "historical product",
                    "persistent over time",
                    "over time",
                    "historical trend",
                    "sales trend",
                    "trend"
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
            # EXTERNAL MARKET / COMPETITOR INVESTIGATION
            # -------------------------------------------------

            elif any(
                phrase in question_lower
                for phrase in [
                    "market",
                    "competitor",
                    "competitive",
                    "industry",
                    "external"
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
            # BUSINESS PERFORMANCE / CAUSE INVESTIGATION
            # -------------------------------------------------

            elif any(
                phrase in question_lower
                for phrase in [
                    "why is",
                    "why are",
                    "underperforming",
                    "underperformance",
                    "performance gap",
                    "performing worse",
                    "performing better"
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
            # UNKNOWN INVESTIGATION TYPE
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
