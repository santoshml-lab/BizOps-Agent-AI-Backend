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
        # PRODUCT ANALYSIS
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
        # REGION ANALYSIS
        # -------------------------------------------------

        region_analysis = {}

        for row in data:

            region = row.get("region")

            if not region:
                continue

            if region not in region_analysis:
                region_analysis[region] = {
                    "orders": 0,
                    "units_sold": 0,
                    "revenue": 0
                }

            region_data = region_analysis[region]

            region_data["orders"] += 1

            region_data["units_sold"] += (
                row.get("units_sold", 0) or 0
            )

            region_data["revenue"] += (
                row.get("revenue", 0) or 0
            )

        # -------------------------------------------------
        # MONTHLY SALES ANALYSIS
        # -------------------------------------------------

        monthly_analysis = {}

        for row in data:

            order_date = row.get("order_date")

            if not order_date:
                continue

            month = str(order_date)[:7]

            if month not in monthly_analysis:
                monthly_analysis[month] = {
                    "orders": 0,
                    "units_sold": 0,
                    "revenue": 0,
                    "products": {}
                }

            month_data = monthly_analysis[month]

            month_data["orders"] += 1

            month_data["units_sold"] += (
                row.get("units_sold", 0) or 0
            )

            month_data["revenue"] += (
                row.get("revenue", 0) or 0
            )

            product = row.get("product")

            if product:

                if product not in month_data["products"]:
                    month_data["products"][product] = {
                        "orders": 0,
                        "units_sold": 0,
                        "revenue": 0
                    }

                product_month = (
                    month_data["products"][product]
                )

                product_month["orders"] += 1

                product_month["units_sold"] += (
                    row.get("units_sold", 0) or 0
                )

                product_month["revenue"] += (
                    row.get("revenue", 0) or 0
                )

        monthly_analysis = dict(
            sorted(
                monthly_analysis.items(),
                key=lambda item: item[0]
            )
        )

        # -------------------------------------------------
        # MONTH-OVER-MONTH ANALYSIS
        # -------------------------------------------------

        monthly_change = {}

        months = list(monthly_analysis.keys())

        for index in range(1, len(months)):

            previous_month = months[index - 1]
            current_month = months[index]

            previous_revenue = (
                monthly_analysis[
                    previous_month
                ]["revenue"]
            )

            current_revenue = (
                monthly_analysis[
                    current_month
                ]["revenue"]
            )

            change_amount = (
                current_revenue
                - previous_revenue
            )

            if previous_revenue != 0:
                change_percentage = (
                    change_amount
                    / previous_revenue
                ) * 100
            else:
                change_percentage = 0

            monthly_change[current_month] = {
                "previous_month": previous_month,
                "previous_revenue": previous_revenue,
                "current_revenue": current_revenue,
                "change_amount": change_amount,
                "change_percentage": change_percentage,
                "direction": (
                    "increase"
                    if change_amount > 0
                    else "decrease"
                    if change_amount < 0
                    else "no_change"
                )
            }

        # -------------------------------------------------
        # STRONGEST / WEAKEST PRODUCT
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
        # INVESTIGATION RESULT
        # -------------------------------------------------

        investigation_result = None

        # Product comparison
        if (
            "why is" in question_lower
            or "underperforming" in question_lower
            or "performance gap" in question_lower
            or "compare" in question_lower
        ):

            products = list(
                product_analysis.keys()
            )

            if len(products) >= 2:

                selected_products = []

                for product in products:

                    if product.lower() in question_lower:
                        selected_products.append(
                            product
                        )

                if len(selected_products) >= 2:

                    product_1 = selected_products[0]
                    product_2 = selected_products[1]

                else:

                    product_1 = strongest_product[0]
                    product_2 = weakest_product[0]

                first = product_analysis[
                    product_1
                ]

                second = product_analysis[
                    product_2
                ]

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
                            first[
                                "average_unit_price"
                            ]
                            - second[
                                "average_unit_price"
                            ]
                        ),
                        "average_discount": (
                            first[
                                "average_discount"
                            ]
                            - second[
                                "average_discount"
                            ]
                        ),
                    }
                }

        # Historical trend
        if (
            "persistent" in question_lower
            or "over time" in question_lower
            or "historical trend" in question_lower
            or "sales trend" in question_lower
            or "monthly" in question_lower
            or "month" in question_lower
            or "sales dropped" in question_lower
            or "sales decline" in question_lower
            or "sales declined" in question_lower
        ):

            investigation_result = {
                "type": "historical_trend",
                "monthly_analysis": monthly_analysis,
                "monthly_change": monthly_change
            }

        # -------------------------------------------------
        # FINAL RESULT
        # -------------------------------------------------

        result = {
            "status": "success",
            "row_count": row_count,
            "columns": columns,
            "numeric_summary": numeric_summary,
            "product_analysis": product_analysis,
            "region_analysis": region_analysis,
            "monthly_analysis": monthly_analysis,
            "monthly_change": monthly_change
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

        if investigation_result:

            result["investigation"] = (
                investigation_result
            )

        return result
