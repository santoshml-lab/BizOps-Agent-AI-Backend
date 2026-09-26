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

            aggregated_result = {
                "task_id": result.get("task_id"),
                "tool": result.get("tool"),
                "status": result.get("status"),
                "output": result.get("output"),
                "error": result.get("error"),
            }

            # Preserve external web-search evidence
            if result.get("tool") == "web_search":

                output = result.get("output")

                if isinstance(output, dict):

                    sources = output.get("sources", [])

                    if isinstance(sources, list):
                        aggregated_result["sources"] = sources

                    # Preserve common web-search metadata
                    for key in [
                        "query",
                        "title",
                        "url",
                        "content",
                        "snippet",
                        "description",
                        "text",
                    ]:
                        if key in output:
                            aggregated_result[key] = output.get(key)

                elif isinstance(output, list):

                    aggregated_result["sources"] = output

            aggregated_results.append(aggregated_result)

        return {
            "status": "success",
            "count": len(aggregated_results),
            "results": aggregated_results,
        }
