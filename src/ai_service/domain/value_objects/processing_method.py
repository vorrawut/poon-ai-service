"""Processing method value object for tracking how spending entries were processed."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ProcessingMethod(str, Enum):
    """Methods used to process spending entries."""

    # Primary processing methods
    MANUAL_ENTRY = "manual_entry"
    OCR_PROCESSING = "ocr_processing"
    NLP_PARSING = "nlp_parsing"
    VOICE_INPUT = "voice_input"
    BATCH_IMPORT = "batch_import"

    # AI enhancement methods
    AI_ENHANCED = "ai_enhanced"
    LLAMA_DIRECT = "llama_direct"
    LLAMA_ENHANCED = "llama_enhanced"
    OPENAI_ENHANCED = "openai_enhanced"

    # Combined methods
    OCR_NLP = "ocr_nlp"
    OCR_NLP_AI = "ocr_nlp_ai"
    NLP_AI = "nlp_ai"
    VOICE_AI = "voice_ai"

    # Template and quick methods
    TEMPLATE_BASED = "template_based"
    QUICK_ACTION = "quick_action"

    def is_ai_enhanced(self) -> bool:
        """Check if processing method uses AI enhancement."""
        ai_methods = {
            self.LLAMA_DIRECT,
            self.LLAMA_ENHANCED,
            self.OPENAI_ENHANCED,
            self.OCR_NLP_AI,
            self.NLP_AI,
            self.VOICE_AI,
        }
        return self in ai_methods

    def is_local_processing(self) -> bool:
        """Check if processing is done locally (no external APIs)."""
        local_methods = {
            self.MANUAL_ENTRY,
            self.OCR_PROCESSING,
            self.NLP_PARSING,
            self.VOICE_INPUT,
            self.BATCH_IMPORT,
            self.LLAMA_DIRECT,
            self.LLAMA_ENHANCED,
            self.OCR_NLP,
            self.TEMPLATE_BASED,
            self.QUICK_ACTION,
        }
        return self in local_methods

    def is_automated(self) -> bool:
        """Check if processing is fully automated (no manual input)."""
        automated_methods = {
            self.OCR_PROCESSING,
            self.NLP_PARSING,
            self.BATCH_IMPORT,
            self.LLAMA_DIRECT,
            self.LLAMA_ENHANCED,
            self.OPENAI_ENHANCED,
            self.OCR_NLP,
            self.OCR_NLP_AI,
            self.NLP_AI,
        }
        return self in automated_methods

    def get_display_name(self) -> str:
        """Get human-readable display name."""
        display_names = {
            self.MANUAL_ENTRY: "Manual Entry",
            self.OCR_PROCESSING: "OCR Processing",
            self.NLP_PARSING: "NLP Parsing",
            self.VOICE_INPUT: "Voice Input",
            self.BATCH_IMPORT: "Batch Import",
            self.LLAMA_DIRECT: "Llama4 Direct",
            self.LLAMA_ENHANCED: "Llama4 Enhanced",
            self.OPENAI_ENHANCED: "OpenAI Enhanced",
            self.OCR_NLP: "OCR + NLP",
            self.OCR_NLP_AI: "OCR + NLP + AI",
            self.NLP_AI: "NLP + AI",
            self.VOICE_AI: "Voice + AI",
            self.TEMPLATE_BASED: "Template Based",
            self.QUICK_ACTION: "Quick Action",
        }
        return display_names.get(self, self.value)

    def get_thai_name(self) -> str:
        """Get Thai display name."""
        thai_names = {
            self.MANUAL_ENTRY: "กรอกข้อมูลเอง",
            self.OCR_PROCESSING: "อ่านข้อความจากภาพ",
            self.NLP_PARSING: "วิเคราะห์ภาษาธรรมชาติ",
            self.VOICE_INPUT: "ป้อนข้อมูลด้วยเสียง",
            self.BATCH_IMPORT: "นำเข้าข้อมูลจำนวนมาก",
            self.LLAMA_DIRECT: "AI ประมวลผลโดยตรง",
            self.LLAMA_ENHANCED: "AI ปรับปรุงข้อมูล",
            self.OPENAI_ENHANCED: "OpenAI ปรับปรุง",
            self.OCR_NLP: "อ่านภาพ + วิเคราะห์ภาษา",
            self.OCR_NLP_AI: "อ่านภาพ + วิเคราะห์ + AI",
            self.NLP_AI: "วิเคราะห์ภาษา + AI",
            self.VOICE_AI: "เสียง + AI",
            self.TEMPLATE_BASED: "ใช้แม่แบบ",
            self.QUICK_ACTION: "ป้อนข้อมูลด่วน",
        }
        return thai_names.get(self, self.get_display_name())


@dataclass(frozen=True)
class ProcessingMetadata:
    """Metadata about how a spending entry was processed."""

    method: ProcessingMethod
    processing_time_ms: int | None = None
    model_used: str | None = None
    api_calls_made: int = 0
    cost_incurred: float = 0.0
    errors_encountered: list[str] | None = None

    def __post_init__(self) -> None:
        """Validate processing metadata."""
        if self.processing_time_ms is not None and self.processing_time_ms < 0:
            msg = "Processing time cannot be negative"
            raise ValueError(msg)

        if self.api_calls_made < 0:
            msg = "API calls count cannot be negative"
            raise ValueError(msg)

        if self.cost_incurred < 0:
            msg = "Cost cannot be negative"
            raise ValueError(msg)

    def is_fast(self) -> bool:
        """Check if processing was fast (< 1000ms)."""
        return self.processing_time_ms is not None and self.processing_time_ms < 1000

    def is_free(self) -> bool:
        """Check if processing was free (no cost)."""
        return self.cost_incurred == 0.0

    def has_errors(self) -> bool:
        """Check if processing encountered errors."""
        return self.errors_encountered is not None and len(self.errors_encountered) > 0

    def get_performance_rating(self) -> str:
        """Get performance rating based on speed and cost."""
        if self.is_fast() and self.is_free():
            return "Excellent"
        elif self.is_fast():
            return "Good"
        elif self.is_free():
            return "Economical"
        else:
            return "Standard"

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if not isinstance(other, ProcessingMetadata):
            return False
        return (
            self.method == other.method
            and self.processing_time_ms == other.processing_time_ms
            and self.model_used == other.model_used
            and self.api_calls_made == other.api_calls_made
            and abs(self.cost_incurred - other.cost_incurred) < 1e-6
            and self.errors_encountered == other.errors_encountered
        )
