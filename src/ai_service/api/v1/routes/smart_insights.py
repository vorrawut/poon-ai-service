"""API routes for smart insights and predictions."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query, Request

from ....domain.value_objects.spending_category import SpendingCategory
from ..schemas.smart_insights import (
    BudgetAlertsResponse,
    SmartInsightsResponse,
    SpendingPredictionResponse,
    SpendingScoreResponse,
    WeeklyPredictionsResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Smart Insights"])


@router.get(
    "/insights",
    response_model=SmartInsightsResponse,
    summary="Get comprehensive spending insights",
    description="Generate AI-powered insights about spending patterns, anomalies, and optimization opportunities.",
)
async def get_smart_insights(
    request: Request,
    days_back: int = Query(90, ge=7, le=365, description="Number of days to analyze"),
    user_id: str | None = Query(None, description="User ID for personalized insights"),
) -> SmartInsightsResponse:
    """Get comprehensive smart spending insights."""
    try:
        smart_insights_service = getattr(
            request.app.state, "smart_insights_service", None
        )
        if not smart_insights_service:
            raise HTTPException(
                status_code=503, detail="Smart insights service not available"
            )

        insights = await smart_insights_service.generate_comprehensive_insights(
            user_id=user_id, days_back=days_back
        )

        return SmartInsightsResponse(
            status="success",
            message=f"Generated {len(insights)} smart insights",
            insights=[insight.to_dict() for insight in insights],
            analysis_period_days=days_back,
            total_insights=len(insights),
        )

    except Exception as e:
        logger.error("Failed to generate smart insights", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/spending-score",
    response_model=SpendingScoreResponse,
    summary="Get spending health score",
    description="Calculate an overall spending health score based on patterns and risks.",
)
async def get_spending_score(
    request: Request,
    user_id: str | None = Query(None, description="User ID for personalized score"),
) -> SpendingScoreResponse:
    """Get spending health score."""
    try:
        smart_insights_service = getattr(
            request.app.state, "smart_insights_service", None
        )
        if not smart_insights_service:
            raise HTTPException(
                status_code=503, detail="Smart insights service not available"
            )

        score_data = await smart_insights_service.get_spending_score(user_id=user_id)

        return SpendingScoreResponse(
            status="success",
            message="Spending score calculated successfully",
            **score_data,
        )

    except Exception as e:
        logger.error("Failed to calculate spending score", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/predictions/next-month",
    response_model=SpendingPredictionResponse,
    summary="Predict next month's spending",
    description="Predict total spending for the next month using advanced ML-like algorithms.",
)
async def predict_next_month_spending(
    request: Request,
    user_id: str | None = Query(
        None, description="User ID for personalized prediction"
    ),
) -> SpendingPredictionResponse:
    """Predict next month's spending."""
    try:
        spending_predictor_service = getattr(
            request.app.state, "spending_predictor_service", None
        )
        if not spending_predictor_service:
            raise HTTPException(
                status_code=503, detail="Spending predictor service not available"
            )

        prediction = await spending_predictor_service.predict_next_month_spending(
            user_id=user_id
        )

        return SpendingPredictionResponse(
            status="success",
            message="Next month spending prediction generated",
            prediction=prediction.to_dict(),
        )

    except Exception as e:
        logger.error("Failed to predict next month spending", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/predictions/category/{category}",
    response_model=SpendingPredictionResponse,
    summary="Predict category spending",
    description="Predict spending for a specific category next month.",
)
async def predict_category_spending(
    request: Request,
    category: SpendingCategory,
    user_id: str | None = Query(
        None, description="User ID for personalized prediction"
    ),
) -> SpendingPredictionResponse:
    """Predict spending for a specific category."""
    try:
        spending_predictor_service = getattr(
            request.app.state, "spending_predictor_service", None
        )
        if not spending_predictor_service:
            raise HTTPException(
                status_code=503, detail="Spending predictor service not available"
            )

        prediction = await spending_predictor_service.predict_category_spending(
            category=category, user_id=user_id
        )

        return SpendingPredictionResponse(
            status="success",
            message=f"Category {category.value} spending prediction generated",
            prediction=prediction.to_dict(),
        )

    except Exception as e:
        logger.error(
            "Failed to predict category spending", error=str(e), category=category.value
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/predictions/weekly",
    response_model=WeeklyPredictionsResponse,
    summary="Predict weekly spending patterns",
    description="Predict spending for each day of the week based on historical patterns.",
)
async def predict_weekly_spending(
    request: Request,
    user_id: str | None = Query(
        None, description="User ID for personalized predictions"
    ),
) -> WeeklyPredictionsResponse:
    """Predict weekly spending patterns."""
    try:
        spending_predictor_service = getattr(
            request.app.state, "spending_predictor_service", None
        )
        if not spending_predictor_service:
            raise HTTPException(
                status_code=503, detail="Spending predictor service not available"
            )

        predictions = await spending_predictor_service.predict_weekly_spending(
            user_id=user_id
        )

        return WeeklyPredictionsResponse(
            status="success",
            message=f"Generated {len(predictions)} weekly spending predictions",
            predictions=[prediction.to_dict() for prediction in predictions],
            total_predictions=len(predictions),
        )

    except Exception as e:
        logger.error("Failed to predict weekly spending", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/budget-alerts",
    response_model=BudgetAlertsResponse,
    summary="Get budget alerts and warnings",
    description="Get predictive alerts about potential budget overruns and spending spikes.",
)
async def get_budget_alerts(
    request: Request,
    monthly_budget: float = Query(
        ..., gt=0, description="Monthly budget amount in THB"
    ),
    user_id: str | None = Query(None, description="User ID for personalized alerts"),
) -> BudgetAlertsResponse:
    """Get budget alerts and warnings."""
    try:
        spending_predictor_service = getattr(
            request.app.state, "spending_predictor_service", None
        )
        if not spending_predictor_service:
            raise HTTPException(
                status_code=503, detail="Spending predictor service not available"
            )

        alerts = await spending_predictor_service.predict_budget_alerts(
            monthly_budget=monthly_budget, user_id=user_id
        )

        # Count alerts by severity
        high_severity = len([a for a in alerts if a.get("severity") == "high"])
        medium_severity = len([a for a in alerts if a.get("severity") == "medium"])
        low_severity = len([a for a in alerts if a.get("severity") == "low"])

        return BudgetAlertsResponse(
            status="success",
            message=f"Generated {len(alerts)} budget alerts",
            alerts=alerts,
            total_alerts=len(alerts),
            severity_breakdown={
                "high": high_severity,
                "medium": medium_severity,
                "low": low_severity,
            },
            monthly_budget=monthly_budget,
        )

    except Exception as e:
        logger.error("Failed to generate budget alerts", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/recommendations",
    summary="Get personalized spending recommendations",
    description="Get AI-powered recommendations for optimizing spending and saving money.",
)
async def get_spending_recommendations(
    request: Request,
    user_id: str | None = Query(
        None, description="User ID for personalized recommendations"
    ),
    focus_area: str | None = Query(
        None,
        description="Focus area for recommendations (optimization, budgeting, savings)",
    ),
) -> dict[str, Any]:
    """Get personalized spending recommendations."""
    try:
        smart_insights_service = getattr(
            request.app.state, "smart_insights_service", None
        )
        if not smart_insights_service:
            raise HTTPException(
                status_code=503, detail="Smart insights service not available"
            )

        # Get insights and filter for recommendations
        insights = await smart_insights_service.generate_comprehensive_insights(
            user_id=user_id
        )

        # Group recommendations by type
        recommendations: dict[str, list[dict[str, Any]]] = {
            "optimization": [],
            "budgeting": [],
            "savings": [],
            "risk_management": [],
        }

        for insight in insights:
            if insight.insight_type == "optimization":
                recommendations["optimization"].extend(insight.recommendations)
            elif insight.insight_type in ["budget_risk", "spending_spike"]:
                recommendations["budgeting"].extend(insight.recommendations)
                recommendations["risk_management"].extend(insight.recommendations)
            elif insight.insight_type in ["spending_pattern", "category_dominance"]:
                recommendations["savings"].extend(insight.recommendations)

        # Filter by focus area if specified
        if focus_area and focus_area in recommendations:
            filtered_recommendations = {focus_area: recommendations[focus_area]}
        else:
            filtered_recommendations = recommendations

        # Remove duplicates and limit recommendations
        for category in filtered_recommendations:
            filtered_recommendations[category] = list(
                dict.fromkeys(filtered_recommendations[category])
            )[:5]

        return {
            "status": "success",
            "message": "Personalized recommendations generated",
            "recommendations": filtered_recommendations,
            "focus_area": focus_area,
            "total_recommendations": sum(
                len(recs) for recs in filtered_recommendations.values()
            ),
        }

    except Exception as e:
        logger.error("Failed to generate recommendations", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/trends",
    summary="Get spending trends analysis",
    description="Analyze spending trends across different time periods and categories.",
)
async def get_spending_trends(
    request: Request,
    period: str = Query(
        "monthly",
        pattern="^(daily|weekly|monthly|quarterly)$",
        description="Trend analysis period",
    ),
    category: SpendingCategory | None = Query(
        None, description="Specific category to analyze"
    ),
    user_id: str | None = Query(None, description="User ID for personalized trends"),
) -> dict[str, Any]:
    """Get spending trends analysis."""
    try:
        smart_insights_service = getattr(
            request.app.state, "smart_insights_service", None
        )
        if not smart_insights_service:
            raise HTTPException(
                status_code=503, detail="Smart insights service not available"
            )

        # Get insights and extract trend-related information
        insights = await smart_insights_service.generate_comprehensive_insights(
            user_id=user_id
        )

        trend_insights = [
            insight
            for insight in insights
            if insight.insight_type
            in ["spending_pattern", "seasonal_pattern", "spending_prediction"]
        ]

        trends: dict[str, Any] = {
            "period": period,
            "category": category.value if category else "all",
            "trend_insights": [insight.to_dict() for insight in trend_insights],
            "summary": {
                "total_trends_identified": len(trend_insights),
                "high_confidence_trends": len(
                    [i for i in trend_insights if i.confidence > 0.8]
                ),
                "actionable_trends": len(
                    [i for i in trend_insights if i.impact_score > 0.7]
                ),
            },
        }

        # Extract key trend indicators
        if trend_insights:
            trends["key_findings"] = []
            for insight in trend_insights[:3]:  # Top 3 trends
                trends["key_findings"].append(
                    {
                        "title": insight.title,
                        "description": insight.description,
                        "confidence": insight.confidence,
                        "impact": insight.impact_score,
                    }
                )

        return {
            "status": "success",
            "message": f"Spending trends analysis for {period} period",
            "trends": trends,
        }

    except Exception as e:
        logger.error("Failed to analyze spending trends", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
