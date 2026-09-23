from typing import Any, Dict


class Validator:

    def validate_task_result(
        self,
        task: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:

        issues = []

        task_id = task.get("task_id")
        tool_name = task.get("tool")

        if not task_id:
            issues.append("Task ID is missing.")

        if not tool_name:
            issues.append("Tool name is missing.")

        if not result:
            issues.append("Tool result is empty.")

        if result.get("status") == "error":
            issues.append(
                result.get("error", "Tool execution failed.")
            )

        if result.get("status") == "success":
            if result.get("output") is None:
                issues.append("Successful task has no output.")

        if issues:
            return {
                "status": "failed",
                "task_id": task_id,
                "tool": tool_name,
                "issues": issues
            }

        return {
            "status": "passed",
            "task_id": task_id,
            "tool": tool_name,
            "issues": []
        }
