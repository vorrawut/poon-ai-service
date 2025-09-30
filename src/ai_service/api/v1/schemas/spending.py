"""Spending API schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import BaseResponse, IDResponse, PaginatedResponse


class CreateSpendingRequest(BaseModel):
    """Request model for creating a spending entry."""

    amount: float = Field(
        gt=0,
        description="Spending amount (must be positive)",
        examples=[12.50, 1250.00, 99.99],
    )
    merchant: str = Field(
        min_length=1,
        max_length=200,
        description="Merchant or vendor name",
        examples=["Starbucks", "Amazon", "Shell Gas Station", "ร้านอาหารไทย"],
    )
    description: str = Field(
        min_length=1,
        max_length=1000,
        description="Transaction description or notes",
        examples=[
            "Morning coffee",
            "Weekly groceries",
            "Gas for road trip",
            "ซื้อของใช้ในบ้าน",
        ],
    )
    category: str = Field(
        default="Miscellaneous",
        max_length=100,
        description="Spending category",
        examples=["Food & Dining", "Transportation", "Shopping", "Entertainment"],
    )
    payment_method: str = Field(
        default="Cash",
        max_length=50,
        description="Payment method used",
        examples=[
            "Cash",
            "Credit Card",
            "Debit Card",
            "Mobile Payment",
            "Bank Transfer",
        ],
    )
    currency: str = Field(
        default="THB",
        min_length=3,
        max_length=3,
        description="Currency code (ISO 4217)",
        examples=["THB", "USD", "EUR", "JPY"],
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code format."""
        return v.upper()

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "amount": 85.50,
                    "merchant": "Central World Food Court",
                    "description": "Lunch with colleagues",
                    "category": "Food & Dining",
                    "payment_method": "Credit Card",
                    "currency": "THB",
                },
                {
                    "amount": 1200.00,
                    "merchant": "BTS Skytrain",
                    "description": "Monthly transit pass",
                    "category": "Transportation",
                    "payment_method": "Mobile Payment",
                    "currency": "THB",
                },
            ]
        }
    )


class ProcessTextRequest(BaseModel):
    """Request model for processing natural language text."""

    text: str = Field(
        min_length=3,
        max_length=2000,
        description="Natural language text describing a spending transaction",
        examples=[
            "Bought coffee at Starbucks for $5.50",
            "ซื้อกาแฟที่สตาร์บัคส์ 120 บาท ด้วยบัตรเครดิต",
            "Paid 25 euros for lunch at Italian restaurant",
            "Gas station fill-up $45.20 with debit card",
        ],
    )
    language: str = Field(
        default="en",
        min_length=2,
        max_length=5,
        description="Language code for text processing (ISO 639-1)",
        examples=["en", "th", "es", "fr", "de"],
    )

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate and normalize language code."""
        return v.lower()

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text": "Bought lunch at McDonald's for 150 baht with cash",
                    "language": "en",
                },
                {"text": "ซื้อน้ำมันที่ปตท 800 บาท จ่ายด้วยบัตรเครดิต", "language": "th"},
            ]
        }
    )


class ParsedSpendingData(BaseModel):
    """Parsed spending data from AI processing."""

    amount: float = Field(description="Extracted amount")
    currency: str = Field(description="Detected currency")
    merchant: str = Field(description="Identified merchant")
    category: str = Field(description="Suggested category")
    payment_method: str = Field(description="Detected payment method")
    description: str = Field(description="Generated description")
    confidence: float = Field(
        ge=0.0, le=1.0, description="AI confidence score (0.0 to 1.0)"
    )


class SpendingEntryResponse(BaseModel):
    """Response model for a single spending entry."""

    id: UUID = Field(description="Unique entry identifier")
    amount: Decimal = Field(description="Spending amount")
    currency: str = Field(description="Currency code")
    merchant: str = Field(description="Merchant name")
    description: str = Field(description="Transaction description")
    category: str = Field(description="Spending category")
    payment_method: str = Field(description="Payment method")
    transaction_date: datetime = Field(description="Transaction timestamp")
    created_at: datetime = Field(description="Entry creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    confidence: float | None = Field(
        default=None, description="AI processing confidence score"
    )
    processing_method: str | None = Field(
        default=None,
        description="How the entry was processed",
        examples=["manual", "ai_enhanced", "ocr_processed"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
        }
    )


class CreateSpendingResponse(IDResponse):
    """Response for creating a spending entry."""

    entry_id: UUID = Field(description="Created spending entry ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "Spending entry created successfully",
                "timestamp": "2024-01-15T12:35:00Z",
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "entry_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }
    )


class SpendingListResponse(PaginatedResponse[SpendingEntryResponse]):
    """Response for listing spending entries."""

    entries: list[SpendingEntryResponse] = Field(description="List of spending entries")

    model_config = ConfigDict(
        json_schema_extra={
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
    )


class ProcessTextResponse(BaseResponse):
    """Response for text processing endpoint."""

    entry_id: UUID = Field(description="Created spending entry ID")
    parsed_data: ParsedSpendingData = Field(
        description="AI-parsed spending information"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Overall processing confidence"
    )
    processing_time_ms: int = Field(ge=0, description="Processing time in milliseconds")

    model_config = ConfigDict(
        json_schema_extra={
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
    )
