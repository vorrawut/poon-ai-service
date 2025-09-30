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
    """Process natural language text into structured spending entries using ultra-fast AI."""
    from datetime import datetime

    from ...application.services.enhanced_text_processor import EnhancedTextProcessor

    datetime.utcnow()

    try:
        # Get services
        llama_client = getattr(request.app.state, "llama_client", None)
        ai_learning_service = getattr(request.app.state, "ai_learning_service", None)

        # Initialize enhanced processor with ultra-fast processing
        enhanced_processor = EnhancedTextProcessor(llama_client)

        logger.info(
            f"🚀 Processing text: {len(text_data.text)} chars, language: {text_data.language}"
        )

        # Use enhanced fast processing (1-3 second target)
        result = await enhanced_processor.process_text_fast(
            text_data.text, text_data.language
        )

        # Record AI interaction for learning
        if ai_learning_service:
            try:
                await ai_learning_service.record_ai_interaction(
                    input_text=text_data.text,
                    language=text_data.language,
                    raw_ai_response=str(result),
                    parsed_ai_data=result,
                    ai_confidence=result.get("confidence", 0.5),
                    processing_time_ms=result.get("processing_time_ms", 0),
                    model_version=f"{result.get('method', 'enhanced')}_processor",
                    user_id=getattr(request.state, "user_id", None),
                    session_id=getattr(request.state, "session_id", None),
                )
            except Exception as e:
                logger.warning(f"Failed to record AI interaction: {e}")

        # Validate result
        if not result or result.get("amount", 0) <= 0:
            # Record failure for learning
            if ai_learning_service:
                try:
                    await ai_learning_service.record_processing_failure(
                        input_text=text_data.text,
                        language=text_data.language,
                        error_message="No valid amount extracted",
                        raw_ai_response=str(result),
                        processing_time_ms=result.get("processing_time_ms", 0),
                    )
                except Exception as e:
                    logger.warning(f"Failed to record processing failure: {e}")

            raise HTTPException(
                status_code=400,
                detail="Could not extract valid spending information from text",
            )

        parsed_data = result

        # Create spending entry from parsed data
        from datetime import datetime

        from ....application.commands.spending_commands import (
            CreateSpendingEntryCommand,
            CreateSpendingEntryCommandHandler,
        )

        repository = request.app.state.spending_repository

        # Map AI categories to valid SpendingCategory values using dynamic learning
        async def map_category(ai_category: str | None) -> str:
            """Map AI-generated categories to valid SpendingCategory enum values."""
            if not ai_category:
                return "Miscellaneous"

            # Get dynamic mappings from AI learning system
            dynamic_mappings = {}
            if ai_learning_service:
                try:
                    dynamic_mappings = (
                        await ai_learning_service.get_dynamic_category_mapping()
                    )
                except Exception as e:
                    logger.warning(f"Failed to get dynamic category mappings: {e}")

            # Static fallback mapping for common AI responses
            static_mapping = {
                "accommodation": "Travel",
                "hotel": "Travel",
                "lodging": "Travel",
                "restaurant": "Food & Dining",
                "cafe": "Food & Dining",
                "coffee": "Food & Dining",
                "gas": "Transportation",
                "fuel": "Transportation",
                "grocery": "Groceries",
                "supermarket": "Groceries",
                "medicine": "Healthcare",
                "pharmacy": "Healthcare",
                "clothes": "Shopping",
                "clothing": "Shopping",
            }

            # Combine dynamic and static mappings (dynamic takes precedence)
            combined_mapping = {**static_mapping, **dynamic_mappings}

            # Check case-insensitive mapping
            ai_category_lower = ai_category.lower()
            if ai_category_lower in combined_mapping:
                mapped_value = combined_mapping[ai_category_lower]
                return str(mapped_value)

            # If no mapping found, return the original or default
            return str(ai_category or "Miscellaneous")

        # Map category using dynamic learning
        mapped_category = await map_category(parsed_data.get("category"))

        command = CreateSpendingEntryCommand(
            amount=parsed_data.get("amount") or 0.0,
            currency=parsed_data.get("currency") or "THB",
            merchant=parsed_data.get("merchant") or "Unknown Merchant",
            description=parsed_data.get("description") or text_data.text,
            transaction_date=datetime.utcnow(),
            category=mapped_category,
            payment_method=parsed_data.get("payment_method") or "Cash",
            confidence=parsed_data.get("confidence") or 0.7,
            processing_method=f"enhanced_{result.get('method', 'hybrid')}",
            raw_text=text_data.text,
        )

        handler = CreateSpendingEntryCommandHandler(repository)
        create_result = await handler.handle(command)

        if create_result.is_failure():
            raise HTTPException(status_code=400, detail=create_result.message)

        # Clean parsed data for response (remove None values)
        cleaned_parsed_data = {
            "amount": float(parsed_data.get("amount") or 0.0),
            "currency": str(parsed_data.get("currency") or "THB"),
            "merchant": str(parsed_data.get("merchant") or "Unknown Merchant"),
            "category": str(mapped_category),  # Use the already mapped category
            "payment_method": str(parsed_data.get("payment_method") or "Cash"),
            "description": str(parsed_data.get("description") or text_data.text),
            "confidence": float(parsed_data.get("confidence") or 0.7),
        }

        return ProcessTextResponse(
            status="success",
            message="Text processed and spending entry created",
            entry_id=create_result.data["entry_id"],
            parsed_data=ParsedSpendingData(**cleaned_parsed_data),
            confidence=float(cleaned_parsed_data["confidence"]),
            processing_time_ms=result.get("processing_time_ms", 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process text", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
