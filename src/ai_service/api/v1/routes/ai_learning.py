"""AI Learning management routes."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query, Request

from ..schemas.ai_learning import (
    AIInsightsResponse,
    FeedbackRequest,
    FeedbackResponse,
    ImprovementSuggestionsResponse,
    TrainingDataResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Learning"])


@router.get(
    "/insights",
    response_model=AIInsightsResponse,
    summary="Get AI processing insights",
    description="Get comprehensive insights about AI processing performance and learning.",
)
async def get_ai_insights(request: Request) -> AIInsightsResponse:
    """Get AI processing insights and statistics."""
    try:
        ai_learning_service = getattr(request.app.state, "ai_learning_service", None)
        if not ai_learning_service:
            raise HTTPException(
                status_code=503, detail="AI learning service not available"
            )

        insights = await ai_learning_service.get_processing_insights()

        return AIInsightsResponse(
            status="success",
            message="AI insights retrieved successfully",
            insights=insights,
        )

    except Exception as e:
        logger.error("Failed to get AI insights", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/suggestions",
    response_model=ImprovementSuggestionsResponse,
    summary="Get improvement suggestions",
    description="Get suggestions for improving AI accuracy and performance.",
)
async def get_improvement_suggestions(
    request: Request,
) -> ImprovementSuggestionsResponse:
    """Get suggestions for improving AI performance."""
    try:
        ai_learning_service = getattr(request.app.state, "ai_learning_service", None)
        if not ai_learning_service:
            raise HTTPException(
                status_code=503, detail="AI learning service not available"
            )

        suggestions = await ai_learning_service.get_improvement_suggestions()

        return ImprovementSuggestionsResponse(
            status="success",
            message="Improvement suggestions retrieved successfully",
            suggestions=suggestions,
        )

    except Exception as e:
        logger.error("Failed to get improvement suggestions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Add user feedback",
    description="Add user feedback and corrections to improve AI learning.",
)
async def add_feedback(
    request: Request, feedback_data: FeedbackRequest
) -> FeedbackResponse:
    """Add user feedback for AI improvement."""
    try:
        ai_learning_service = getattr(request.app.state, "ai_learning_service", None)
        if not ai_learning_service:
            raise HTTPException(
                status_code=503, detail="AI learning service not available"
            )

        success = await ai_learning_service.add_user_feedback(
            training_data_id=feedback_data.training_data_id,
            corrected_data=feedback_data.corrected_data,
            feedback_type=feedback_data.feedback_type,
            admin_notes=feedback_data.admin_notes,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Training data not found")

        return FeedbackResponse(
            status="success",
            message="Feedback added successfully",
            training_data_id=feedback_data.training_data_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add feedback", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/training-data/failed",
    response_model=TrainingDataResponse,
    summary="Get failed training cases",
    description="Get failed processing cases for review and improvement.",
)
async def get_failed_cases(
    request: Request,
    limit: int = Query(50, ge=1, le=200, description="Number of cases to retrieve"),
    offset: int = Query(0, ge=0, description="Number of cases to skip"),
) -> TrainingDataResponse:
    """Get failed processing cases for review."""
    try:
        ai_learning_service = getattr(request.app.state, "ai_learning_service", None)
        if not ai_learning_service:
            raise HTTPException(
                status_code=503, detail="AI learning service not available"
            )

        # Get the training repository from the service
        training_repository = ai_learning_service._training_repository
        failed_cases = await training_repository.find_failed_cases(
            limit=limit, offset=offset
        )

        # Convert to dict format for response
        cases_data = [case.to_dict() for case in failed_cases]

        return TrainingDataResponse(
            status="success",
            message=f"Retrieved {len(failed_cases)} failed cases",
            training_data=cases_data,
            total_count=len(failed_cases),
        )

    except Exception as e:
        logger.error("Failed to get failed cases", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/training-data/low-accuracy",
    response_model=TrainingDataResponse,
    summary="Get low accuracy cases",
    description="Get cases with low accuracy scores for review.",
)
async def get_low_accuracy_cases(
    request: Request,
    accuracy_threshold: float = Query(
        0.7, ge=0.0, le=1.0, description="Accuracy threshold"
    ),
    limit: int = Query(50, ge=1, le=200, description="Number of cases to retrieve"),
    offset: int = Query(0, ge=0, description="Number of cases to skip"),
) -> TrainingDataResponse:
    """Get cases with low accuracy scores."""
    try:
        ai_learning_service = getattr(request.app.state, "ai_learning_service", None)
        if not ai_learning_service:
            raise HTTPException(
                status_code=503, detail="AI learning service not available"
            )

        # Get the training repository from the service
        training_repository = ai_learning_service._training_repository
        low_accuracy_cases = await training_repository.find_low_accuracy_cases(
            accuracy_threshold=accuracy_threshold, limit=limit, offset=offset
        )

        # Convert to dict format for response
        cases_data = [case.to_dict() for case in low_accuracy_cases]

        return TrainingDataResponse(
            status="success",
            message=f"Retrieved {len(low_accuracy_cases)} low accuracy cases",
            training_data=cases_data,
            total_count=len(low_accuracy_cases),
        )

    except Exception as e:
        logger.error("Failed to get low accuracy cases", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/category-mappings",
    summary="Get learned category mappings",
    description="Get dynamically learned category mappings from user feedback.",
)
async def get_category_mappings(request: Request) -> dict[str, Any]:
    """Get learned category mappings."""
    try:
        ai_learning_service = getattr(request.app.state, "ai_learning_service", None)
        if not ai_learning_service:
            raise HTTPException(
                status_code=503, detail="AI learning service not available"
            )

        mappings = await ai_learning_service.get_dynamic_category_mapping()

        return {
            "status": "success",
            "message": "Category mappings retrieved successfully",
            "mappings": mappings,
            "total_mappings": len(mappings),
        }

    except Exception as e:
        logger.error("Failed to get category mappings", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/cleanup",
    summary="Cleanup old training data",
    description="Clean up old training data to maintain database performance.",
)
async def cleanup_old_data(
    request: Request,
    days_to_keep: int = Query(365, ge=30, le=1825, description="Days of data to keep"),
) -> dict[str, Any]:
    """Clean up old training data."""
    try:
        ai_learning_service = getattr(request.app.state, "ai_learning_service", None)
        if not ai_learning_service:
            raise HTTPException(
                status_code=503, detail="AI learning service not available"
            )

        deleted_count = await ai_learning_service.cleanup_old_data(days_to_keep)

        return {
            "status": "success",
            "message": f"Cleaned up {deleted_count} old training records",
            "deleted_count": deleted_count,
            "days_kept": days_to_keep,
        }

    except Exception as e:
        logger.error("Failed to cleanup old data", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/confidence-report",
    summary="Get confidence calibration report",
    description="Get report on how well AI confidence correlates with actual accuracy.",
)
async def get_confidence_report(request: Request) -> dict[str, Any]:
    """Get confidence calibration report."""
    try:
        ai_learning_service = getattr(request.app.state, "ai_learning_service", None)
        if not ai_learning_service:
            raise HTTPException(
                status_code=503, detail="AI learning service not available"
            )

        report = await ai_learning_service.get_confidence_calibration_report()

        return {
            "status": "success",
            "message": "Confidence calibration report retrieved successfully",
            "report": report,
        }

    except Exception as e:
        logger.error("Failed to get confidence report", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
