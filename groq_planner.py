from typing import Any, Dict
import json

from groq_client import groq_client


AVAILABLE_TOOLS = [
    "data_analysis",
    "web_search",
    "calculator",
]


def create_llm_plan(
    user_request: str
) -> Dict[str, Any]:

    prompt = f"""
You are the planning component of BizOps Agent AI.

Your job is to convert a business request into a small,
structured and deterministic execution plan.

Available tools:

1. data_analysis
   - Reads business data from Supabase.
   - Can analyze products, regions, revenue, units sold,
     pricing, discounts and historical/monthly trends.
   - Can perform business data comparisons.

2. web_search
   - Searches external information.
   - Use for market trends, competitor activity,
     industry trends and external business factors.

3. calculator
   - Performs mathematical calculations.
   - Use only when the required numerical values are
     already available from previous task results
     or explicitly provided by the user.

Important planning rules:

1. Use only the available tools.
2. Do not invent tools.
3. Do not execute any tool.
4. Do not make business decisions.
5. Return JSON only.
6. Every task must contain:
   - task_id
   - description
   - tool
7. Tasks execute sequentially.
8. Later tasks may depend on results from earlier tasks.
9. Do not create a calculator task if the required
   numerical operands are not yet available.
10. Do not use data_analysis to generate business
    recommendations. Business recommendations will be
    generated later by the reasoning component.
11. If the request asks why sales changed, dropped,
    increased or declined, the first data_analysis task
    must retrieve/analyze monthly historical sales data.
12. If month-over-month change is required, ensure that
    the required monthly values are available before
    creating a calculator task.
13. If the request asks for product or regional causes,
    create a data_analysis task for product/region analysis.
14. If external market factors are relevant, create a
    web_search task.
15. Keep the plan small and avoid unnecessary tasks.

For a request such as:

"Analyze why our sales dropped this month and suggest 3 actions"

a suitable plan may contain:

- historical/monthly sales analysis
- product/region analysis
- external market research

The final recommendations must be produced by the
business reasoning component after the evidence is
collected.

User request:
{user_request}

Return exactly this JSON structure:

{{
  "tasks": [
    {{
      "task_id": "task_1",
      "description": "string",
      "tool": "data_analysis"
    }}
  ]
}}
"""

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise business-agent planner. "
                    "Return valid JSON only."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    plan = json.loads(content)

    return {
        "status": "success",
        "plan": plan,
        "raw_response": content
    }


def validate_llm_plan(
    plan: Dict[str, Any]
) -> Dict[str, Any]:

    tasks = plan.get("tasks", [])

    if not isinstance(tasks, list):
        return {
            "status": "failed",
            "issues": [
                "Plan tasks must be a list."
            ]
        }

    issues = []

    for task in tasks:

        tool = task.get("tool")

        if tool not in AVAILABLE_TOOLS:
            issues.append(
                f"Unknown tool requested: {tool}"
            )

        if not task.get("task_id"):
            issues.append(
                "Task ID is missing."
            )

        if not task.get("description"):
            issues.append(
                "Task description is missing."
            )

    if issues:
        return {
            "status": "failed",
            "issues": issues
        }

    return {
        "status": "validated",
        "task_count": len(tasks),
        "tasks": tasks,
        "issues": []
    }
    
    



