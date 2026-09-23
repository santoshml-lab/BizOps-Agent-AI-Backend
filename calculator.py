import ast
import operator as op
from typing import Any, Dict

from base import BaseTool


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Performs safe mathematical calculations."

    OPERATORS = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
        ast.Mod: op.mod,
        ast.USub: op.neg,
        ast.UAdd: op.pos,
    }

    def _calculate(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numbers are allowed.")

        if isinstance(node, ast.BinOp):
            operator = self.OPERATORS.get(type(node.op))

            if operator is None:
                raise ValueError("Unsupported operator.")

            left = self._calculate(node.left)
            right = self._calculate(node.right)

            return operator(left, right)

        if isinstance(node, ast.UnaryOp):
            operator = self.OPERATORS.get(type(node.op))

            if operator is None:
                raise ValueError("Unsupported unary operator.")

            return operator(self._calculate(node.operand))

        raise ValueError("Invalid mathematical expression.")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        expression = input_data.get("expression")

        if not expression:
            raise ValueError("Expression is required.")

        try:
            tree = ast.parse(expression, mode="eval")
            result = self._calculate(tree.body)

            return {
                "status": "success",
                "expression": expression,
                "result": result,
            }

        except Exception as error:
            return {
                "status": "error",
                "expression": expression,
                "error": str(error),
            }
