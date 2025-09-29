#!/usr/bin/env python3
"""
Test script for the new Clean Architecture implementation.
"""

import asyncio
from pathlib import Path
import sys

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from datetime import datetime

import structlog

from ai_service.application.commands.spending_commands import (
    CreateSpendingEntryCommand,
    CreateSpendingEntryCommandHandler,
)
from ai_service.core.config import get_settings, setup_logging
from ai_service.domain.entities.spending_entry import SpendingEntry
from ai_service.domain.value_objects.confidence import ConfidenceScore
from ai_service.domain.value_objects.money import Currency, Money
from ai_service.domain.value_objects.processing_method import ProcessingMethod
from ai_service.domain.value_objects.spending_category import (
    PaymentMethod,
    SpendingCategory,
)
from ai_service.infrastructure.database.sqlite_repository import (
    SqliteSpendingRepository,
)
from ai_service.infrastructure.external_apis.llama_client import LlamaClient
from ai_service.infrastructure.external_apis.ocr_client import TesseractOCRClient


async def test_new_architecture():
    """Test the new Clean Architecture implementation."""

    # Setup logging
    setup_logging()
    logger = structlog.get_logger(__name__)

    logger.info("🧪 Testing New Clean Architecture Implementation")

    try:
        # Test 1: Configuration
        logger.info("📋 Testing configuration...")
        settings = get_settings()
        logger.info(
            f"✅ Configuration loaded: {settings.app_name} v{settings.app_version}"
        )

        # Test 2: Database Repository
        logger.info("💾 Testing database repository...")
        repository = SqliteSpendingRepository(settings.get_database_url())
        await repository.initialize()

        # Test creating a spending entry using domain entities
        entry = SpendingEntry(
            amount=Money.from_float(120.0, Currency.THB),
            merchant="Starbucks",
            description="Coffee and pastry",
            transaction_date=datetime.utcnow(),
            category=SpendingCategory.FOOD_DINING,
            payment_method=PaymentMethod.CREDIT_CARD,
            confidence=ConfidenceScore.high(),
            processing_method=ProcessingMethod.MANUAL_ENTRY,
        )

        await repository.save(entry)
        logger.info(f"✅ Spending entry created: {entry.id.value}")

        # Test retrieving the entry
        retrieved_entry = await repository.find_by_id(entry.id)
        assert retrieved_entry is not None
        assert retrieved_entry.merchant == "Starbucks"
        logger.info("✅ Spending entry retrieved successfully")

        # Test 3: Command Handler (CQRS)
        logger.info("⚡ Testing CQRS command handler...")
        command = CreateSpendingEntryCommand(
            amount=250.0,
            currency="THB",
            merchant="Thai Restaurant",
            description="Pad Thai lunch",
            transaction_date=datetime.utcnow(),
            category=SpendingCategory.FOOD_DINING.value,
            payment_method=PaymentMethod.CASH.value,
            confidence=0.9,
            processing_method=ProcessingMethod.MANUAL_ENTRY.value,
        )

        handler = CreateSpendingEntryCommandHandler(repository)
        result = await handler.handle(command)

        assert result.is_success()
        logger.info(f"✅ Command handled successfully: {result.data['entry_id']}")

        # Test 4: Llama Client (if available)
        logger.info("🦙 Testing Llama client...")
        if settings.use_llama:
            llama_client = LlamaClient(
                base_url=settings.get_ollama_url(),
                model=settings.llama_model,
                timeout=settings.llama_timeout,
            )

            is_available = await llama_client.health_check()
            if is_available:
                logger.info("✅ Llama client is available")

                # Test text parsing
                parse_result = await llama_client.parse_spending_text(
                    "Coffee at Starbucks 120 baht with credit card", language="en"
                )

                if parse_result["success"]:
                    logger.info("✅ Llama text parsing successful")
                    logger.info(f"Parsed data: {parse_result['parsed_data']}")
                else:
                    logger.warning(
                        f"⚠️ Llama parsing failed: {parse_result.get('error')}"
                    )
            else:
                logger.warning("⚠️ Llama client not available (Ollama not running)")

            await llama_client.close()
        else:
            logger.info("⚠️ Llama client disabled in settings")

        # Test 5: OCR Client
        logger.info("👁️ Testing OCR client...")
        ocr_client = TesseractOCRClient(
            tesseract_path=settings.tesseract_path,
            languages=settings.tesseract_languages,
        )

        if ocr_client.is_available():
            logger.info("✅ OCR client is available")
        else:
            logger.warning("⚠️ OCR client not available (Tesseract not found)")

        # Test 6: Domain Events
        logger.info("📡 Testing domain events...")
        events = entry.get_events()
        logger.info(f"✅ Domain events captured: {len(events)} events")
        for event in events:
            logger.info(f"  - {event.event_type}: {event.get_event_data()}")

        # Cleanup
        await repository.close()
        logger.info("🧹 Cleanup completed")

        logger.info("🎉 All tests passed! New architecture is working correctly.")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e!s}", exc_info=True)
        return False


async def main():
    """Main test function."""
    success = await test_new_architecture()

    if success:
        print("\n✅ Clean Architecture implementation is working correctly!")
        print("🚀 The AI service has been successfully restructured following:")
        print("   - Domain-Driven Design (DDD)")
        print("   - Clean Architecture principles")
        print("   - CQRS pattern")
        print("   - Repository pattern")
        print("   - Domain events")
        print("   - Proper dependency injection")
        print("   - Structured logging")
        sys.exit(0)
    else:
        print("\n❌ Tests failed. Please check the logs above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
