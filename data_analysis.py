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

        return result
