from typing import Any, Dict

from registry import get_tool


class Executor:
    def execute_task(
        self,
        task: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        task_id = task.get("task_id")
        tool_name = task.get("tool")

        if not task_id:
            raise ValueError("Task ID is required.")

        if not tool_name:
            raise ValueError("Tool name is required.")

        if tool_name == "none":
            return {
                "task_id": task_id,
                "tool": tool_name,
                "status": "skipped",
                "input": input_data,
                "output": None,
                "error": None,
            }

        try:
            tool = get_tool(tool_name)

            result = tool.execute(input_data)

            return {
                "task_id": task_id,
                "tool": tool_name,
                "status": "success",
                "input": input_data,
                "output": result,
                "error": None,
            }

        except Exception as error:
            return {
                "task_id": task_id,
                "tool": tool_name,
                "status": "error",
                "input": input_data,
                "output": None,
                "error": str(error),
            }

    def execute_plan(
        self,
        tasks: list,
        task_inputs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:

        results = []

        for task in tasks:
            task_id = task.get("task_id")

            input_data = task_inputs.get(task_id, {})

            result = self.execute_task(
                task,
                input_data
            )

            results.append(result)

        return {
            "status": "success",
            "results": results,
        }
