"""Test configuration and fixtures."""

import asyncio
import os

# Add src to Python path
import sys
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

from ai_service.core.config import Settings
from ai_service.domain.entities.spending_entry import SpendingEntry
from ai_service.domain.value_objects.confidence import ConfidenceScore
from ai_service.domain.value_objects.money import Currency, Money
from ai_service.domain.value_objects.processing_method import ProcessingMethod
from ai_service.domain.value_objects.spending_category import (
    PaymentMethod,
    SpendingCategory,
)
from ai_service.infrastructure.database.mongodb_repository import (
    MongoDBSpendingRepository,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings."""
    # Use test MongoDB for tests
    test_settings = Settings()
    test_settings.mongodb_url = "mongodb://localhost:27017"
    test_settings.mongodb_database = "test_spending_db"
    test_settings.mongodb_collection = "test_spending_entries"
    test_settings.mongodb_timeout = 5
    test_settings.environment = "test"
    test_settings.debug = True
    test_settings.use_llama = False  # Disable for tests
    test_settings.use_openai_fallback = False
    return test_settings


@pytest_asyncio.fixture
async def test_repository(
    test_settings: Settings,
) -> AsyncGenerator[MongoDBSpendingRepository, None]:
    """Create a test repository with mock MongoDB implementation."""
    from tests.mocks.mock_mongodb_repository import MockMongoDBSpendingRepository

    repository = MockMongoDBSpendingRepository(test_settings)
    await repository.initialize()
    yield repository
    await repository.close()


@pytest.fixture
def sample_spending_entry() -> SpendingEntry:
    """Create a sample spending entry for testing."""
    return SpendingEntry(
        amount=Money.from_float(120.50, Currency.THB),
        merchant="Test Cafe",
        description="Coffee and pastry",
        transaction_date=datetime(2024, 1, 15, 10, 30, 0),
        category=SpendingCategory.FOOD_DINING,
        payment_method=PaymentMethod.CREDIT_CARD,
        confidence=ConfidenceScore.high(),
        processing_method=ProcessingMethod.MANUAL,
    )


@pytest.fixture
def sample_spending_data() -> dict:
    """Sample spending data for API tests."""
    return {
        "amount": 120.50,
        "merchant": "Test Cafe",
        "description": "Coffee and pastry",
        "category": "Food & Dining",
        "payment_method": "Credit Card",
    }


@pytest.fixture
def temp_db_file() -> Generator[str, None, None]:
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        temp_path = tmp.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


# Override settings for tests
@pytest.fixture(autouse=True)
def _override_get_settings(test_settings: Settings, monkeypatch):
    """Override the get_settings dependency for tests."""

    def mock_get_settings():
        return test_settings

    monkeypatch.setattr("ai_service.core.config.get_settings", mock_get_settings)
    monkeypatch.setattr(
        "ai_service.api.v1.routes.health.get_settings", mock_get_settings
    )


@pytest_asyncio.fixture
async def test_app():
    """Create a test FastAPI application."""
    from src.main import create_app

    app = create_app()

    # Initialize test services with mock repository
    from ai_service.core.config import Settings
    from tests.mocks.mock_mongodb_repository import MockMongoDBSpendingRepository

    test_settings = Settings()
    test_settings.mongodb_url = "mongodb://localhost:27017"
    test_settings.mongodb_database = "test_spending_db"
    test_settings.mongodb_collection = "test_spending_entries"
    test_settings.mongodb_timeout = 5

    test_repo = MockMongoDBSpendingRepository(test_settings)
    await test_repo.initialize()

    app.state.spending_repository = test_repo

    # Create mock clients for tests
    from unittest.mock import AsyncMock, MagicMock

    mock_llama_client = MagicMock()

    # Mock process_text to return a proper result
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.spending_entry = MagicMock()
    mock_result.spending_entry.id.value = "test-id"
    mock_result.spending_entry.confidence.value = 0.8
    mock_result.spending_entry.processing_method.value = "manual"

    mock_llama_client.process_text = AsyncMock(return_value=mock_result)
    mock_llama_client.is_available = MagicMock(return_value=True)

    mock_ocr_client = MagicMock()
    mock_ocr_client.extract_text = AsyncMock(
        return_value={"success": True, "text": "Test receipt text", "confidence": 0.9}
    )
    mock_ocr_client.is_available = MagicMock(return_value=True)

    app.state.llama_client = mock_llama_client
    app.state.ocr_client = mock_ocr_client

    yield app

    # Cleanup
    await test_repo.close()


@pytest_asyncio.fixture
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_client(test_app) -> TestClient:
    """Create a sync HTTP client for testing."""
    return TestClient(test_app)


# Test data factories
class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_spending_entry(**kwargs) -> SpendingEntry:
        """Create a spending entry with default values."""
        defaults = {
            "amount": Money.from_float(100.0, Currency.THB),
            "merchant": "Test Merchant",
            "description": "Test transaction",
            "transaction_date": datetime.utcnow(),
            "category": SpendingCategory.MISCELLANEOUS,
            "payment_method": PaymentMethod.CASH,
            "confidence": ConfidenceScore.medium(),
            "processing_method": ProcessingMethod.MANUAL,
        }
        defaults.update(kwargs)
        return SpendingEntry(**defaults)

    @staticmethod
    def create_spending_request(**kwargs) -> dict:
        """Create a spending request dict."""
        defaults = {
            "amount": 100.0,
            "merchant": "Test Merchant",
            "description": "Test transaction",
            "category": "Miscellaneous",
            "payment_method": "Cash",
        }
        defaults.update(kwargs)
        return defaults


@pytest.fixture
def test_data_factory() -> TestDataFactory:
    """Provide the test data factory."""
    return TestDataFactory()


# Markers for different test types
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (slower, with dependencies)",
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests (slowest, full system)"
    )
    config.addinivalue_line("markers", "slow: marks tests as slow running")


# Mock fixtures for external services
@pytest.fixture
def mock_llama_client():
    """Mock Llama client for testing."""

    class MockLlamaClient:
        async def health_check(self) -> bool:
            return True

        async def parse_spending_text(self, text: str, language: str = "en") -> dict:
            return {
                "success": True,
                "parsed_data": {
                    "amount": 100.0,
                    "merchant": "Mock Merchant",
                    "category": "Food & Dining",
                    "confidence": 0.9,
                },
            }

        async def close(self):
            pass

    return MockLlamaClient()


@pytest.fixture
def mock_ocr_client():
    """Mock OCR client for testing."""

    class MockOCRClient:
        def is_available(self) -> bool:
            return True

        async def extract_text(
            self, image_data: bytes, language: str | None = None
        ) -> dict:
            return {
                "success": True,
                "text": "Mock extracted text: Coffee 100 THB",
                "confidence": 0.85,
                "language": "en",
            }

    return MockOCRClient()
