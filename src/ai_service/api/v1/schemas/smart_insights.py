"""Pydantic schemas for smart insights API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .common import BaseResponse


class SmartInsightsResponse(BaseResponse):
    """Response model for smart insights."""

    insights: list[dict[str, Any]] = Field(
        description="List of AI-generated spending insights"
    )
    analysis_period_days: int = Field(
        description="Number of days analyzed for insights"
    )
    total_insights: int = Field(description="Total number of insights generated")


class SpendingScoreResponse(BaseResponse):
    """Response model for spending health score."""

    score: float = Field(description="Spending health score (0-100)", ge=0, le=100)
    grade: str = Field(description="Letter grade (A+, A, B, C, D)")
    status: str = Field(description="Spending health status description")
    risk_factors: int = Field(description="Number of identified risk factors")
    optimization_opportunities: int = Field(
        description="Number of optimization opportunities"
    )
    total_insights: int = Field(description="Total insights used for scoring")
    generated_at: str = Field(description="Timestamp when score was generated")


class SpendingPredictionResponse(BaseResponse):
    """Response model for spending predictions."""

    prediction: dict[str, Any] = Field(
        description="Detailed spending prediction with confidence intervals"
    )


class WeeklyPredictionsResponse(BaseResponse):
    """Response model for weekly spending predictions."""

    predictions: list[dict[str, Any]] = Field(
        description="List of daily spending predictions for the week"
    )
    total_predictions: int = Field(description="Number of daily predictions generated")


class BudgetAlert(BaseModel):
    """Model for budget alert."""

    alert_type: str = Field(
        description="Type of alert (budget_exceeded, budget_warning, spending_spike)"
    )
    severity: str = Field(description="Alert severity (high, medium, low)")
    title: str = Field(description="Alert title")
    message: str = Field(description="Detailed alert message")
    projected_total: float | None = Field(
        default=None, description="Projected monthly total spending"
    )
    current_spending: float | None = Field(
        default=None, description="Current month spending so far"
    )
    budget_remaining: float | None = Field(
        default=None, description="Remaining budget amount"
    )
    days_until_exceeded: float | None = Field(
        default=None, description="Days until budget is exceeded at current rate"
    )
    recent_daily_rate: float | None = Field(
        default=None, description="Recent daily spending rate"
    )
    average_daily_rate: float | None = Field(
        default=None, description="Average daily spending rate"
    )
    increase_percentage: float | None = Field(
        default=None, description="Percentage increase in recent spending"
    )


class BudgetAlertsResponse(BaseResponse):
    """Response model for budget alerts."""

    alerts: list[dict[str, Any]] = Field(
        description="List of budget alerts and warnings"
    )
    total_alerts: int = Field(description="Total number of alerts generated")
    severity_breakdown: dict[str, int] = Field(
        description="Count of alerts by severity level"
    )
    monthly_budget: float = Field(description="Monthly budget amount used for analysis")


class SpendingRecommendation(BaseModel):
    """Model for spending recommendation."""

    category: str = Field(
        description="Recommendation category (optimization, budgeting, savings, risk_management)"
    )
    title: str = Field(description="Recommendation title")
    description: str = Field(description="Detailed recommendation description")
    priority: str = Field(description="Priority level (high, medium, low)")
    potential_savings: float | None = Field(
        default=None, description="Estimated potential savings in THB"
    )
    effort_level: str | None = Field(
        default=None,
        description="Implementation effort level (easy, moderate, difficult)",
    )


class SpendingTrend(BaseModel):
    """Model for spending trend."""

    trend_type: str = Field(
        description="Type of trend (increasing, decreasing, stable, seasonal)"
    )
    period: str = Field(description="Time period for the trend")
    category: str | None = Field(
        default=None, description="Category if trend is category-specific"
    )
    percentage_change: float = Field(description="Percentage change in spending")
    confidence: float = Field(
        description="Confidence in trend analysis (0.0-1.0)", ge=0.0, le=1.0
    )
    description: str = Field(description="Human-readable trend description")


class InsightData(BaseModel):
    """Model for insight data."""

    insight_type: str = Field(description="Type of insight")
    title: str = Field(description="Insight title")
    description: str = Field(description="Detailed insight description")
    confidence: float = Field(description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)
    impact_score: float = Field(description="Impact score (0.0-1.0)", ge=0.0, le=1.0)
    recommendations: list[str] = Field(description="List of actionable recommendations")
    data: dict[str, Any] = Field(
        default_factory=dict, description="Additional data supporting the insight"
    )
    generated_at: str = Field(description="Timestamp when insight was generated")


class PredictionData(BaseModel):
    """Model for prediction data."""

    prediction_type: str = Field(description="Type of prediction")
    period: str = Field(description="Time period for prediction")
    predicted_amount: float = Field(description="Predicted spending amount in THB")
    confidence_interval: dict[str, float] = Field(
        description="Confidence interval with lower and upper bounds"
    )
    confidence_score: float = Field(
        description="Confidence in prediction (0.0-1.0)", ge=0.0, le=1.0
    )
    factors: list[str] = Field(description="Factors considered in prediction")
    recommendations: list[str] = Field(
        description="Recommendations based on prediction"
    )
    data: dict[str, Any] = Field(
        default_factory=dict, description="Additional prediction data"
    )
    generated_at: str = Field(description="Timestamp when prediction was generated")


class SmartInsightsSummary(BaseModel):
    """Summary model for smart insights."""

    total_insights: int = Field(description="Total number of insights generated")
    high_priority_insights: int = Field(description="Number of high priority insights")
    optimization_opportunities: int = Field(
        description="Number of optimization opportunities identified"
    )
    risk_factors: int = Field(description="Number of risk factors identified")
    spending_score: float = Field(
        description="Overall spending health score", ge=0.0, le=100.0
    )
    top_categories: list[str] = Field(description="Top spending categories")
    prediction_accuracy: float | None = Field(
        default=None,
        description="Historical prediction accuracy if available",
        ge=0.0,
        le=1.0,
    )


class AdvancedAnalyticsResponse(BaseResponse):
    """Response model for advanced analytics."""

    insights: list[InsightData] = Field(description="Detailed insights data")
    predictions: list[PredictionData] = Field(description="Spending predictions")
    trends: list[SpendingTrend] = Field(description="Identified spending trends")
    recommendations: list[SpendingRecommendation] = Field(
        description="Personalized recommendations"
    )
    summary: SmartInsightsSummary = Field(description="Summary of analytics results")
    analysis_metadata: dict[str, Any] = Field(
        description="Metadata about the analysis performed"
    )
