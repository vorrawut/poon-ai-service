"""Spending-related API endpoints."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = structlog.get_logger(__name__)
router = APIRouter()


class CreateSpendingRequest(BaseModel):
    """Request model for creating spending entry."""

    amount: float
    merchant: str
    description: str
    category: str = "Miscellaneous"
    payment_method: str = "Cash"


class ProcessTextRequest(BaseModel):
    """Request model for processing text."""

    text: str
    language: str = "en"


@router.get("/")
async def get_spending_entries(request: Request) -> dict[str, Any]:
    """Get all spending entries."""
    try:
        if (
            not hasattr(request.app.state, "spending_repository")
            or not request.app.state.spending_repository
        ):
            raise HTTPException(status_code=503, detail="Repository not available")

        repository = request.app.state.spending_repository
        entries = await repository.find_all(limit=10)
        total_count = await repository.count_total()

        return {
            "entries": [entry.to_dict() for entry in entries],
            "total_count": total_count,
            "status": "success",
        }

    except Exception as e:
        logger.error("Failed to get spending entries", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/")
async def create_spending_entry(
    request: Request, spending_data: CreateSpendingRequest
) -> dict[str, Any]:
    """Create a new spending entry."""
    try:
        from datetime import datetime

        from ....application.commands.spending_commands import (
            CreateSpendingEntryCommand,
            CreateSpendingEntryCommandHandler,
        )

        if (
            not hasattr(request.app.state, "spending_repository")
            or not request.app.state.spending_repository
        ):
            raise HTTPException(status_code=503, detail="Repository not available")

        repository = request.app.state.spending_repository

        # Create command
        command = CreateSpendingEntryCommand(
            amount=spending_data.amount,
            currency="THB",  # Default to Thai Baht
            merchant=spending_data.merchant,
            description=spending_data.description,
            transaction_date=datetime.utcnow(),
            category=spending_data.category,
            payment_method=spending_data.payment_method,
        )

        # Handle command
        handler = CreateSpendingEntryCommandHandler(repository)
        result = await handler.handle(command)

        if result.is_failure():
            raise HTTPException(status_code=400, detail=result.message)

        return {
            "message": result.message,
            "entry_id": result.data["entry_id"],
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create spending entry", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/process/text")
async def process_text(
    request: Request, text_data: ProcessTextRequest
) -> dict[str, Any]:
    """Process natural language text into spending entry."""
    try:
        if (
            not hasattr(request.app.state, "llama_client")
            or not request.app.state.llama_client
        ):
            raise HTTPException(status_code=503, detail="AI service not available")

        llama_client = request.app.state.llama_client

        # Use Llama to parse the text
        result = await llama_client.parse_spending_text(
            text=text_data.text, language=text_data.language
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400, detail=result.get("error", "Failed to process text")
            )

        parsed_data = result["parsed_data"]

        # Create spending entry from parsed data
        from datetime import datetime

        from ....application.commands.spending_commands import (
            CreateSpendingEntryCommand,
            CreateSpendingEntryCommandHandler,
        )

        repository = request.app.state.spending_repository

        command = CreateSpendingEntryCommand(
            amount=parsed_data.get("amount", 0.0),
            currency=parsed_data.get("currency", "THB"),
            merchant=parsed_data.get("merchant", "Unknown Merchant"),
            description=parsed_data.get("description", text_data.text),
            transaction_date=datetime.utcnow(),
            category=parsed_data.get("category", "Miscellaneous"),
            payment_method=parsed_data.get("payment_method", "Cash"),
            confidence=parsed_data.get("confidence", 0.7),
            processing_method="llama_direct",
            raw_text=text_data.text,
        )

        handler = CreateSpendingEntryCommandHandler(repository)
        create_result = await handler.handle(command)

        if create_result.is_failure():
            raise HTTPException(status_code=400, detail=create_result.message)

        return {
            "message": "Text processed and spending entry created",
            "entry_id": create_result.data["entry_id"],
            "parsed_data": parsed_data,
            "confidence": parsed_data.get("confidence", 0.7),
            "processing_time_ms": result.get("processing_time_ms", 0),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process text", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
