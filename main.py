"""
Ultra Ultimate Add Spending AI Microservice
FastAPI service for OCR, NLP, and AI-powered spending entry parsing
Supports local processing with OpenAI fallback for cost efficiency
"""

from contextlib import asynccontextmanager
from datetime import datetime
import logging
from typing import Any, Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# Request Models
class NLPParseRequest(BaseModel):
    text: str
    language: Optional[str] = None
    use_local_only: bool = True


class TextProcessingRequest(BaseModel):
    text: str
    language: Optional[str] = None
    use_ai_fallback: bool = True
    context: Optional[dict[str, Any]] = None


class BatchProcessingRequest(BaseModel):
    data: list[dict[str, Any]]
    use_ai_enhancement: bool = False


class SpendingAnalysisRequest(BaseModel):
    entries: list[dict[str, Any]]  # Will be converted to SpendingEntry
    analysis_type: str = "comprehensive"


# Import our AI processing modules
from config.settings import get_settings
from models.spending_models import AIAnalysis, NLPResult, OCRResult, SpendingEntry
from services.cache_service import CacheService
from services.database_service import database_service
from services.nlp_service import NLPService
from services.ocr_service import OCRService
from utils.image_utils import preprocess_image, validate_image
from utils.text_utils import clean_text, detect_language

# Import AI services conditionally
try:
    from services.llama_service_enhanced import EnhancedLlamaService

    LLAMA_SERVICE_AVAILABLE = True
except ImportError:
    EnhancedLlamaService = None
    LLAMA_SERVICE_AVAILABLE = False

try:
    from services.ai_service import AIService

    OPENAI_SERVICE_AVAILABLE = True
except ImportError:
    AIService = None
    OPENAI_SERVICE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
services = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown"""
    settings = get_settings()

    # Initialize services
    services["cache"] = CacheService(settings.redis_url)
    services["ocr"] = OCRService(settings)
    services["nlp"] = NLPService(settings)
    services["database"] = database_service

    # Initialize database
    await database_service.initialize()

    # Initialize AI services (prioritize Llama4)
    services["ai"] = None

    if LLAMA_SERVICE_AVAILABLE and getattr(settings, "use_llama", True):
        services["ai"] = EnhancedLlamaService(settings)
        logger.info("🦙 Primary AI service: Enhanced Llama4 via Ollama")
    elif OPENAI_SERVICE_AVAILABLE and settings.openai_api_key:
        services["ai"] = AIService(settings)
        logger.info("🤖 Fallback AI service: OpenAI GPT")
    else:
        logger.info("⚠️ No AI service available - using local NLP only")

    logger.info("🚀 AI Microservice started successfully!")
    yield

    # Cleanup
    await services["cache"].close()
    await services["database"].close()
    logger.info("🔄 AI Microservice shutdown complete")


app = FastAPI(
    title="Ultra Ultimate Add Spending AI Service",
    description="AI-powered OCR, NLP, and spending entry parsing service",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:4000",
    ],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    ai_status = "disabled"
    ai_type = "none"

    if services["ai"]:
        if isinstance(services["ai"], EnhancedLlamaService):
            ai_type = "enhanced_llama4"
            # Check if Ollama is actually running
            try:
                if hasattr(services["ai"], "_check_ollama_connection"):
                    ollama_available = await services["ai"]._check_ollama_connection()
                    ai_status = "ready" if ollama_available else "ollama_offline"
                else:
                    ai_status = "ready"
            except:
                ai_status = "error"
        elif isinstance(services["ai"], AIService):
            ai_type = "openai"
            ai_status = (
                "ready" if services["ai"].settings.openai_api_key else "no_api_key"
            )

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "ocr": "ready",
            "nlp": "ready",
            "ai": ai_status,
            "ai_type": ai_type,
            "cache": "ready",
        },
    }


@app.get("/ai/status")
async def get_ai_status():
    """Get detailed AI service status"""
    if not services["ai"]:
        return {
            "ai_available": False,
            "ai_type": "none",
            "message": "No AI service configured",
        }

    ai_info = {
        "ai_available": True,
        "ai_type": "enhanced_llama4"
        if isinstance(services["ai"], EnhancedLlamaService)
        else "openai",
    }

    if isinstance(services["ai"], EnhancedLlamaService):
        try:
            model_info = await services["ai"].get_model_info()
            ai_info.update(model_info)
        except Exception as e:
            ai_info["error"] = str(e)

    return ai_info


# OCR Processing Endpoints
@app.post("/ocr/process", response_model=OCRResult)
async def process_image_ocr(
    file: UploadFile = File(...),
    language: str = "eng+tha",
    confidence_threshold: float = 0.7,
):
    """
    Process image with OCR to extract text
    Supports Thai and English languages
    """
    try:
        # Validate image
        if not validate_image(file):
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Read and preprocess image
        image_bytes = await file.read()
        processed_image = preprocess_image(image_bytes)

        # Check cache first
        cache_key = f"ocr:{hash(image_bytes)}:{language}"
        cached_result = await services["cache"].get(cache_key)
        if cached_result:
            logger.info("📋 OCR result served from cache")
            return OCRResult(**cached_result)

        # Process with OCR
        ocr_service = services["ocr"]
        result = await ocr_service.extract_text(processed_image, language)

        # Cache result if confidence is high
        if result.confidence >= confidence_threshold:
            await services["cache"].set(cache_key, result.dict(), ttl=3600)

        logger.info(f"📸 OCR processed with {result.confidence:.2f} confidence")
        return result

    except Exception as e:
        logger.error(f"❌ OCR processing failed: {e!s}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {e!s}")


# NLP Processing Endpoints
@app.post("/nlp/parse", response_model=NLPResult)
async def parse_text_nlp(request: NLPParseRequest):
    """
    Parse text using local NLP patterns with AI fallback
    Cost-efficient approach: local first, AI only if needed
    """
    try:
        # Clean and detect language
        clean_text_input = clean_text(request.text)
        language = request.language
        if not language:
            language = detect_language(clean_text_input)

        # Check cache first
        cache_key = f"nlp:{hash(clean_text_input)}:{language}"
        cached_result = await services["cache"].get(cache_key)
        if cached_result:
            logger.info("📋 NLP result served from cache")
            return NLPResult(**cached_result)

        # Try local NLP first
        nlp_service = services["nlp"]
        result = await nlp_service.parse_spending_text(clean_text_input, language)

        # If confidence is low and AI fallback is allowed
        if result.confidence < 0.7 and not request.use_local_only and services["ai"]:
            logger.info("🤖 Local confidence low, trying AI fallback...")
            ai_service = services["ai"]
            ai_result = await ai_service.enhance_nlp_result(
                clean_text_input, result, language
            )
            result = ai_result
        elif result.confidence < 0.7 and not request.use_local_only:
            logger.warning("⚠️ Low confidence but AI service not available")

        # Cache result
        await services["cache"].set(cache_key, result.dict(), ttl=1800)

        logger.info(f"🧠 NLP parsed with {result.confidence:.2f} confidence")
        return result

    except Exception as e:
        logger.error(f"❌ NLP parsing failed: {e!s}")
        raise HTTPException(status_code=500, detail=f"NLP parsing failed: {e!s}")


# Combined OCR + NLP Endpoint (The Ultimate Feature)
@app.post("/process/receipt", response_model=SpendingEntry)
async def process_receipt_complete(
    file: UploadFile = File(...),
    language: str = "eng+tha",
    use_ai_fallback: bool = True,
    confidence_threshold: float = 0.8,
):
    """
    Ultimate receipt processing: OCR + NLP + AI enhancement
    This is the main endpoint for the "Add Spending" photo feature
    """
    try:
        logger.info("🚀 Starting complete receipt processing...")

        # Step 1: OCR Processing
        ocr_result = await process_image_ocr(file, language, confidence_threshold)

        # Step 2: NLP Processing
        nlp_result = await parse_text_nlp(
            ocr_result.text, language, use_local_only=not use_ai_fallback
        )

        # Step 3: AI Enhancement (if needed and allowed)
        final_result = nlp_result
        if (
            use_ai_fallback
            and nlp_result.confidence < confidence_threshold
            and services["ai"]
        ):
            logger.info("🤖 Enhancing with AI...")
            ai_service = services["ai"]
            enhanced_result = await ai_service.create_spending_entry(
                ocr_result, nlp_result, language
            )
            final_result = enhanced_result
        elif use_ai_fallback and nlp_result.confidence < confidence_threshold:
            logger.warning("⚠️ Low confidence but AI service not available")

        # Step 4: Convert to SpendingEntry
        spending_entry = SpendingEntry(
            amount=final_result.amount or 0.0,
            merchant=final_result.merchant or "Unknown Merchant",
            category=final_result.category or "Miscellaneous",
            subcategory=final_result.subcategory,
            description=final_result.description or f"Receipt: {final_result.merchant}",
            date=final_result.date or datetime.utcnow(),
            payment_method=final_result.payment_method,
            confidence=final_result.confidence,
            processing_method="ocr+nlp"
            + (
                "+ai"
                if use_ai_fallback and final_result.confidence < confidence_threshold
                else ""
            ),
            raw_text=ocr_result.text,
        )

        logger.info(
            f"✅ Receipt processed successfully with {spending_entry.confidence:.2f} confidence"
        )
        return spending_entry

    except Exception as e:
        logger.error(f"❌ Complete receipt processing failed: {e!s}")
        raise HTTPException(status_code=500, detail=f"Receipt processing failed: {e!s}")


# Llama4 Direct Text Processing
@app.post("/llama/parse", response_model=NLPResult)
async def parse_with_llama(request: TextProcessingRequest):
    """
    Parse spending text directly with Llama4 (bypassing local NLP)
    For high-accuracy parsing when local NLP is insufficient
    """
    try:
        logger.info("🦙 Direct Llama4 parsing requested...")

        if not services["ai"] or not isinstance(services["ai"], EnhancedLlamaService):
            raise HTTPException(
                status_code=503, detail="Enhanced Llama4 service not available"
            )

        llama_service = services["ai"]
        result = await llama_service.parse_spending_text(
            request.text, request.language or "en", request.context
        )

        logger.info(
            f"✅ Direct Llama4 parsing completed with {result.confidence:.2f} confidence"
        )
        return result

    except Exception as e:
        logger.error(f"❌ Direct Llama4 parsing failed: {e!s}")
        raise HTTPException(status_code=500, detail=f"Llama4 parsing failed: {e!s}")


# Voice/Chat Text Processing
@app.post("/process/text", response_model=SpendingEntry)
async def process_spending_text(request: TextProcessingRequest):
    """
    Process natural language text for spending entries
    Used by voice input and chat input features
    """
    try:
        logger.info("💬 Processing spending text...")

        # Parse with NLP service
        nlp_service = services["nlp"]
        nlp_result = await nlp_service.parse_spending_text(
            request.text, request.language
        )

        # AI enhancement if needed
        if request.use_ai_fallback and nlp_result.confidence < 0.8 and services["ai"]:
            ai_service = services["ai"]
            enhanced_result = await ai_service.enhance_text_parsing(
                request.text, nlp_result, request.language, request.context
            )
            nlp_result = enhanced_result
        elif request.use_ai_fallback and nlp_result.confidence < 0.8:
            logger.warning("⚠️ Low confidence but AI service not available")

        # Convert to SpendingEntry
        spending_entry = SpendingEntry(
            amount=nlp_result.amount or 0.0,
            merchant=nlp_result.merchant or "Text Entry",
            category=nlp_result.category or "Miscellaneous",
            subcategory=nlp_result.subcategory,
            description=nlp_result.description or request.text[:100],
            date=nlp_result.date or datetime.utcnow(),
            payment_method=nlp_result.payment_method,
            confidence=nlp_result.confidence,
            processing_method="nlp"
            + (
                "+ai" if request.use_ai_fallback and nlp_result.confidence < 0.8 else ""
            ),
            raw_text=request.text,
        )

        logger.info(
            f"✅ Text processed successfully with {spending_entry.confidence:.2f} confidence"
        )
        return spending_entry

    except Exception as e:
        logger.error(f"❌ Text processing failed: {e!s}")
        raise HTTPException(status_code=500, detail=f"Text processing failed: {e!s}")


# Batch Processing for File Uploads
@app.post("/process/batch", response_model=list[SpendingEntry])
async def process_batch_data(
    request: BatchProcessingRequest, background_tasks: BackgroundTasks
):
    """
    Process batch data from file uploads (CSV, Excel, JSON)
    Returns processed spending entries
    """
    try:
        logger.info(f"📊 Processing batch of {len(request.data)} entries...")

        results = []
        nlp_service = services["nlp"]

        for idx, row in enumerate(request.data):
            try:
                # Extract text representation of the row
                text_repr = " ".join([f"{k}: {v}" for k, v in row.items() if v])

                # Process with NLP
                nlp_result = await nlp_service.parse_batch_entry(row, text_repr)

                # Convert to SpendingEntry
                spending_entry = SpendingEntry(
                    amount=nlp_result.amount or 0.0,
                    merchant=nlp_result.merchant or f"Import Entry {idx+1}",
                    category=nlp_result.category or "Miscellaneous",
                    subcategory=nlp_result.subcategory,
                    description=nlp_result.description or text_repr[:100],
                    date=nlp_result.date or datetime.utcnow(),
                    payment_method=nlp_result.payment_method,
                    confidence=nlp_result.confidence,
                    processing_method="batch_nlp",
                    raw_text=text_repr,
                )

                results.append(spending_entry)

            except Exception as e:
                logger.warning(f"⚠️ Failed to process batch entry {idx}: {e!s}")
                continue

        # Background task for AI enhancement if requested
        if request.use_ai_enhancement and services["ai"]:
            background_tasks.add_task(enhance_batch_results, results)
        elif request.use_ai_enhancement:
            logger.warning("⚠️ AI enhancement requested but AI service not available")

        logger.info(
            f"✅ Batch processed: {len(results)}/{len(request.data)} entries successful"
        )
        return results

    except Exception as e:
        logger.error(f"❌ Batch processing failed: {e!s}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {e!s}")


# AI Analysis and Insights
@app.post("/analyze/spending", response_model=AIAnalysis)
async def analyze_spending_patterns(request: SpendingAnalysisRequest):
    """
    AI-powered analysis of spending patterns
    Returns insights and recommendations
    """
    try:
        # Convert dict entries to SpendingEntry objects
        entries = [SpendingEntry(**entry) for entry in request.entries]

        logger.info(f"🧠 Analyzing {len(entries)} spending entries...")

        if not services["ai"]:
            raise HTTPException(status_code=503, detail="AI service not available")

        ai_service = services["ai"]
        analysis = await ai_service.analyze_spending_patterns(
            entries, request.analysis_type
        )

        logger.info("✅ Spending analysis completed")
        return analysis

    except Exception as e:
        logger.error(f"❌ Spending analysis failed: {e!s}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e!s}")


# Utility Endpoints
@app.get("/categories/suggest")
async def suggest_categories(merchant: str, amount: float, description: str = ""):
    """Suggest spending categories based on merchant and context"""
    try:
        nlp_service = services["nlp"]
        suggestions = await nlp_service.suggest_categories(
            merchant, amount, description
        )
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/merchants/normalize")
async def normalize_merchant_name(name: str):
    """Normalize and clean merchant names"""
    try:
        nlp_service = services["nlp"]
        normalized = await nlp_service.normalize_merchant(name)
        return {"original": name, "normalized": normalized}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Database Endpoints
@app.post("/spending/store")
async def store_spending_entry(entry: SpendingEntry):
    """Store a spending entry in the database"""
    try:
        success = await services["database"].store_spending_entry(entry)
        if success:
            return {
                "success": True,
                "message": "Entry stored successfully",
                "id": entry.id,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to store entry")
    except Exception as e:
        logger.error(f"❌ Failed to store spending entry: {e!s}")
        raise HTTPException(status_code=500, detail=f"Storage failed: {e!s}")


@app.get("/spending/entries")
async def get_spending_entries(
    limit: int = 100,
    offset: int = 0,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """Get spending entries with filtering"""
    try:
        entries = await services["database"].get_spending_entries(
            limit=limit,
            offset=offset,
            category=category,
            date_from=date_from,
            date_to=date_to,
        )
        return {"entries": entries, "count": len(entries)}
    except Exception as e:
        logger.error(f"❌ Failed to get spending entries: {e!s}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {e!s}")


@app.get("/spending/entries/{entry_id}")
async def get_spending_entry(entry_id: str):
    """Get a specific spending entry by ID"""
    try:
        entry = await services["database"].get_spending_entry(entry_id)
        if entry:
            return entry
        else:
            raise HTTPException(status_code=404, detail="Entry not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get spending entry {entry_id}: {e!s}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {e!s}")


@app.put("/spending/entries/{entry_id}")
async def update_spending_entry(entry_id: str, updates: dict[str, Any]):
    """Update a spending entry"""
    try:
        success = await services["database"].update_spending_entry(entry_id, updates)
        if success:
            return {"success": True, "message": "Entry updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Entry not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update spending entry {entry_id}: {e!s}")
        raise HTTPException(status_code=500, detail=f"Update failed: {e!s}")


@app.delete("/spending/entries/{entry_id}")
async def delete_spending_entry(entry_id: str):
    """Delete a spending entry"""
    try:
        success = await services["database"].delete_spending_entry(entry_id)
        if success:
            return {"success": True, "message": "Entry deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Entry not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete spending entry {entry_id}: {e!s}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {e!s}")


@app.get("/spending/statistics")
async def get_spending_statistics():
    """Get database statistics"""
    try:
        stats = await services["database"].get_statistics()
        return stats
    except Exception as e:
        logger.error(f"❌ Failed to get statistics: {e!s}")
        raise HTTPException(status_code=500, detail=f"Statistics failed: {e!s}")


@app.get("/spending/logs/{entry_id}")
async def get_processing_logs(entry_id: str):
    """Get processing logs for an entry"""
    try:
        logs = await services["database"].get_processing_logs(entry_id)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"❌ Failed to get processing logs: {e!s}")
        raise HTTPException(status_code=500, detail=f"Log retrieval failed: {e!s}")


# Enhanced processing endpoints with database storage
@app.post("/process/text/store", response_model=SpendingEntry)
async def process_and_store_spending_text(request: TextProcessingRequest):
    """Process spending text and automatically store in database"""
    try:
        # Process the text
        spending_entry = await process_spending_text(request)

        # Store in database
        success = await services["database"].store_spending_entry(spending_entry)
        if success:
            logger.info(f"✅ Processed and stored spending entry: {spending_entry.id}")
        else:
            logger.warning(f"⚠️ Failed to store processed entry: {spending_entry.id}")

        return spending_entry

    except Exception as e:
        logger.error(f"❌ Process and store failed: {e!s}")
        raise HTTPException(status_code=500, detail=f"Process and store failed: {e!s}")


@app.post("/process/receipt/store", response_model=SpendingEntry)
async def process_and_store_receipt(
    file: UploadFile = File(...),
    language: str = "eng+tha",
    use_ai_fallback: bool = True,
    confidence_threshold: float = 0.8,
):
    """Process receipt image and automatically store in database"""
    try:
        # Process the receipt
        spending_entry = await process_receipt_complete(
            file, language, use_ai_fallback, confidence_threshold
        )

        # Store in database
        success = await services["database"].store_spending_entry(spending_entry)
        if success:
            logger.info(f"✅ Processed and stored receipt entry: {spending_entry.id}")
        else:
            logger.warning(f"⚠️ Failed to store processed receipt: {spending_entry.id}")

        return spending_entry

    except Exception as e:
        logger.error(f"❌ Process and store receipt failed: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Process and store receipt failed: {e!s}"
        )


# Background task for batch enhancement
async def enhance_batch_results(results: list[SpendingEntry]):
    """Background task to enhance batch results with AI"""
    try:
        if not services["ai"]:
            logger.warning("⚠️ AI service not available for batch enhancement")
            return

        ai_service = services["ai"]
        for entry in results:
            if entry.confidence < 0.8:
                enhanced = await ai_service.enhance_spending_entry(entry)
                # Update the entry and store in database
                entry.confidence = enhanced.confidence
                entry.category = enhanced.category or entry.category
                entry.subcategory = enhanced.subcategory or entry.subcategory

                # Update in database
                await services["database"].update_spending_entry(
                    entry.id,
                    {
                        "confidence": entry.confidence,
                        "category": entry.category,
                        "subcategory": entry.subcategory,
                    },
                )
    except Exception as e:
        logger.error(f"❌ Background enhancement failed: {e!s}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True, log_level="info")
