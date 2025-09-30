"""Integration tests for external API clients."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from ai_service.infrastructure.external_apis.llama_client import LlamaClient
from ai_service.infrastructure.external_apis.ocr_client import TesseractOCRClient


@pytest.mark.integration
class TestLlamaClientIntegration:
    """Integration tests for Llama client."""

    @pytest.fixture
    def llama_client(self):
        """Create Llama client for testing."""
        return LlamaClient(
            base_url="http://localhost:11434", model="llama3.2:3b", timeout=30
        )

    async def test_health_check_success(self, llama_client):
        """Test successful health check."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await llama_client.health_check()
            assert result is True

    async def test_health_check_failure(self, llama_client):
        """Test health check failure."""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = Exception("Connection failed")

            result = await llama_client.health_check()
            assert result is False

    async def test_generate_completion_success(self, llama_client):
        """Test successful completion generation."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "response": "This is a test response",
                "done": True,
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await llama_client.generate_completion("Test prompt")
            assert result["success"] is True
            assert result["response"] == "This is a test response"

    async def test_generate_completion_failure(self, llama_client):
        """Test completion generation failure."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_response.json.return_value = {"error": "model not found"}
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await llama_client.generate_completion("Test prompt")
            assert result["success"] is False
            assert "HTTP error" in result["error"]

    async def test_parse_spending_text_success(self, llama_client):
        """Test successful spending text parsing."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "response": '{"merchant": "Coffee Shop", "amount": 4.50, "category": "Food & Dining"}',
                "done": True,
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await llama_client.parse_spending_text(
                "Coffee at Coffee Shop $4.50"
            )

            assert result is not None
            assert result["success"] is True
            assert "merchant" in result["parsed_data"]
            assert "amount" in result["parsed_data"]
            assert "category" in result["parsed_data"]

    async def test_parse_spending_text_invalid_json(self, llama_client):
        """Test spending text parsing with invalid JSON response."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "response": "Invalid JSON response",
                "done": True,
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await llama_client.parse_spending_text("Test text")
            assert result is not None
            assert result["success"] is False
            assert "error" in result

    async def test_client_lifecycle(self, llama_client):
        """Test client initialization and cleanup."""
        # Client should be ready to use
        assert llama_client.base_url == "http://localhost:11434"
        assert llama_client.model == "llama3.2:3b"

        # Close should work without errors
        await llama_client.close()


@pytest.mark.integration
class TestTesseractOCRClientIntegration:
    """Integration tests for Tesseract OCR client."""

    @pytest.fixture
    def ocr_client(self):
        """Create OCR client for testing."""
        return TesseractOCRClient()

    @pytest.fixture
    def test_image(self):
        """Create a test image with text."""
        # Create a simple test image with text
        img = Image.new("RGB", (200, 100), color="white")

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(temp_file.name)
        temp_file.close()

        yield temp_file.name

        # Cleanup
        Path(temp_file.name).unlink(missing_ok=True)

    def test_client_availability(self, ocr_client):
        """Test OCR client availability detection."""
        # This will depend on whether Tesseract is actually installed
        availability = ocr_client.is_available()
        assert isinstance(availability, bool)

        if availability:
            assert ocr_client.tesseract_path is not None
            assert ocr_client.languages == "eng+tha"

    async def test_extract_text_success(self, ocr_client, test_image):
        """Test successful text extraction."""
        if not ocr_client.is_available():
            pytest.skip("Tesseract not available")

        # Mock subprocess.run to return predictable results
        with patch("subprocess.run") as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Test Receipt\nCoffee Shop\n$4.50"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            result = await ocr_client.extract_text(test_image)

            assert result is not None
            assert result["success"] is True
            assert "Test Receipt" in result["text"]
            assert "Coffee Shop" in result["text"]
            assert "$4.50" in result["text"]

    async def test_extract_text_with_confidence(self, ocr_client, test_image):
        """Test text extraction with confidence scores."""
        if not ocr_client.is_available():
            pytest.skip("Tesseract not available")

        # Mock subprocess.run to return predictable results with confidence
        with patch("subprocess.run") as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Test Receipt\nCoffee Shop\n$4.50"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result

            result = await ocr_client.extract_text(test_image)

            assert result is not None
            assert "text" in result
            assert "confidence" in result
            assert result["confidence"] > 0

    async def test_extract_text_file_not_found(self, ocr_client):
        """Test text extraction with non-existent file."""
        if not ocr_client.is_available():
            pytest.skip("Tesseract not available")

        result = await ocr_client.extract_text("/non/existent/file.png")
        assert result is not None
        assert result["success"] is False
        assert "error" in result

    async def test_extract_text_invalid_image(self, ocr_client):
        """Test text extraction with invalid image file."""
        if not ocr_client.is_available():
            pytest.skip("Tesseract not available")

        # Create a text file instead of image
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        temp_file.write("This is not an image")
        temp_file.close()

        try:
            result = await ocr_client.extract_text(temp_file.name)
            assert result is not None
            assert result["success"] is False
            assert "error" in result
        finally:
            Path(temp_file.name).unlink(missing_ok=True)

    def test_client_configuration(self, ocr_client):
        """Test client configuration."""
        assert ocr_client.languages == "eng+tha"

        # Test with custom configuration
        custom_client = TesseractOCRClient(languages="eng")
        assert custom_client.languages == "eng"

    async def test_batch_processing(self, ocr_client):
        """Test processing multiple images."""
        if not ocr_client.is_available():
            pytest.skip("Tesseract not available")

        # Create multiple test images
        test_images = []
        for i in range(3):
            img = Image.new("RGB", (200, 100), color="white")
            temp_file = tempfile.NamedTemporaryFile(suffix=f"_{i}.png", delete=False)
            img.save(temp_file.name)
            temp_file.close()
            test_images.append(temp_file.name)

        try:
            with patch("subprocess.run") as mock_run:
                from unittest.mock import MagicMock

                mock_result = MagicMock()
                mock_result.stdout = "Test text"
                mock_result.stderr = ""
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                # Process all images
                results = []
                for image_path in test_images:
                    result = await ocr_client.extract_text(image_path)
                    results.append(result)

                # All should succeed
                assert len(results) == 3
                assert all(
                    result["success"] is True and result["text"] == "Test text"
                    for result in results
                )

        finally:
            # Cleanup
            for image_path in test_images:
                Path(image_path).unlink(missing_ok=True)


