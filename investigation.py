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

            # Internal business data investigation
            if any(
                phrase in question_lower
                for phrase in [
                    "persistent or temporary",
                    "historical sales",
                    "historical product"
                ]
            ):

                tasks.append({
                    "task_id": f"investigation_{index}",
                    "description": question,
                    "type": "data_request",
                    "tool": "none",
                    "status": "pending"
                })

            # External market / competitor investigation
            elif any(
                phrase in question_lower
                for phrase in [
                    "market",
                    "competitor",
                    "competitive"
                ]
            ):

                tasks.append({
                    "task_id": f"investigation_{index}",
                    "description": question,
                    "type": "external_research",
                    "tool": "web_search",
                    "status": "pending"
                })

            # Unknown investigation type
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
