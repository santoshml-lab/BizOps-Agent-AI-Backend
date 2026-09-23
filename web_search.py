import os
from typing import Any, Dict

import requests

from base import BaseTool


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Searches the web for current business information."

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query")

        if not query:
            raise ValueError("Search query is required.")

        api_key = os.getenv("TAVILY_API_KEY")

        if not api_key:
            raise ValueError("TAVILY_API_KEY is not configured.")

        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 5,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data.get("results", []):
            results.append(
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "content": item.get("content"),
                }
            )

        return {
            "status": "success",
            "query": query,
            "results": results,
        }
