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
            # INTERNAL BUSINESS DATA / HISTORICAL INVESTIGATION
            # -------------------------------------------------

            if any(
                phrase in question_lower
                for phrase in [
                    "why does",
                    "why is",
                    "why does this product",
                    "why is this product",
                    "why does the top",
                    "why is the top",
                    "why does it outperform",
                    "why does it generate",
                    "why is it generating",
                    "factors driving",
                    "factors behind",
                    "factors are most strongly associated",
                    "factors most strongly associated",
                    "product-level factors",
                    "reasons behind",
                    "reason behind",
                    "what factors",
                    "what drives",
                    "driving revenue",
                    "revenue drivers",
                    "performance drivers",
                    "outperforms other products",
                    "outperforms others"
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
            # PRODUCT PERFORMANCE / WHY INVESTIGATION
            # -------------------------------------------------

            elif any(
                phrase in question_lower
                for phrase in [
                    "why does",
                    "why is",
                    "why does this product",
                    "why is this product",
                    "why does the top",
                    "why is the top",
                    "why does it outperform",
                    "why does it generate",
                    "why is it generating",
                    "factors driving",
                    "factors behind",
                    "reasons behind",
                    "reason behind",
                    "what factors",
                    "what drives",
                    "driving revenue",
                    "revenue drivers",
                    "performance drivers",
                    "outperforms other products",
                    "outperforms others"
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
            # PRODUCT / PRODUCT MIX INVESTIGATION
            # -------------------------------------------------

            elif any(
                phrase in question_lower
                for phrase in [
                    "which products contribute",
                    "product mix",
                    "products contribute",
                    "product contribution",
                    "by product"
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
            # BUSINESS PERFORMANCE INVESTIGATION
            # -------------------------------------------------

            elif any(
                phrase in question_lower
                for phrase in [
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
        

