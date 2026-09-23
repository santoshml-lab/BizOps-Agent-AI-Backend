from typing import Any, Dict

from base import BaseTool


class DataAnalysisTool(BaseTool):
    name = "data_analysis"
    description = "Performs basic analysis on business data."

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        data = input_data.get("data")

        if not data:
            raise ValueError("Data is required.")

        if not isinstance(data, list):
            raise ValueError("Data must be a list of records.")

        if not all(isinstance(row, dict) for row in data):
            raise ValueError("Each record must be a dictionary.")

        row_count = len(data)

        columns = list(data[0].keys()) if data else []

        numeric_summary = {}

        for column in columns:
            values = [
                row[column]
                for row in data
                if isinstance(row.get(column), (int, float))
            ]

            if values:
                numeric_summary[column] = {
                    "count": len(values),
                    "sum": sum(values),
                    "average": sum(values) / len(values),
                    "minimum": min(values),
                    "maximum": max(values),
                }

        return {
            "status": "success",
            "row_count": row_count,
            "columns": columns,
            "numeric_summary": numeric_summary,
        }
