from typing import Any, Dict, List


class Planner:
    def plan(self, user_request: str) -> Dict[str, Any]:

        if not user_request or not user_request.strip():
            raise ValueError("User request is required.")

        request = user_request.lower()

        tasks: List[Dict[str, Any]] = []

        if any(word in request for word in [
            "calculate",
            "calculation",
            "compute",
            "sum",
            "average",
            "percentage",
        ]):
            tasks.append({
                "task_id": "task_1",
                "description": "Perform the required calculation.",
                "tool": "calculator",
                "status": "pending",
            })

        if any(word in request for word in [
            "analyze",
            "analysis",
            "sales data",
            "business data",
            "data",
        ]):
            tasks.append({
                "task_id": f"task_{len(tasks) + 1}",
                "description": "Analyze the provided business data.",
                "tool": "data_analysis",
                "status": "pending",
            })

        if any(word in request for word in [
            "search",
            "latest",
            "current",
            "market trends",
            "competitor",
            "news",
        ]):
            tasks.append({
                "task_id": f"task_{len(tasks) + 1}",
                "description": "Search the web for current information.",
                "tool": "web_search",
                "status": "pending",
            })

        if any(word in request for word in [
            "send email",
            "send an email",
            "email client",
            "email the client",
        ]):
            tasks.append({
                "task_id": f"task_{len(tasks) + 1}",
                "description": "Send an email to the specified recipient.",
                "tool": "send_email",
                "status": "pending",
            })

        if any(word in request for word in [
            "delete data",
            "delete the data",
            "remove data",
            "remove the data",
        ]):
            tasks.append({
                "task_id": f"task_{len(tasks) + 1}",
                "description": "Delete the specified business data.",
                "tool": "delete_data",
                "status": "pending",
            })

        if any(word in request for word in [
            "modify data",
            "update data",
            "change data",
        ]):
            tasks.append({
                "task_id": f"task_{len(tasks) + 1}",
                "description": "Modify the specified business data.",
                "tool": "modify_data",
                "status": "pending",
            })

        if any(word in request for word in [
            "make transaction",
            "make a transaction",
            "process payment",
            "make payment",
        ]):
            tasks.append({
                "task_id": f"task_{len(tasks) + 1}",
                "description": "Perform the requested business transaction.",
                "tool": "make_transaction",
                "status": "pending",
            })

        if not tasks:
            tasks.append({
                "task_id": "task_1",
                "description": "Understand and process the user request.",
                "tool": "none",
                "status": "pending",
            })

        return {
            "status": "success",
            "user_request": user_request,
            "tasks": tasks,
        }