@pytest.mark.integration
class TestExternalAPIIntegration:
    """Integration tests for combined external API usage."""

    @pytest.fixture
    def llama_client(self):
        """Create Llama client."""
        return LlamaClient()

    @pytest.fixture
    def ocr_client(self):
        """Create OCR client."""
        return TesseractOCRClient()

    async def test_ocr_to_llama_pipeline(self, ocr_client, llama_client):
        """Test complete OCR to Llama processing pipeline."""
        if not ocr_client.is_available():
            pytest.skip("Tesseract not available")

        # Create test image
        img = Image.new("RGB", (300, 150), color="white")
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(temp_file.name)
        temp_file.close()

        try:
            # Mock OCR extraction
            with patch("pytesseract.image_to_string") as mock_ocr:
                mock_ocr.return_value = "Coffee Shop Receipt\nLatte $4.50\nTotal: $4.50"

                # Extract text
                extracted_text = await ocr_client.extract_text(temp_file.name)
                assert extracted_text is not None

                # Mock Llama parsing
                with patch("aiohttp.ClientSession.post") as mock_post:
                    mock_response = AsyncMock()
                    mock_response.status = 200
                    mock_response.json.return_value = {
                        "response": '{"merchant": "Coffee Shop", "amount": 4.50, "category": "Food & Dining"}',
                        "done": True,
                    }
                    mock_post.return_value.__aenter__.return_value = mock_response

                    # Parse with Llama
                    parsed_data = await llama_client.parse_spending_text(extracted_text)

                    assert parsed_data is not None
                    assert parsed_data["success"] is True
                    assert parsed_data["parsed_data"]["merchant"] == "Coffee Shop"
                    assert parsed_data["parsed_data"]["amount"] == 4.50
                    assert parsed_data["parsed_data"]["category"] == "Food & Dining"

        finally:
            Path(temp_file.name).unlink(missing_ok=True)

    async def test_error_handling_pipeline(self, ocr_client, llama_client):
        """Test error handling in the complete pipeline."""
        # Test with non-existent image
        extracted_text = await ocr_client.extract_text("/non/existent/image.png")
        assert extracted_text is not None
        assert extracted_text["success"] is False
        assert "error" in extracted_text

        # Test Llama with empty text
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.json.return_value = {"error": "Invalid input"}
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await llama_client.parse_spending_text("")
            assert result is not None
            assert result["success"] is False
            assert "error" in result

    async def test_service_health_checks(self, ocr_client, llama_client):
        """Test health checks for all external services."""
        # OCR health check (based on Tesseract availability)
        ocr_healthy = ocr_client.is_available()
        assert isinstance(ocr_healthy, bool)

        # Llama health check (mocked)
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_get.return_value.__aenter__.return_value = mock_response

            llama_healthy = await llama_client.health_check()
            assert llama_healthy is True
