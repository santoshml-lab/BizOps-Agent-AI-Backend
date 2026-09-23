from typing import Any, Dict, List


class ResultAggregator:

    def aggregate(
        self,
        execution_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        if not execution_results:
            return {
                "status": "failed",
                "error": "No execution results available.",
                "results": [],
            }

        aggregated_results = []

        for result in execution_results:

            if not isinstance(result, dict):
                continue

            aggregated_results.append({
                "task_id": result.get("task_id"),
                "tool": result.get("tool"),
                "status": result.get("status"),
                "output": result.get("output"),
                "error": result.get("error"),
            })

        return {
            "status": "success",
            "count": len(aggregated_results),
            "results": aggregated_results,
        }
