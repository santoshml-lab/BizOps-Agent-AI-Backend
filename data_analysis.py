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

        # -------------------------------------------------
        # DETECT REGION FROM INVESTIGATION QUESTION
        # -------------------------------------------------

        available_regions = sorted({
            str(row.get("region")).strip()
            for row in data
            if row.get("region")
        })

        selected_region = None

        for region in available_regions:
            if region.lower() in question_lower:
                selected_region = region
                break

        # -------------------------------------------------
        # DETECT PRODUCT FROM INVESTIGATION QUESTION
        # -------------------------------------------------

        available_products = sorted({
            str(row.get("product")).strip()
            for row in data
            if row.get("product")
        })

        selected_product = None

        for product in available_products:
            if product.lower() in question_lower:
                selected_product = product
                break

        # -------------------------------------------------
        # APPLY REGION FILTER FOR INVESTIGATION
        # -------------------------------------------------

        analysis_data = data

        if selected_region:
            analysis_data = [
                row
                for row in data
                if str(row.get("region", "")).strip().lower()
                == selected_region.lower()
            ]

        if not analysis_data:
            raise ValueError(
                "No business data found for the requested analysis scope."
            )

        row_count = len(analysis_data)

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
                for row in analysis_data
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

        for row in analysis_data:

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
                    sum(unit_prices)
                    / len(unit_prices)
                )

            if discounts:

                product_data["average_discount"] = (
                    sum(discounts)
                    / len(discounts)
                )

        # -------------------------------------------------
        # REGION ANALYSIS
        # -------------------------------------------------

        region_analysis = {}

        for row in analysis_data:

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

        for row in analysis_data:

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

        months = list(
            monthly_analysis.keys()
        )

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

        # -------------------------------------------------
        # REGION PRODUCT CONTRIBUTION
        # -------------------------------------------------

        if (
            selected_region
            and (
                "which products contribute"
                in question_lower
                or "products contribute"
                in question_lower
                or "product mix"
                in question_lower
                or "product contribution"
                in question_lower
                or "by product"
                in question_lower
            )
        ):

            investigation_result = {

                "type":
                    "regional_product_contribution",

                "region":
                    selected_region,

                "product_analysis":
                    product_analysis
            }

        # -------------------------------------------------
        # REGION HISTORICAL TREND
        # -------------------------------------------------

        elif (
            selected_region
            and (
                "persistent"
                in question_lower
                or "over time"
                in question_lower
                or "historical trend"
                in question_lower
                or "sales trend"
                in question_lower
                or "monthly"
                in question_lower
                or "month"
                in question_lower
                or "consistent across"
                in question_lower
                or "consistent over"
                in question_lower
                or "across the observed months"
                in question_lower
                or "across months"
                in question_lower
            )
        ):

            investigation_result = {

                "type":
                    "regional_historical_trend",

                "region":
                    selected_region,

                "monthly_analysis":
                    monthly_analysis,

                "monthly_change":
                    monthly_change
            }

        # -------------------------------------------------
        # PRODUCT PERFORMANCE INVESTIGATION
        # -------------------------------------------------

        elif (
            selected_product
            and (
                "why does" in question_lower
                or "why is" in question_lower
                or "why does this product"
                in question_lower
                or "why does the top"
                in question_lower
                or "why does it outperform"
                in question_lower
                or "why does it generate"
                in question_lower
                or "factors driving"
                in question_lower
                or "factors behind"
                in question_lower
                or "what factors"
                in question_lower
                or "what drives"
                in question_lower
                or "revenue drivers"
                in question_lower
                or "performance drivers"
                in question_lower
                or "higher revenue performance"
                in question_lower
                or "outperforms"
                in question_lower
            )
        ):

            target_data = product_analysis.get(
                selected_product
            )

            comparison = {}

            for product, product_data in (
                product_analysis.items()
            ):

                comparison[product] = {

                    "orders":
                        product_data["orders"],

                    "units_sold":
                        product_data["units_sold"],

                    "revenue":
                        product_data["revenue"],

                    "average_unit_price":
                        product_data[
                            "average_unit_price"
                        ],

                    "average_discount":
                        product_data[
                            "average_discount"
                        ]
                }

            # ---------------------------------------------
            # CALCULATE DIFFERENCES FROM OTHER PRODUCTS
            # ---------------------------------------------

            differences = {}

            if target_data:

                for product, product_data in (
                    product_analysis.items()
                ):

                    if product == selected_product:
                        continue

                    differences[product] = {

                        "revenue_difference":
                            (
                                target_data["revenue"]
                                - product_data["revenue"]
                            ),

                        "units_sold_difference":
                            (
                                target_data["units_sold"]
                                - product_data["units_sold"]
                            ),

                        "average_unit_price_difference":
                            (
                                target_data[
                                    "average_unit_price"
                                ]
                                - product_data[
                                    "average_unit_price"
                                ]
                            ),

                        "average_discount_difference":
                            (
                                target_data[
                                    "average_discount"
                                ]
                                - product_data[
                                    "average_discount"
                                ]
                            )
                    }

            investigation_result = {

                "type":
                    "product_performance",

                "target_product":
                    selected_product,

                "target_product_data":
                    target_data,

                "comparison":
                    comparison,

                "differences":
                    differences
            }

        # -------------------------------------------------
        # PRODUCT COMPARISON
        # -------------------------------------------------

        elif (
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
                    product_2 = selected
