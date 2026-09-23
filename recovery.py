from typing import Any, Dict


class RecoveryEngine:

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    def recover(
        self,
        task: Dict[str, Any],
        result: Dict[str, Any],
        recovery_state: Dict[str, Any]
    ) -> Dict[str, Any]:

        retry_count = recovery_state.get("retry_count", 0)

        if result.get("status") == "success":
            return {
                "status": "not_required",
                "task_id": task.get("task_id"),
                "retry_count": retry_count,
                "strategy": None,
                "message": "Recovery is not required."
            }

        if retry_count >= self.max_retries:
            return {
                "status": "failed",
                "task_id": task.get("task_id"),
                "retry_count": retry_count,
                "strategy": "max_retries_reached",
                "message": "Maximum retry limit reached."
            }

        return {
            "status": "retry",
            "task_id": task.get("task_id"),
            "retry_count": retry_count + 1,
            "strategy": "retry_same_tool",
            "message": "Task failed. Retrying with the same tool."
        }
