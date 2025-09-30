"""Advanced spending prediction service with ML-like capabilities."""

from __future__ import annotations

import statistics
from datetime import datetime, timedelta
from typing import Any

import structlog

from ...domain.entities.spending_entry import SpendingEntry
from ...domain.repositories.spending_repository import SpendingRepository
from ...domain.value_objects.spending_category import SpendingCategory

logger = structlog.get_logger(__name__)


class SpendingPrediction:
    """Represents a spending prediction with confidence intervals."""

    def __init__(
        self,
        prediction_type: str,
        period: str,
        predicted_amount: float,
        confidence_interval: tuple[float, float],
        confidence_score: float,
        factors: list[str],
        recommendations: list[str],
        data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize spending prediction."""
        self.prediction_type = prediction_type
        self.period = period
        self.predicted_amount = predicted_amount
        self.confidence_interval = confidence_interval  # (lower, upper)
        self.confidence_score = confidence_score  # 0.0 to 1.0
        self.factors = factors
        self.recommendations = recommendations
        self.data = data or {}
        self.generated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert prediction to dictionary."""
        return {
            "prediction_type": self.prediction_type,
            "period": self.period,
            "predicted_amount": self.predicted_amount,
            "confidence_interval": {
                "lower": self.confidence_interval[0],
                "upper": self.confidence_interval[1],
            },
            "confidence_score": self.confidence_score,
            "factors": self.factors,
            "recommendations": self.recommendations,
            "data": self.data,
            "generated_at": self.generated_at.isoformat(),
        }


class SpendingPredictorService:
    """Advanced service for predicting future spending patterns using ML-like algorithms."""

    def __init__(self, spending_repository: SpendingRepository) -> None:
        """Initialize spending predictor service."""
        self._repository = spending_repository

    async def predict_next_month_spending(
        self, _user_id: str | None = None
    ) -> SpendingPrediction:
        """Predict next month's total spending."""
        try:
            # Get historical data (last 12 months)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=365)

            entries = await self._repository.find_by_date_range(
                start_date=start_date, end_date=end_date, limit=2000
            )

            if len(entries) < 30:
                return self._create_insufficient_data_prediction("next_month")

            # Group by month
            monthly_totals = {}
            for entry in entries:
                month_key = entry.transaction_date.strftime("%Y-%m")
                if month_key not in monthly_totals:
                    monthly_totals[month_key] = 0
                monthly_totals[month_key] += float(entry.amount.amount)

            if len(monthly_totals) < 3:
                return self._create_insufficient_data_prediction("next_month")

            # Use multiple prediction methods and ensemble them
            predictions = []
            factors = []

            # Method 1: Simple moving average
            recent_months = sorted(monthly_totals.keys())[-3:]
            recent_amounts = [monthly_totals[month] for month in recent_months]
            moving_avg = statistics.mean(recent_amounts)
            predictions.append(moving_avg)
            factors.append("3-month moving average")

            # Method 2: Weighted moving average (more weight to recent months)
            if len(recent_amounts) >= 3:
                weights = [1, 2, 3]  # More weight to recent months
                weighted_avg = sum(
                    w * a for w, a in zip(weights, recent_amounts, strict=False)
                ) / sum(weights)
                predictions.append(weighted_avg)
                factors.append("Weighted recent trend")

            # Method 3: Linear trend extrapolation
            if len(monthly_totals) >= 6:
                months = sorted(monthly_totals.keys())
                amounts = [monthly_totals[month] for month in months]
                trend_prediction = self._linear_trend_prediction(amounts)
                if trend_prediction is not None:
                    predictions.append(trend_prediction)
                    factors.append("Linear trend analysis")

            # Method 4: Seasonal adjustment
            seasonal_prediction = self._seasonal_prediction(monthly_totals)
            if seasonal_prediction is not None:
                predictions.append(seasonal_prediction)
                factors.append("Seasonal pattern adjustment")

            # Method 5: Category-based prediction
            category_prediction = await self._category_based_prediction(entries)
            if category_prediction is not None:
                predictions.append(category_prediction)
                factors.append("Category trend analysis")

            # Ensemble prediction (weighted average of methods)
            if predictions:
                # Give more weight to methods that consider more data
                weights = [0.2, 0.25, 0.25, 0.15, 0.15][: len(predictions)]
                ensemble_prediction = sum(
                    w * p for w, p in zip(weights, predictions, strict=False)
                ) / sum(weights[: len(predictions)])
            else:
                ensemble_prediction = statistics.mean(list(monthly_totals.values()))

            # Calculate confidence interval
            historical_std = (
                statistics.stdev(list(monthly_totals.values()))
                if len(monthly_totals) > 1
                else 0
            )
            confidence_interval = (
                max(
                    0, ensemble_prediction - 1.96 * historical_std
                ),  # 95% confidence interval
                ensemble_prediction + 1.96 * historical_std,
            )

            # Calculate confidence score based on data quality and consistency
            confidence_score = self._calculate_confidence_score(
                monthly_totals, predictions
            )

            # Generate recommendations
            recommendations = self._generate_spending_recommendations(
                ensemble_prediction, monthly_totals, factors
            )

            return SpendingPrediction(
                prediction_type="monthly_total",
                period="next_month",
                predicted_amount=ensemble_prediction,
                confidence_interval=confidence_interval,
                confidence_score=confidence_score,
                factors=factors,
                recommendations=recommendations,
                data={
                    "historical_months": len(monthly_totals),
                    "prediction_methods": len(predictions),
                    "recent_average": moving_avg,
                    "historical_average": statistics.mean(
                        list(monthly_totals.values())
                    ),
                    "trend": "increasing"
                    if ensemble_prediction > moving_avg
                    else "stable/decreasing",
                },
            )

        except Exception as e:
            logger.error(f"Error predicting next month spending: {e}")
            return self._create_error_prediction("next_month", str(e))

    async def predict_category_spending(
        self, category: SpendingCategory, _user_id: str | None = None
    ) -> SpendingPrediction:
        """Predict spending for a specific category."""
        try:
            # Get historical data for the category
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=365)

            entries = await self._repository.find_by_category(
                category=category, start_date=start_date, end_date=end_date, limit=1000
            )

            if len(entries) < 10:
                return self._create_insufficient_data_prediction(
                    f"{category.value}_category"
                )

            # Group by month
            monthly_totals = {}
            monthly_counts = {}
            for entry in entries:
                month_key = entry.transaction_date.strftime("%Y-%m")
                if month_key not in monthly_totals:
                    monthly_totals[month_key] = 0
                    monthly_counts[month_key] = 0
                monthly_totals[month_key] += float(entry.amount.amount)
                monthly_counts[month_key] += 1

            if len(monthly_totals) < 2:
                return self._create_insufficient_data_prediction(
                    f"{category.value}_category"
                )

            # Predict based on frequency and amount patterns
            avg_monthly_amount = statistics.mean(list(monthly_totals.values()))
            avg_monthly_frequency = statistics.mean(list(monthly_counts.values()))

            # Consider recent trends
            recent_months = sorted(monthly_totals.keys())[-3:]
            if len(recent_months) >= 2:
                recent_avg = statistics.mean(
                    [monthly_totals[month] for month in recent_months]
                )
                # Weight recent trend more heavily
                prediction = 0.7 * recent_avg + 0.3 * avg_monthly_amount
            else:
                prediction = avg_monthly_amount

            # Calculate confidence interval
            std_dev = (
                statistics.stdev(list(monthly_totals.values()))
                if len(monthly_totals) > 1
                else 0
            )
            confidence_interval = (
                max(0, prediction - 1.5 * std_dev),
                prediction + 1.5 * std_dev,
            )

            # Confidence score based on consistency
            coefficient_of_variation = (
                (std_dev / avg_monthly_amount) if avg_monthly_amount > 0 else 1
            )
            confidence_score = max(0.3, 1 - coefficient_of_variation)

            factors = [
                f"Historical {category.value} spending pattern",
                f"Average {avg_monthly_frequency:.1f} transactions per month",
                "Recent trend analysis",
            ]

            recommendations = [
                f"Budget approximately {prediction:.0f} THB for {category.value} next month",
                f"Typical range: {confidence_interval[0]:.0f} - {confidence_interval[1]:.0f} THB",
                f"Monitor spending if it exceeds {confidence_interval[1]:.0f} THB",
            ]

            return SpendingPrediction(
                prediction_type="category_spending",
                period="next_month",
                predicted_amount=prediction,
                confidence_interval=confidence_interval,
                confidence_score=confidence_score,
                factors=factors,
                recommendations=recommendations,
                data={
                    "category": category.value,
                    "historical_months": len(monthly_totals),
                    "avg_monthly_frequency": avg_monthly_frequency,
                    "avg_transaction_amount": avg_monthly_amount / avg_monthly_frequency
                    if avg_monthly_frequency > 0
                    else 0,
                },
            )

        except Exception as e:
            logger.error(f"Error predicting category spending: {e}")
            return self._create_error_prediction(f"{category.value}_category", str(e))

    async def predict_weekly_spending(
        self, _user_id: str | None = None
    ) -> list[SpendingPrediction]:
        """Predict spending for each day of the week."""
        try:
            # Get recent data (last 3 months)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=90)

            entries = await self._repository.find_by_date_range(
                start_date=start_date, end_date=end_date, limit=1000
            )

            if len(entries) < 21:  # Need at least 3 weeks of data
                return []

            # Group by day of week
            daily_totals = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday
            for entry in entries:
                day_of_week = entry.transaction_date.weekday()
                daily_totals[day_of_week].append(float(entry.amount.amount))

            predictions = []
            day_names = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]

            for day_idx, amounts in daily_totals.items():
                if len(amounts) < 3:  # Need at least 3 data points
                    continue

                avg_amount = statistics.mean(amounts)
                std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0

                confidence_interval = (
                    max(0, avg_amount - std_dev),
                    avg_amount + std_dev,
                )

                # Higher confidence for days with more consistent spending
                coefficient_of_variation = (
                    (std_dev / avg_amount) if avg_amount > 0 else 1
                )
                confidence_score = max(0.4, 1 - coefficient_of_variation * 0.5)

                predictions.append(
                    SpendingPrediction(
                        prediction_type="daily_spending",
                        period=day_names[day_idx],
                        predicted_amount=avg_amount,
                        confidence_interval=confidence_interval,
                        confidence_score=confidence_score,
                        factors=[f"Historical {day_names[day_idx]} spending pattern"],
                        recommendations=[
                            f"Typical {day_names[day_idx]} spending: {avg_amount:.0f} THB",
                            f"Plan for {confidence_interval[0]:.0f} - {confidence_interval[1]:.0f} THB range",
                        ],
                        data={
                            "day_of_week": day_names[day_idx],
                            "sample_size": len(amounts),
                            "spending_frequency": len(amounts)
                            / 12,  # Approximate weeks in 3 months
                        },
                    )
                )

            return sorted(predictions, key=lambda x: x.predicted_amount, reverse=True)

        except Exception as e:
            logger.error(f"Error predicting weekly spending: {e}")
            return []

    async def predict_budget_alerts(
        self, monthly_budget: float, _user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Predict when user might exceed budget and generate alerts."""
        try:
            # Get current month data
            datetime.utcnow().strftime("%Y-%m")
            current_month_start = datetime.utcnow().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

            current_entries = await self._repository.find_by_date_range(
                start_date=current_month_start, end_date=datetime.utcnow(), limit=500
            )

            current_spending = sum(
                float(entry.amount.amount) for entry in current_entries
            )
            days_elapsed = datetime.utcnow().day
            days_in_month = 30  # Approximate

            # Calculate daily spending rate
            daily_rate = current_spending / days_elapsed if days_elapsed > 0 else 0

            # Predict end-of-month spending
            projected_monthly = daily_rate * days_in_month

            alerts = []

            # Budget alerts
            if projected_monthly > monthly_budget:
                days_until_budget_exceeded = (
                    (monthly_budget - current_spending) / daily_rate
                    if daily_rate > 0
                    else float("inf")
                )

                alerts.append(
                    {
                        "alert_type": "budget_exceeded",
                        "severity": "high",
                        "title": "Budget Overrun Predicted",
                        "message": f"At current spending rate ({daily_rate:.0f} THB/day), you'll exceed your "
                        f"{monthly_budget:.0f} THB budget by {projected_monthly - monthly_budget:.0f} THB",
                        "days_until_exceeded": max(0, days_until_budget_exceeded),
                        "projected_total": projected_monthly,
                        "current_spending": current_spending,
                        "budget_remaining": max(0, monthly_budget - current_spending),
                    }
                )

            # Warning alerts (80% of budget)
            elif projected_monthly > monthly_budget * 0.8:
                alerts.append(
                    {
                        "alert_type": "budget_warning",
                        "severity": "medium",
                        "title": "Approaching Budget Limit",
                        "message": f"You're on track to spend {projected_monthly:.0f} THB "
                        f"({(projected_monthly / monthly_budget) * 100:.0f}% of budget)",
                        "projected_total": projected_monthly,
                        "current_spending": current_spending,
                        "budget_remaining": monthly_budget - current_spending,
                    }
                )

            # Spending spike alerts
            if len(current_entries) >= 7:  # Need at least a week of data
                recent_week_spending = sum(
                    float(entry.amount.amount)
                    for entry in current_entries
                    if entry.transaction_date >= datetime.utcnow() - timedelta(days=7)
                )
                weekly_rate = recent_week_spending / 7

                if (
                    weekly_rate > daily_rate * 1.5
                ):  # Recent week is 50% higher than average
                    alerts.append(
                        {
                            "alert_type": "spending_spike",
                            "severity": "medium",
                            "title": "Increased Spending Detected",
                            "message": f"Your spending has increased to {weekly_rate:.0f} THB/day in the last week "
                            f"(vs {daily_rate:.0f} THB/day average)",
                            "recent_daily_rate": weekly_rate,
                            "average_daily_rate": daily_rate,
                            "increase_percentage": ((weekly_rate / daily_rate) - 1)
                            * 100
                            if daily_rate > 0
                            else 0,
                        }
                    )

            return alerts

        except Exception as e:
            logger.error(f"Error predicting budget alerts: {e}")
            return []

    def _linear_trend_prediction(self, amounts: list[float]) -> float | None:
        """Calculate linear trend prediction."""
        try:
            if len(amounts) < 3:
                return None

            n = len(amounts)
            x_values = list(range(n))

            # Calculate linear regression
            sum_x = sum(x_values)
            sum_y = sum(amounts)
            sum_xy = sum(x * y for x, y in zip(x_values, amounts, strict=False))
            sum_x2 = sum(x * x for x in x_values)

            denominator = n * sum_x2 - sum_x * sum_x
            if denominator == 0:
                return None

            slope = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n

            # Predict next value
            next_prediction = slope * n + intercept
            return max(0, next_prediction)

        except Exception:
            return None

    def _seasonal_prediction(self, monthly_totals: dict[str, float]) -> float | None:
        """Predict based on seasonal patterns."""
        try:
            if len(monthly_totals) < 6:
                return None

            # Group by month number (1-12)
            month_patterns = {}
            for month_key, amount in monthly_totals.items():
                month_num = int(month_key.split("-")[1])
                if month_num not in month_patterns:
                    month_patterns[month_num] = []
                month_patterns[month_num].append(amount)

            # Get next month number
            next_month = (datetime.utcnow().month % 12) + 1

            if next_month in month_patterns and len(month_patterns[next_month]) > 0:
                # Use historical average for this month
                seasonal_prediction = statistics.mean(month_patterns[next_month])

                # Adjust for overall trend
                overall_avg = statistics.mean(list(monthly_totals.values()))
                recent_avg = statistics.mean(list(monthly_totals.values())[-3:])
                trend_factor = recent_avg / overall_avg if overall_avg > 0 else 1

                return seasonal_prediction * trend_factor

            return None

        except Exception:
            return None

    async def _category_based_prediction(
        self, entries: list[SpendingEntry]
    ) -> float | None:
        """Predict based on category trends."""
        try:
            if len(entries) < 30:
                return None

            # Group by category and month
            category_monthly = {}
            for entry in entries:
                category = entry.category.value
                month_key = entry.transaction_date.strftime("%Y-%m")

                if category not in category_monthly:
                    category_monthly[category] = {}
                if month_key not in category_monthly[category]:
                    category_monthly[category][month_key] = 0

                category_monthly[category][month_key] += float(entry.amount.amount)

            # Predict each category and sum
            total_prediction = 0
            for _category, monthly_data in category_monthly.items():
                if len(monthly_data) >= 2:
                    recent_months = sorted(monthly_data.keys())[-2:]
                    recent_avg = statistics.mean(
                        [monthly_data[month] for month in recent_months]
                    )
                    total_prediction += recent_avg

            return total_prediction if total_prediction > 0 else None

        except Exception:
            return None

    def _calculate_confidence_score(
        self, monthly_totals: dict[str, float], predictions: list[float]
    ) -> float:
        """Calculate confidence score based on data quality and prediction consistency."""
        try:
            # Base confidence on data quantity
            data_quality_score = min(
                1.0, len(monthly_totals) / 12
            )  # Full confidence with 12 months

            # Consistency of historical data
            amounts = list(monthly_totals.values())
            if len(amounts) > 1:
                cv = statistics.stdev(amounts) / statistics.mean(amounts)
                consistency_score = max(0.3, 1 - cv)
            else:
                consistency_score = 0.5

            # Agreement between prediction methods
            if len(predictions) > 1:
                pred_std = statistics.stdev(predictions)
                pred_mean = statistics.mean(predictions)
                pred_cv = pred_std / pred_mean if pred_mean > 0 else 1
                agreement_score = max(0.3, 1 - pred_cv)
            else:
                agreement_score = 0.7

            # Weighted average
            return (
                0.4 * data_quality_score
                + 0.3 * consistency_score
                + 0.3 * agreement_score
            )

        except Exception:
            return 0.5

    def _generate_spending_recommendations(
        self, prediction: float, monthly_totals: dict[str, float], _factors: list[str]
    ) -> list[str]:
        """Generate recommendations based on prediction."""
        recommendations = []

        try:
            historical_avg = statistics.mean(list(monthly_totals.values()))

            if prediction > historical_avg * 1.1:
                recommendations.append(
                    f"Predicted spending ({prediction:.0f} THB) is above your average. Consider reviewing discretionary expenses."
                )
            elif prediction < historical_avg * 0.9:
                recommendations.append(
                    f"Predicted spending ({prediction:.0f} THB) is below average. Good opportunity to save extra."
                )
            else:
                recommendations.append(
                    f"Predicted spending ({prediction:.0f} THB) is consistent with your typical pattern."
                )

            recommendations.extend(
                [
                    f"Set a budget alert at {prediction * 0.8:.0f} THB to stay on track",
                    "Monitor daily spending to ensure you stay within predicted range",
                    "Review and adjust if actual spending deviates significantly",
                ]
            )

        except Exception:
            recommendations.append(
                "Monitor your spending patterns for better predictions"
            )

        return recommendations

    def _create_insufficient_data_prediction(self, period: str) -> SpendingPrediction:
        """Create prediction for insufficient data scenarios."""
        return SpendingPrediction(
            prediction_type="insufficient_data",
            period=period,
            predicted_amount=0,
            confidence_interval=(0, 0),
            confidence_score=0.0,
            factors=["Insufficient historical data"],
            recommendations=[
                "Continue tracking expenses to improve predictions",
                "Need at least 30 days of data for reliable predictions",
                "Manual budgeting recommended until more data is available",
            ],
            data={"error": "insufficient_data"},
        )

    def _create_error_prediction(self, period: str, error: str) -> SpendingPrediction:
        """Create prediction for error scenarios."""
        return SpendingPrediction(
            prediction_type="error",
            period=period,
            predicted_amount=0,
            confidence_interval=(0, 0),
            confidence_score=0.0,
            factors=["Prediction error"],
            recommendations=["Please try again later or contact support"],
            data={"error": error},
        )
