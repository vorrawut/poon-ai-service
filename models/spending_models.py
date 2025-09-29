"""
Pydantic models for spending entry processing
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ProcessingMethod(str, Enum):
    OCR = "ocr"
    NLP = "nlp"
    OCR_NLP = "ocr+nlp"
    OCR_NLP_AI = "ocr+nlp+ai"
    BATCH_NLP = "batch_nlp"
    VOICE = "voice"
    CHAT = "chat"

class SpendingCategory(str, Enum):
    FOOD_DINING = "Food & Dining"
    TRANSPORTATION = "Transportation"
    GROCERIES = "Groceries"
    SHOPPING = "Shopping"
    ENTERTAINMENT = "Entertainment"
    HEALTHCARE = "Healthcare"
    BILLS_SERVICES = "Bills & Services"
    TRAVEL = "Travel"
    EDUCATION = "Education"
    MISCELLANEOUS = "Miscellaneous"

class PaymentMethod(str, Enum):
    CASH = "Cash"
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    BANK_TRANSFER = "Bank Transfer"
    PROMPTPAY = "PromptPay"
    MOBILE_BANKING = "Mobile Banking"
    DIGITAL_WALLET = "Digital Wallet"
    OTHER = "Other"

class OCRResult(BaseModel):
    """Result from OCR processing"""
    text: str = Field(..., description="Extracted text from image")
    confidence: float = Field(..., ge=0.0, le=1.0, description="OCR confidence score")
    language: str = Field(default="en", description="Detected language")
    processing_time: float = Field(..., description="Processing time in seconds")
    bounding_boxes: Optional[List[Dict[str, Any]]] = Field(default=None, description="Text bounding boxes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class NLPResult(BaseModel):
    """Result from NLP processing"""
    merchant: Optional[str] = Field(default=None, description="Extracted merchant name")
    amount: Optional[float] = Field(default=None, ge=0.0, description="Extracted amount")
    category: Optional[str] = Field(default=None, description="Predicted category")
    subcategory: Optional[str] = Field(default=None, description="Predicted subcategory")
    date: Optional[datetime] = Field(default=None, description="Extracted date")
    payment_method: Optional[str] = Field(default=None, description="Extracted payment method")
    description: Optional[str] = Field(default=None, description="Generated description")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    extraction_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed extraction info")
    reasoning: Optional[str] = Field(default=None, description="AI reasoning for decisions")

class SpendingEntry(BaseModel):
    """Final spending entry result"""
    id: Optional[str] = Field(default=None, description="Entry ID")
    amount: float = Field(..., ge=0.0, description="Spending amount")
    merchant: str = Field(..., description="Merchant name")
    category: str = Field(..., description="Spending category")
    subcategory: Optional[str] = Field(default=None, description="Spending subcategory")
    description: str = Field(..., description="Entry description")
    date: datetime = Field(..., description="Transaction date")
    payment_method: Optional[str] = Field(default=None, description="Payment method used")
    location: Optional[str] = Field(default=None, description="Transaction location")
    tags: List[str] = Field(default_factory=list, description="Entry tags")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    processing_method: str = Field(..., description="How this entry was processed")
    raw_text: Optional[str] = Field(default=None, description="Original raw text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

class AIAnalysis(BaseModel):
    """AI analysis of spending patterns"""
    total_entries: int = Field(..., description="Number of entries analyzed")
    analysis_type: str = Field(..., description="Type of analysis performed")
    insights: List[Dict[str, Any]] = Field(..., description="Generated insights")
    recommendations: List[Dict[str, Any]] = Field(..., description="AI recommendations")
    patterns: Dict[str, Any] = Field(..., description="Detected patterns")
    anomalies: List[Dict[str, Any]] = Field(default_factory=list, description="Detected anomalies")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")

class BatchProcessingRequest(BaseModel):
    """Request for batch processing"""
    data: List[Dict[str, Any]] = Field(..., description="Raw data entries")
    format: str = Field(..., description="Data format (csv, excel, json)")
    mapping: Optional[Dict[str, str]] = Field(default=None, description="Column mapping")
    use_ai_enhancement: bool = Field(default=False, description="Whether to use AI enhancement")

class ProcessingStats(BaseModel):
    """Processing statistics"""
    total_processed: int
    successful: int
    failed: int
    average_confidence: float
    processing_time: float
    method_breakdown: Dict[str, int]

class AIInsight(BaseModel):
    """Individual AI insight"""
    title: str
    description: str
    impact: str  # high/medium/low

class AIRecommendation(BaseModel):
    """AI recommendation"""
    action: str
    reason: str
    potential_savings: float = 0.0

class AIAnomaly(BaseModel):
    """Detected spending anomaly"""
    description: str
    amount: float
    date: str

class AIAnalysis(BaseModel):
    """AI spending analysis result"""
    total_entries: int
    analysis_type: str
    insights: List[AIInsight]
    recommendations: List[AIRecommendation]
    patterns: Dict[str, Any]
    anomalies: List[AIAnomaly]
    confidence: float = Field(..., ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
