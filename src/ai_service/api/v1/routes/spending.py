"""Spending-related API endpoints."""

import structlog
from fastapi import APIRouter, HTTPException, Request, status

from ..schemas.spending import (
    CreateSpendingRequest,
    CreateSpendingResponse,
    ParsedSpendingData,
    ProcessTextRequest,
    ProcessTextResponse,
    SpendingListResponse,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=SpendingListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Spending Entries",
    description="""
    **Retrieve a list of spending entries** with pagination support.

    This endpoint returns spending entries stored in the system, allowing you to:
    - Browse all spending transactions
    - Implement pagination for large datasets
    - Get summary statistics (total count)

    **Features:**
    - **Pagination**: Built-in limit/offset support
    - **Metadata**: Total count and pagination info
    - **Performance**: Optimized queries for large datasets

    **Default Behavior:**
    - Returns up to 10 entries by default
    - Sorted by creation date (newest first)
    - Includes all entry details and metadata

    **Future Enhancements:**
    - Filtering by category, date range, merchant
    - Sorting options (amount, date, merchant)
    - Search functionality
    """,
    responses={
        200: {
            "description": "Spending entries retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Spending entries retrieved successfully",
                        "timestamp": "2024-01-15T12:35:00Z",
                        "data": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "amount": 85.50,
                                "currency": "THB",
                                "merchant": "Central World Food Court",
                                "description": "Lunch with colleagues",
                                "category": "Food & Dining",
                                "payment_method": "Credit Card",
                                "transaction_date": "2024-01-15T12:30:00Z",
                                "created_at": "2024-01-15T12:35:00Z",
                                "updated_at": "2024-01-15T12:35:00Z",
                                "confidence": 0.95,
                                "processing_method": "ai_enhanced",
                            }
                        ],
                        "entries": [],
                        "total_count": 1,
                        "has_more": False,
                        "pagination": {"limit": 10, "offset": 0, "total": 1},
                    }
                }
            },
        },
        503: {
            "description": "Service unavailable - database not accessible",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Repository not available",
                        "error_code": "SERVICE_UNAVAILABLE",
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Database connection failed",
                        "error_code": "INTERNAL_ERROR",
                    }
                }
            },
        },
    },
    tags=["Spending"],
)
async def get_spending_entries(request: Request) -> SpendingListResponse:
    """Retrieve a paginated list of spending entries with metadata."""
    try:
        if (
            not hasattr(request.app.state, "spending_repository")
            or not request.app.state.spending_repository
        ):
            raise HTTPException(status_code=503, detail="Repository not available")

        repository = request.app.state.spending_repository
        entries = await repository.find_all(limit=10)
        total_count = await repository.count_total()

        # Convert entries to response format
        entry_data = [entry.to_dict() for entry in entries]

        return SpendingListResponse(
            status="success",
            message="Spending entries retrieved successfully",
            data=entry_data,
            entries=entry_data,  # For backward compatibility
            total_count=total_count,
            has_more=len(entries) >= 10,  # Simple check for more data
            pagination={"limit": 10, "offset": 0, "total": total_count},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get spending entries", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/",
    response_model=CreateSpendingResponse,
    status_code=status.HTTP_200_OK,
    summary="Create Spending Entry",
    description="""
    **Create a new spending entry** with manual input data.

    This endpoint allows you to manually create spending entries by providing
    transaction details. It's perfect for:
    - Manual expense tracking
    - Importing data from other systems
    - Creating entries when AI processing isn't needed

    **Required Fields:**
    - **amount**: Transaction amount (must be positive)
    - **merchant**: Store or vendor name
    - **description**: Transaction details or notes

    **Optional Fields:**
    - **category**: Spending category (defaults to "Miscellaneous")
    - **payment_method**: How the payment was made (defaults to "Cash")
    - **currency**: Currency code (defaults to "THB")

    **Validation:**
    - Amount must be positive
    - Merchant and description cannot be empty
    - Currency must be valid ISO 4217 code
    - All text fields have length limits

    **Processing:**
    - Automatic timestamp assignment
    - UUID generation for unique identification
    - Data validation and sanitization
    """,
    responses={
        200: {
            "description": "Spending entry created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Spending entry created successfully",
                        "timestamp": "2024-01-15T12:35:00Z",
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "entry_id": "123e4567-e89b-12d3-a456-426614174000",
                    }
                }
            },
        },
        400: {
            "description": "Validation error - invalid input data",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Amount must be positive",
                        "error_code": "VALIDATION_ERROR",
                        "details": {
                            "field": "amount",
                            "value": -10.50,
                            "constraint": "must be greater than 0",
                        },
                    }
                }
            },
        },
        503: {
            "description": "Service unavailable - database not accessible",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Repository not available",
                        "error_code": "SERVICE_UNAVAILABLE",
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Failed to save spending entry",
                        "error_code": "INTERNAL_ERROR",
                    }
                }
            },
        },
    },
    tags=["Spending"],
)
async def create_spending_entry(
    request: Request, spending_data: CreateSpendingRequest
) -> CreateSpendingResponse:
    """Create a new spending entry with manual input data."""
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

        entry_id = result.data["entry_id"]
        return CreateSpendingResponse(
            status="success",
            message=result.message or "Spending entry created successfully",
            id=entry_id,
            entry_id=entry_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create spending entry", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/process/text",
    response_model=ProcessTextResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Text Processing",
    description="""
    **Process natural language text** into structured spending entries using AI.

    This is the **core AI feature** of the service! It uses a local Llama 3.2 model
    to intelligently parse natural language descriptions of spending transactions
    and automatically create structured spending entries.

    **🤖 AI Capabilities:**
    - **Amount Extraction**: Recognizes various currency formats and amounts
    - **Merchant Identification**: Identifies store names and vendors
    - **Category Classification**: Automatically categorizes spending types
    - **Payment Method Detection**: Recognizes payment methods from context
    - **Multi-language Support**: Supports English, Thai, and other languages

    **📝 Input Examples:**
    - "Bought coffee at Starbucks for $5.50"
    - "ซื้อกาแฟที่สตาร์บัคส์ 120 บาท ด้วยบัตรเครดิต"
    - "Paid 25 euros for lunch at Italian restaurant"
    - "Gas station fill-up $45.20 with debit card"

    **🎯 Processing Flow:**
    1. **Text Analysis**: AI analyzes the natural language input
    2. **Data Extraction**: Extracts structured spending information
    3. **Validation**: Validates and normalizes extracted data
    4. **Entry Creation**: Automatically creates a spending entry
    5. **Confidence Scoring**: Provides confidence metrics

    **⚡ Performance:**
    - Typical processing time: 1-3 seconds
    - High accuracy for common spending patterns
    - Confidence scores help identify uncertain extractions

    **🔧 Configuration:**
    - Requires Ollama service to be running
    - Uses Llama 3.2:3b model by default
    - Supports custom language preferences
    """,
    responses={
        200: {
            "description": "Text processed successfully and spending entry created",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Text processed and spending entry created",
                        "timestamp": "2024-01-15T12:35:00Z",
                        "entry_id": "123e4567-e89b-12d3-a456-426614174000",
                        "parsed_data": {
                            "amount": 85.50,
                            "currency": "THB",
                            "merchant": "Central World Food Court",
                            "category": "Food & Dining",
                            "payment_method": "Credit Card",
                            "description": "Lunch with colleagues",
                            "confidence": 0.95,
                        },
                        "confidence": 0.95,
                        "processing_time_ms": 1250,
                    }
                }
            },
        },
        400: {
            "description": "Invalid input or AI processing failed",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Unable to extract spending information from text",
                        "error_code": "AI_PROCESSING_FAILED",
                        "details": {
                            "input_text": "random gibberish text",
                            "reason": "No spending-related information detected",
                        },
                    }
                }
            },
        },
        503: {
            "description": "AI service unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "AI service not available",
                        "error_code": "SERVICE_UNAVAILABLE",
                        "details": {"service": "ollama", "status": "offline"},
                    }
                }
            },
        },
        500: {
            "description": "Internal processing error",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "AI model processing failed",
                        "error_code": "INTERNAL_ERROR",
                    }
                }
            },
        },
    },
    tags=["Spending", "AI Processing"],
)
async def process_text(
    request: Request, text_data: ProcessTextRequest
) -> ProcessTextResponse:
    """Process natural language text into structured spending entries using AI."""
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

        return ProcessTextResponse(
            status="success",
            message="Text processed and spending entry created",
            entry_id=create_result.data["entry_id"],
            parsed_data=ParsedSpendingData(**parsed_data),
            confidence=parsed_data.get("confidence", 0.7),
            processing_time_ms=result.get("processing_time_ms", 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process text", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
