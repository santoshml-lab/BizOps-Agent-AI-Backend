from typing import Any, Dict

from base import BaseTool
from supabase_client import supabase


class DataAnalysisTool(BaseTool):
    name = "data_analysis"
    description = "Performs business data analysis from Supabase."

    def execute(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        # -------------------------------------------------
        # FETCH BUSINESS DATA
        # -------------------------------------------------

        response = (
            supabase
            .table("orders")
            .select("*")
            .execute()
        )

        data = response.data

        if not data:
            raise ValueError(
                "No business data found in Supabase."
            )

        if not isinstance(data, list):
            raise ValueError(
                "Data must be a list of records."
            )

        if not all(
            isinstance(row, dict)
            for row in data
        ):
            raise ValueError(
                "Each record must be a dictionary."
            )

        # -------------------------------------------------
        # INVESTIGATION QUESTION
        # -------------------------------------------------

        investigation_question = (
            input_data.get("investigation_question", "")
            if isinstance(input_data, dict)
            else ""
        )

        question_lower = (
            investigation_question.lower()
            if investigation_question
            else ""
        )

        # -------------------------------------------------
        # BASIC DATA INFORMATION
        # -------------------------------------------------

        row_count = len(data)

        columns = (
            list(data[0].keys())
            if data
            else []
        )

        # -------------------------------------------------
        # NUMERIC SUMMARY
        # -------------------------------------------------

        numeric_summary = {}

        for column in columns:

            values = [
                row[column]
                for row in data
                if isinstance(
                    row.get(column),
                    (int, float)
                )
            ]

            if values:

                numeric_summary[column] = {
                    "count": len(values),
                    "sum": sum(values),
                    "average": (
                        sum(values) / len(values)
                    ),
                    "minimum": min(values),
                    "maximum": max(values),
                }

        # -------------------------------------------------
        # PRODUCT-WISE ANALYSIS
        # -------------------------------------------------

        product_analysis = {}

        for row in data:

            product = row.get("product")

            if not product:
                continue

            if product not in product_analysis:

                product_analysis[product] = {
                    "orders": 0,
                    "units_sold": 0,
                    "revenue": 0,
                    "average_unit_price": 0,
                    "average_discount": 0,
                    "_unit_prices": [],
                    "_discounts": []
                }

            product_data = product_analysis[product]

            product_data["orders"] += 1

            product_data["units_sold"] += (
                row.get("units_sold", 0) or 0
            )

            product_data["revenue"] += (
                row.get("revenue", 0) or 0
            )

            if row.get("unit_price") is not None:

                product_data["_unit_prices"].append(
                    float(row["unit_price"])
                )

            if row.get("discount") is not None:

                product_data["_discounts"].append(
                    float(row["discount"])
                )

        # -------------------------------------------------
        # CALCULATE PRODUCT AVERAGES
        # -------------------------------------------------

        for product, product_data in product_analysis.items():

            unit_prices = product_data.pop(
                "_unit_prices"
            )

            discounts = product_data.pop(
                "_discounts"
            )

            if unit_prices:

                product_data["average_unit_price"] = (
                    sum(unit_prices) / len(unit_prices)
                )

            if discounts:

                product_data["average_discount"] = (
                    sum(discounts) / len(discounts)
                )

        # -------------------------------------------------
        # FIND STRONGEST AND WEAKEST PRODUCTS
        # -------------------------------------------------

        strongest_product = None
        weakest_product = None

        if product_analysis:

            strongest_product = max(
                product_analysis.items(),
                key=lambda item: item[1]["revenue"]
            )

            weakest_product = min(
                product_analysis.items(),
                key=lambda item: item[1]["revenue"]
            )

        # -------------------------------------------------
        # QUESTION-SPECIFIC INVESTIGATION
        # -------------------------------------------------

        investigation_result = None

        # -------------------------------------------------
        # PRODUCT COMPARISON INVESTIGATION
        # -------------------------------------------------

        if (
            "why is" in question_lower
            or "underperforming" in question_lower
            or "performance gap" in question_lower
            or "compare" in question_lower
        ):

            products = list(product_analysis.keys())

            if len(products) >= 2:

                # Try to identify Product A and Product C
                # from the investigation question.

                selected_products = []

                for product in products:

                    if product.lower() in question_lower:
                        selected_products.append(product)

                # If the question explicitly mentions two
                # products, use those two.
                if len(selected_products) >= 2:

                    product_1 = selected_products[0]
                    product_2 = selected_products[1]

                else:

                    product_1 = strongest_product[0]
                    product_2 = weakest_product[0]

                first = product_analysis[product_1]
                second = product_analysis[product_2]

                investigation_result = {
                    "type": "product_comparison",
                    "products": [
                        product_1,
                        product_2
                    ],
                    "comparison": {
                        product_1: first,
                        product_2: second
                    },
                    "differences": {
                        "revenue": (
                            first["revenue"]
                            - second["revenue"]
                        ),
                        "units_sold": (
                            first["units_sold"]
                            - second["units_sold"]
                        ),
                        "average_unit_price": (
                            first["average_unit_price"]
                            - second["average_unit_price"]
                        ),
                        "average_discount": (
                            first["average_discount"]
                            - second["average_discount"]
                        ),
                    }
                }

        # -------------------------------------------------
        # HISTORICAL / PERSISTENCE INVESTIGATION
        # -------------------------------------------------

        if (
            "persistent" in question_lower
            or "over time" in question_lower
            or "historical trend" in question_lower
            or "sales trend" in question_lower
        ):

            monthly_analysis = {}

            for row in data:

                order_date = row.get("order_date")
                product = row.get("product")

                if not order_date or not product:
                    continue

                month = str(order_date)[:7]

                if month not in monthly_analysis:

                    monthly_analysis[month] = {}

                if product not in monthly_analysis[month]:

                    monthly_analysis[month][product] = {
                        "units_sold": 0,
                        "revenue": 0,
                        "orders": 0
                    }

                product_month = (
                    monthly_analysis[month][product]
                )

                product_month["units_sold"] += (
                    row.get("units_sold", 0) or 0
                )

                product_month["revenue"] += (
                    row.get("revenue", 0) or 0
                )

                product_month["orders"] += 1

            # Sort months chronologically.
            monthly_analysis = dict(
                sorted(
                    monthly_analysis.items(),
                    key=lambda item: item[0]
                )
            )

            investigation_result = {
                "type": "historical_trend",
                "monthly_analysis": monthly_analysis
            }

        # -------------------------------------------------
        # RETURN ANALYSIS
        # -------------------------------------------------

        result = {
            "status": "success",
            "row_count": row_count,
            "columns": columns,
            "numeric_summary": numeric_summary,
            "product_analysis": product_analysis,
        }

        if strongest_product:

            result["strongest_product"] = {
                "product": strongest_product[0],
                **strongest_product[1]
            }

        if weakest_product:

            result["weakest_product"] = {
                "product": weakest_product[0],
                **weakest_product[1]
            }

        # Add investigation-specific evidence only when
        # an investigation question was supplied.

        if investigation_result:

            result["investigation"] = investigation_result

        return result
