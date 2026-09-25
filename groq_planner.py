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
structured execution plan.

Available tools:
- data_analysis
- web_search
- calculator

Rules:
1. Use only the available tools.
2. Do not invent tools.
3. Break the request into logical tasks.
4. Each task must have:
   - task_id
   - description
   - tool
5. Return JSON only.
6. Do not execute any tool.
7. Do not make business decisions.
8. The plan must be suitable for deterministic execution.

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
