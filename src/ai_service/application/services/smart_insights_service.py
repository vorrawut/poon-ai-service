"""Smart insights service for advanced spending analytics and predictions."""

from __future__ import annotations

import statistics
from datetime import datetime, timedelta
from typing import Any

import structlog

from ...domain.entities.spending_entry import SpendingEntry
from ...domain.repositories.spending_repository import SpendingRepository

logger = structlog.get_logger(__name__)


class SpendingInsight:
    """Represents a spending insight with confidence and recommendations."""

    def __init__(
        self,
        insight_type: str,
        title: str,
        description: str,
        confidence: float,
        impact_score: float,
        recommendations: list[str],
        data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize spending insight."""
        self.insight_type = insight_type
        self.title = title
        self.description = description
        self.confidence = confidence  # 0.0 to 1.0
        self.impact_score = impact_score  # 0.0 to 1.0
        self.recommendations = recommendations
        self.data = data or {}
        self.generated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert insight to dictionary."""
        return {
            "insight_type": self.insight_type,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence,
            "impact_score": self.impact_score,
            "recommendations": self.recommendations,
            "data": self.data,
            "generated_at": self.generated_at.isoformat(),
        }


class SmartInsightsService:
    """Advanced AI service for generating smart spending insights and predictions."""

    def __init__(self, spending_repository: SpendingRepository) -> None:
        """Initialize smart insights service."""
        self._repository = spending_repository

    async def generate_comprehensive_insights(
        self, user_id: str | None = None, days_back: int = 90
    ) -> list[SpendingInsight]:
        """Generate comprehensive spending insights."""
        try:
            # Get spending data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)

            entries = await self._repository.find_by_date_range(
                start_date=start_date, end_date=end_date, limit=1000
            )

            if not entries:
                return []

            insights = []

            # Generate various types of insights
            insights.extend(await self._analyze_spending_patterns(entries))
            insights.extend(await self._detect_anomalies(entries))
            insights.extend(await self._predict_future_spending(entries))
            insights.extend(await self._analyze_category_trends(entries))
            insights.extend(await self._detect_budget_risks(entries))
            insights.extend(await self._suggest_optimizations(entries))
            insights.extend(await self._analyze_payment_patterns(entries))
            insights.extend(await self._detect_seasonal_patterns(entries))

            # Sort by impact score and confidence
            insights.sort(key=lambda x: x.impact_score * x.confidence, reverse=True)

            logger.info(f"Generated {len(insights)} insights for user {user_id}")
            return insights[:20]  # Return top 20 insights

        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return []

    async def _analyze_spending_patterns(
        self, entries: list[SpendingEntry]
    ) -> list[SpendingInsight]:
        """Analyze spending patterns and habits."""
        insights = []

        if len(entries) < 10:
            return insights

        try:
            # Daily spending pattern
            daily_amounts = {}
            for entry in entries:
                day = entry.transaction_date.strftime("%A")
                if day not in daily_amounts:
                    daily_amounts[day] = []
                daily_amounts[day].append(float(entry.amount.amount))

            # Find highest spending day
            avg_by_day = {
                day: statistics.mean(amounts) for day, amounts in daily_amounts.items()
            }
            highest_day = max(avg_by_day, key=avg_by_day.get)
            lowest_day = min(avg_by_day, key=avg_by_day.get)

            if avg_by_day[highest_day] > avg_by_day[lowest_day] * 1.5:
                insights.append(
                    SpendingInsight(
                        insight_type="spending_pattern",
                        title=f"High Spending on {highest_day}s",
                        description=f"You spend {avg_by_day[highest_day]:.0f} THB on average on {highest_day}s, "
                        f"which is {((avg_by_day[highest_day] / avg_by_day[lowest_day] - 1) * 100):.0f}% "
                        f"more than {lowest_day}s.",
                        confidence=0.85,
                        impact_score=0.7,
                        recommendations=[
                            f"Consider planning purchases for {lowest_day}s when you typically spend less",
                            f"Set a spending limit for {highest_day}s to control expenses",
                            "Review what drives higher spending on this day",
                        ],
                        data={"daily_averages": avg_by_day},
                    )
                )

            # Spending frequency analysis
            total_days = (
                max(e.transaction_date for e in entries)
                - min(e.transaction_date for e in entries)
            ).days + 1
            spending_frequency = len(entries) / total_days

            if spending_frequency > 2:  # More than 2 transactions per day on average
                insights.append(
                    SpendingInsight(
                        insight_type="spending_frequency",
                        title="High Transaction Frequency",
                        description=f"You make {spending_frequency:.1f} transactions per day on average. "
                        "This might indicate frequent small purchases.",
                        confidence=0.9,
                        impact_score=0.6,
                        recommendations=[
                            "Consider consolidating purchases to reduce transaction fees",
                            "Plan weekly shopping to reduce frequent small purchases",
                            "Use a spending app to track micro-transactions",
                        ],
                        data={
                            "frequency": spending_frequency,
                            "total_transactions": len(entries),
                        },
                    )
                )

        except Exception as e:
            logger.error(f"Error analyzing spending patterns: {e}")

        return insights

    async def _detect_anomalies(
        self, entries: list[SpendingEntry]
    ) -> list[SpendingInsight]:
        """Detect spending anomalies and unusual patterns."""
        insights = []

        if len(entries) < 20:
            return insights

        try:
            amounts = [float(entry.amount.amount) for entry in entries]
            mean_amount = statistics.mean(amounts)
            std_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0

            # Find outliers (amounts > 2 standard deviations from mean)
            outliers = [
                entry
                for entry in entries
                if abs(float(entry.amount.amount) - mean_amount) > 2 * std_amount
            ]

            if outliers and std_amount > 0:
                outlier_count = len(outliers)
                outlier_percentage = (outlier_count / len(entries)) * 100

                if outlier_percentage > 5:  # More than 5% outliers
                    max_outlier = max(outliers, key=lambda x: float(x.amount.amount))

                    insights.append(
                        SpendingInsight(
                            insight_type="anomaly_detection",
                            title="Unusual Spending Detected",
                            description=f"Found {outlier_count} unusual transactions ({outlier_percentage:.1f}% of total). "
                            f"Largest unusual expense: {max_outlier.amount.amount} THB for {max_outlier.description}.",
                            confidence=0.8,
                            impact_score=0.8,
                            recommendations=[
                                "Review large transactions to ensure they were intentional",
                                "Set up alerts for transactions above your normal spending range",
                                "Consider if these represent one-time expenses or new spending habits",
                            ],
                            data={
                                "outlier_count": outlier_count,
                                "outlier_percentage": outlier_percentage,
                                "mean_amount": mean_amount,
                                "std_amount": std_amount,
                            },
                        )
                    )

            # Detect sudden spending spikes
            daily_totals = {}
            for entry in entries:
                date_key = entry.transaction_date.date()
                if date_key not in daily_totals:
                    daily_totals[date_key] = 0
                daily_totals[date_key] += float(entry.amount.amount)

            if len(daily_totals) > 7:
                daily_amounts = list(daily_totals.values())
                daily_mean = statistics.mean(daily_amounts)
                daily_std = (
                    statistics.stdev(daily_amounts) if len(daily_amounts) > 1 else 0
                )

                spike_days = [
                    date
                    for date, amount in daily_totals.items()
                    if amount > daily_mean + 2 * daily_std
                ]

                if spike_days and daily_std > 0:
                    insights.append(
                        SpendingInsight(
                            insight_type="spending_spike",
                            title="Spending Spikes Detected",
                            description=f"Found {len(spike_days)} days with unusually high spending. "
                            f"Average daily spending: {daily_mean:.0f} THB.",
                            confidence=0.75,
                            impact_score=0.7,
                            recommendations=[
                                "Identify what caused high spending on these days",
                                "Plan for similar events in the future",
                                "Consider setting daily spending limits",
                            ],
                            data={
                                "spike_days": len(spike_days),
                                "daily_average": daily_mean,
                            },
                        )
                    )

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")

        return insights

    async def _predict_future_spending(
        self, entries: list[SpendingEntry]
    ) -> list[SpendingInsight]:
        """Predict future spending based on historical patterns."""
        insights = []

        if len(entries) < 30:
            return insights

        try:
            # Calculate monthly spending trend
            monthly_totals = {}
            for entry in entries:
                month_key = entry.transaction_date.strftime("%Y-%m")
                if month_key not in monthly_totals:
                    monthly_totals[month_key] = 0
                monthly_totals[month_key] += float(entry.amount.amount)

            if len(monthly_totals) >= 2:
                months = sorted(monthly_totals.keys())
                amounts = [monthly_totals[month] for month in months]

                # Simple linear trend calculation
                if len(amounts) >= 3:
                    # Calculate trend (simple slope)
                    x_values = list(range(len(amounts)))
                    n = len(amounts)
                    sum_x = sum(x_values)
                    sum_y = sum(amounts)
                    sum_xy = sum(x * y for x, y in zip(x_values, amounts, strict=False))
                    sum_x2 = sum(x * x for x in x_values)

                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                    intercept = (sum_y - slope * sum_x) / n

                    # Predict next month
                    next_month_prediction = slope * len(amounts) + intercept
                    current_avg = statistics.mean(amounts)
                    trend_percentage = (
                        (slope / current_avg) * 100 if current_avg > 0 else 0
                    )

                    if abs(trend_percentage) > 5:  # Significant trend
                        trend_direction = "increasing" if slope > 0 else "decreasing"

                        insights.append(
                            SpendingInsight(
                                insight_type="spending_prediction",
                                title=f"Spending Trend: {trend_direction.title()}",
                                description=f"Your monthly spending is {trend_direction} by {abs(trend_percentage):.1f}% per month. "
                                f"Predicted next month: {next_month_prediction:.0f} THB.",
                                confidence=0.7,
                                impact_score=0.8,
                                recommendations=[
                                    f"Plan for {trend_direction} spending trend",
                                    "Review what's driving this trend",
                                    "Adjust budget accordingly"
                                    if slope > 0
                                    else "Consider if this reduction is sustainable",
                                ],
                                data={
                                    "trend_percentage": trend_percentage,
                                    "prediction": next_month_prediction,
                                    "current_average": current_avg,
                                    "monthly_data": monthly_totals,
                                },
                            )
                        )

        except Exception as e:
            logger.error(f"Error predicting future spending: {e}")

        return insights

    async def _analyze_category_trends(
        self, entries: list[SpendingEntry]
    ) -> list[SpendingInsight]:
        """Analyze spending trends by category."""
        insights = []

        try:
            # Group by category
            category_totals = {}
            category_counts = {}

            for entry in entries:
                category = entry.category.value
                amount = float(entry.amount.amount)

                if category not in category_totals:
                    category_totals[category] = 0
                    category_counts[category] = 0

                category_totals[category] += amount
                category_counts[category] += 1

            total_spending = sum(category_totals.values())

            # Find dominant categories
            category_percentages = {
                cat: (amount / total_spending) * 100
                for cat, amount in category_totals.items()
            }

            dominant_category = max(category_percentages, key=category_percentages.get)
            dominant_percentage = category_percentages[dominant_category]

            if dominant_percentage > 40:  # More than 40% in one category
                insights.append(
                    SpendingInsight(
                        insight_type="category_dominance",
                        title=f"High Spending in {dominant_category}",
                        description=f"{dominant_percentage:.1f}% of your spending is in {dominant_category} "
                        f"({category_totals[dominant_category]:.0f} THB).",
                        confidence=0.9,
                        impact_score=0.7,
                        recommendations=[
                            f"Review {dominant_category} expenses for optimization opportunities",
                            "Consider diversifying your spending across categories",
                            f"Set a specific budget limit for {dominant_category}",
                        ],
                        data={
                            "category": dominant_category,
                            "percentage": dominant_percentage,
                            "amount": category_totals[dominant_category],
                            "all_categories": category_percentages,
                        },
                    )
                )

            # Find categories with high transaction frequency but low amounts
            for category, count in category_counts.items():
                if count >= 5:  # At least 5 transactions
                    avg_amount = category_totals[category] / count
                    overall_avg = total_spending / len(entries)

                    if avg_amount < overall_avg * 0.5:  # Much smaller than average
                        insights.append(
                            SpendingInsight(
                                insight_type="micro_spending",
                                title=f"Frequent Small {category} Purchases",
                                description=f"You made {count} {category} purchases averaging {avg_amount:.0f} THB each. "
                                "These small frequent purchases add up.",
                                confidence=0.8,
                                impact_score=0.6,
                                recommendations=[
                                    f"Consider consolidating {category} purchases",
                                    "Plan weekly/monthly {category} shopping",
                                    "Track these small expenses more carefully",
                                ],
                                data={
                                    "category": category,
                                    "transaction_count": count,
                                    "average_amount": avg_amount,
                                    "total_amount": category_totals[category],
                                },
                            )
                        )

        except Exception as e:
            logger.error(f"Error analyzing category trends: {e}")

        return insights

    async def _detect_budget_risks(
        self, entries: list[SpendingEntry]
    ) -> list[SpendingInsight]:
        """Detect potential budget risks and overspending patterns."""
        insights = []

        try:
            # Calculate current month spending
            current_month = datetime.utcnow().strftime("%Y-%m")
            current_month_entries = [
                entry
                for entry in entries
                if entry.transaction_date.strftime("%Y-%m") == current_month
            ]

            if not current_month_entries:
                return insights

            current_month_total = sum(
                float(entry.amount.amount) for entry in current_month_entries
            )

            # Calculate average monthly spending from previous months
            other_months = {}
            for entry in entries:
                month_key = entry.transaction_date.strftime("%Y-%m")
                if month_key != current_month:
                    if month_key not in other_months:
                        other_months[month_key] = 0
                    other_months[month_key] += float(entry.amount.amount)

            if other_months:
                avg_monthly_spending = statistics.mean(other_months.values())
                days_in_current_month = datetime.utcnow().day
                days_in_month = 30  # Approximate

                # Project current month spending
                projected_monthly = (
                    current_month_total / days_in_current_month
                ) * days_in_month

                if projected_monthly > avg_monthly_spending * 1.2:  # 20% over average
                    overspend_percentage = (
                        (projected_monthly / avg_monthly_spending) - 1
                    ) * 100

                    insights.append(
                        SpendingInsight(
                            insight_type="budget_risk",
                            title="Potential Overspending This Month",
                            description=f"You're on track to spend {projected_monthly:.0f} THB this month, "
                            f"which is {overspend_percentage:.0f}% above your average of {avg_monthly_spending:.0f} THB.",
                            confidence=0.8,
                            impact_score=0.9,
                            recommendations=[
                                "Review and reduce discretionary spending for the rest of the month",
                                "Identify what's causing the increased spending",
                                "Set up spending alerts to stay on track",
                            ],
                            data={
                                "projected_spending": projected_monthly,
                                "average_spending": avg_monthly_spending,
                                "current_spending": current_month_total,
                                "overspend_percentage": overspend_percentage,
                            },
                        )
                    )

        except Exception as e:
            logger.error(f"Error detecting budget risks: {e}")

        return insights

    async def _suggest_optimizations(
        self, entries: list[SpendingEntry]
    ) -> list[SpendingInsight]:
        """Suggest spending optimizations and savings opportunities."""
        insights = []

        try:
            # Analyze payment methods for potential savings
            payment_totals = {}
            for entry in entries:
                payment_method = entry.payment_method.value
                if payment_method not in payment_totals:
                    payment_totals[payment_method] = 0
                payment_totals[payment_method] += float(entry.amount.amount)

            total_spending = sum(payment_totals.values())
            cash_percentage = (
                (payment_totals.get("Cash", 0) / total_spending) * 100
                if total_spending > 0
                else 0
            )

            if cash_percentage > 60:  # High cash usage
                insights.append(
                    SpendingInsight(
                        insight_type="optimization",
                        title="High Cash Usage - Missing Rewards",
                        description=f"{cash_percentage:.1f}% of your spending is in cash. "
                        "You might be missing out on credit card rewards and cashback.",
                        confidence=0.7,
                        impact_score=0.6,
                        recommendations=[
                            "Consider using a rewards credit card for regular purchases",
                            "Look into cashback programs",
                            "Keep cash for small vendors who don't accept cards",
                        ],
                        data={
                            "cash_percentage": cash_percentage,
                            "payment_breakdown": payment_totals,
                        },
                    )
                )

            # Find potential subscription or recurring expense optimization
            merchant_counts = {}
            merchant_totals = {}

            for entry in entries:
                merchant = entry.merchant
                if merchant not in merchant_counts:
                    merchant_counts[merchant] = 0
                    merchant_totals[merchant] = 0
                merchant_counts[merchant] += 1
                merchant_totals[merchant] += float(entry.amount.amount)

            # Find merchants with regular spending
            regular_merchants = {
                merchant: {"count": count, "total": merchant_totals[merchant]}
                for merchant, count in merchant_counts.items()
                if count >= 4  # At least 4 transactions
            }

            if regular_merchants:
                top_regular = max(
                    regular_merchants.items(), key=lambda x: x[1]["total"]
                )
                merchant_name, data = top_regular
                avg_per_visit = data["total"] / data["count"]

                insights.append(
                    SpendingInsight(
                        insight_type="optimization",
                        title=f"Regular Spending at {merchant_name}",
                        description=f"You've spent {data['total']:.0f} THB across {data['count']} visits "
                        f"(avg: {avg_per_visit:.0f} THB per visit). Consider loyalty programs or bulk purchases.",
                        confidence=0.8,
                        impact_score=0.5,
                        recommendations=[
                            f"Check if {merchant_name} offers loyalty programs or discounts",
                            "Consider bulk purchases if applicable",
                            "Look for alternative vendors with better prices",
                        ],
                        data={
                            "merchant": merchant_name,
                            "visit_count": data["count"],
                            "total_spent": data["total"],
                            "average_per_visit": avg_per_visit,
                        },
                    )
                )

        except Exception as e:
            logger.error(f"Error suggesting optimizations: {e}")

        return insights

    async def _analyze_payment_patterns(
        self, entries: list[SpendingEntry]
    ) -> list[SpendingInsight]:
        """Analyze payment method patterns and preferences."""
        insights = []

        try:
            payment_by_category = {}
            for entry in entries:
                category = entry.category.value
                payment = entry.payment_method.value

                if category not in payment_by_category:
                    payment_by_category[category] = {}
                if payment not in payment_by_category[category]:
                    payment_by_category[category][payment] = 0

                payment_by_category[category][payment] += float(entry.amount.amount)

            # Find categories with strong payment preferences
            for category, payments in payment_by_category.items():
                if len(payments) > 1:  # Multiple payment methods used
                    total_in_category = sum(payments.values())
                    dominant_payment = max(payments, key=payments.get)
                    dominant_percentage = (
                        payments[dominant_payment] / total_in_category
                    ) * 100

                    if dominant_percentage > 80:  # Strong preference
                        insights.append(
                            SpendingInsight(
                                insight_type="payment_pattern",
                                title=f"Strong {dominant_payment} Preference for {category}",
                                description=f"You use {dominant_payment} for {dominant_percentage:.0f}% "
                                f"of {category} purchases ({payments[dominant_payment]:.0f} THB).",
                                confidence=0.7,
                                impact_score=0.4,
                                recommendations=[
                                    f"This payment pattern for {category} seems consistent",
                                    "Consider if this is the most rewarding payment method",
                                    "Evaluate if other payment methods offer better benefits",
                                ],
                                data={
                                    "category": category,
                                    "dominant_payment": dominant_payment,
                                    "percentage": dominant_percentage,
                                    "payment_breakdown": payments,
                                },
                            )
                        )

        except Exception as e:
            logger.error(f"Error analyzing payment patterns: {e}")

        return insights

    async def _detect_seasonal_patterns(
        self, entries: list[SpendingEntry]
    ) -> list[SpendingInsight]:
        """Detect seasonal spending patterns."""
        insights = []

        try:
            # Group by month
            monthly_spending = {}
            for entry in entries:
                month = entry.transaction_date.month
                if month not in monthly_spending:
                    monthly_spending[month] = 0
                monthly_spending[month] += float(entry.amount.amount)

            if len(monthly_spending) >= 6:  # Need at least 6 months of data
                avg_monthly = statistics.mean(monthly_spending.values())

                # Find months with significantly higher spending
                high_months = [
                    month
                    for month, amount in monthly_spending.items()
                    if amount > avg_monthly * 1.3
                ]

                if high_months:
                    month_names = {
                        1: "January",
                        2: "February",
                        3: "March",
                        4: "April",
                        5: "May",
                        6: "June",
                        7: "July",
                        8: "August",
                        9: "September",
                        10: "October",
                        11: "November",
                        12: "December",
                    }

                    high_month_names = [month_names[month] for month in high_months]

                    insights.append(
                        SpendingInsight(
                            insight_type="seasonal_pattern",
                            title="Seasonal Spending Pattern Detected",
                            description=f"You typically spend more in {', '.join(high_month_names)}. "
                            f"Average monthly spending: {avg_monthly:.0f} THB.",
                            confidence=0.6,
                            impact_score=0.5,
                            recommendations=[
                                "Plan and budget for higher spending in these months",
                                "Consider saving extra in other months to prepare",
                                "Identify what drives increased spending during these periods",
                            ],
                            data={
                                "high_spending_months": high_month_names,
                                "monthly_averages": {
                                    month_names[k]: v
                                    for k, v in monthly_spending.items()
                                },
                                "overall_average": avg_monthly,
                            },
                        )
                    )

        except Exception as e:
            logger.error(f"Error detecting seasonal patterns: {e}")

        return insights

    async def get_spending_score(self, user_id: str | None = None) -> dict[str, Any]:
        """Calculate an overall spending health score."""
        try:
            insights = await self.generate_comprehensive_insights(user_id)

            # Calculate score based on insights
            total_score = 100
            risk_deductions = 0
            optimization_opportunities = 0

            for insight in insights:
                if insight.insight_type in ["budget_risk", "anomaly_detection"]:
                    risk_deductions += insight.impact_score * 20
                elif insight.insight_type == "optimization":
                    optimization_opportunities += 1

            final_score = max(0, total_score - risk_deductions)

            # Determine grade
            if final_score >= 90:
                grade = "A+"
                status = "Excellent"
            elif final_score >= 80:
                grade = "A"
                status = "Very Good"
            elif final_score >= 70:
                grade = "B"
                status = "Good"
            elif final_score >= 60:
                grade = "C"
                status = "Fair"
            else:
                grade = "D"
                status = "Needs Improvement"

            return {
                "score": final_score,
                "grade": grade,
                "status": status,
                "risk_factors": len(
                    [
                        i
                        for i in insights
                        if i.insight_type in ["budget_risk", "anomaly_detection"]
                    ]
                ),
                "optimization_opportunities": optimization_opportunities,
                "total_insights": len(insights),
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating spending score: {e}")
            return {
                "score": 0,
                "grade": "N/A",
                "status": "Error calculating score",
                "error": str(e),
            }
