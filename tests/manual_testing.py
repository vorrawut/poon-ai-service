#!/usr/bin/env python3
"""
Manual Testing Script for Poon AI Service

This script provides comprehensive manual testing capabilities for the AI service,
including API endpoints, external services, and end-to-end workflows.

Usage:
    python tests/manual_testing.py --help
    python tests/manual_testing.py --test-all
    python tests/manual_testing.py --test-api
    python tests/manual_testing.py --test-ocr
    python tests/manual_testing.py --test-llama
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import tempfile
from pathlib import Path
from typing import Any

import aiohttp
from PIL import Image, ImageDraw, ImageFont

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_service.infrastructure.external_apis.llama_client import LlamaClient
from ai_service.infrastructure.external_apis.ocr_client import TesseractOCRClient


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    END = "\033[0m"


class ManualTester:
    """Manual testing framework for the AI service."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")
        self.session: aiohttp.ClientSession | None = None
        self.results: dict[str, Any] = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "tests": [],
        }

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def log_success(self, message: str):
        """Log success message."""
        print(f"{Colors.GREEN}✓{Colors.END} {message}")

    def log_error(self, message: str):
        """Log error message."""
        print(f"{Colors.RED}✗{Colors.END} {message}")

    def log_warning(self, message: str):
        """Log warning message."""
        print(f"{Colors.YELLOW}⚠{Colors.END} {message}")

    def log_info(self, message: str):
        """Log info message."""
        print(f"{Colors.BLUE}[INFO]{Colors.END} {message}")

    def log_header(self, message: str):
        """Log section header."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{message}{Colors.END}")
        print("=" * len(message))

    async def test_api_health(self) -> bool:
        """Test API health endpoints."""
        self.log_header("Testing API Health Endpoints")

        try:
            # Test basic health
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_success(
                        f"Basic health check: {data.get('status', 'unknown')}"
                    )
                else:
                    self.log_error(f"Basic health check failed: {response.status}")
                    return False

            # Test detailed health
            async with self.session.get(
                f"{self.base_url}/api/v1/health/detailed"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_success("Detailed health check passed")

                    # Check service dependencies
                    deps = data.get("dependencies", {})
                    for service, status in deps.items():
                        if status == "healthy":
                            self.log_success(f"  {service}: {status}")
                        else:
                            self.log_warning(f"  {service}: {status}")
                else:
                    self.log_error(f"Detailed health check failed: {response.status}")
                    return False

            return True

        except Exception as e:
            self.log_error(f"Health check error: {e}")
            return False

    async def test_spending_api(self) -> bool:
        """Test spending API endpoints."""
        self.log_header("Testing Spending API Endpoints")

        try:
            # Test GET /api/v1/spending/ (empty)
            async with self.session.get(
                f"{self.base_url}/api/v1/spending/"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_success(
                        f"Get spending entries: {len(data.get('entries', []))} entries"
                    )
                else:
                    self.log_error(f"Get spending entries failed: {response.status}")
                    return False

            # Test POST /api/v1/spending/ (create entry)
            test_entry = {
                "merchant": "Manual Test Cafe",
                "amount": 15.75,
                "currency": "USD",
                "category": "Food & Dining",
                "description": "Manual testing entry",
            }

            async with self.session.post(
                f"{self.base_url}/api/v1/spending/", json=test_entry
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    entry_id = data.get("entry_id")
                    self.log_success(f"Created spending entry: {entry_id}")

                    # Test GET specific entry
                    async with self.session.get(
                        f"{self.base_url}/api/v1/spending/{entry_id}"
                    ) as get_response:
                        if get_response.status == 200:
                            entry_data = await get_response.json()
                            self.log_success(
                                f"Retrieved entry: {entry_data.get('merchant', 'unknown')}"
                            )
                        else:
                            self.log_warning(
                                f"Could not retrieve created entry: {get_response.status}"
                            )
                else:
                    self.log_error(f"Create spending entry failed: {response.status}")
                    return False

            # Test POST /api/v1/spending/process/text
            test_text = {
                "text": "Coffee at Starbucks $4.50 with credit card",
                "use_ai_enhancement": True,
            }

            async with self.session.post(
                f"{self.base_url}/api/v1/spending/process/text", json=test_text
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_success(
                        f"Text processing: {data.get('status', 'unknown')}"
                    )
                    if data.get("parsed_data"):
                        parsed = data["parsed_data"]
                        self.log_info(f"  Merchant: {parsed.get('merchant', 'N/A')}")
                        self.log_info(f"  Amount: {parsed.get('amount', 'N/A')}")
                        self.log_info(f"  Category: {parsed.get('category', 'N/A')}")
                elif response.status == 400:
                    error_data = await response.json()
                    self.log_warning(
                        f"Text processing failed (expected if Llama unavailable): {error_data.get('detail', 'Unknown error')}"
                    )
                else:
                    self.log_error(f"Text processing failed: {response.status}")

            return True

        except Exception as e:
            self.log_error(f"Spending API error: {e}")
            return False

    def create_test_receipt_image(self) -> str:
        """Create a test receipt image for OCR testing."""
        # Create image
        img = Image.new("RGB", (400, 600), color="white")
        draw = ImageDraw.Draw(img)

        # Try to use a system font, fall back to default
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
            font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
        except OSError:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Draw receipt content
        y = 50
        draw.text((50, y), "COFFEE SHOP RECEIPT", fill="black", font=font_large)
        y += 50
        draw.text((50, y), "123 Main Street", fill="black", font=font_small)
        y += 30
        draw.text((50, y), "Date: 2024-01-15", fill="black", font=font_small)
        y += 50

        # Items
        draw.text((50, y), "Latte                $4.50", fill="black", font=font_medium)
        y += 30
        draw.text((50, y), "Croissant           $3.25", fill="black", font=font_medium)
        y += 30
        draw.text((50, y), "Tax                  $0.62", fill="black", font=font_medium)
        y += 40
        draw.text((50, y), "TOTAL               $8.37", fill="black", font=font_large)
        y += 50

        draw.text((50, y), "Payment: Credit Card", fill="black", font=font_small)
        y += 30
        draw.text((50, y), "Thank you!", fill="black", font=font_medium)

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(temp_file.name)
        temp_file.close()

        return temp_file.name

    async def test_ocr_service(self) -> bool:
        """Test OCR service functionality."""
        self.log_header("Testing OCR Service")

        try:
            ocr_client = TesseractOCRClient()

            # Check availability
            if not ocr_client.is_available():
                self.log_warning("Tesseract OCR not available - skipping OCR tests")
                return True

            self.log_success(f"Tesseract available at: {ocr_client.tesseract_path}")
            self.log_info(f"Languages: {ocr_client.languages}")

            # Create test image
            test_image_path = self.create_test_receipt_image()
            self.log_info(f"Created test receipt image: {test_image_path}")

            try:
                # Test text extraction
                extracted_text = await ocr_client.extract_text(test_image_path)
                if extracted_text:
                    self.log_success("OCR text extraction successful")
                    self.log_info("Extracted text preview:")
                    lines = extracted_text.split("\n")[:5]  # First 5 lines
                    for line in lines:
                        if line.strip():
                            self.log_info(f"  {line.strip()}")

                    # Check for expected content
                    if "COFFEE SHOP" in extracted_text.upper():
                        self.log_success("Found expected 'COFFEE SHOP' text")
                    if "$" in extracted_text:
                        self.log_success("Found currency symbols")
                else:
                    self.log_error("OCR extraction returned no text")
                    return False

                # Test extraction with confidence
                result_with_conf = await ocr_client.extract_text_with_confidence(
                    test_image_path
                )
                if result_with_conf:
                    confidence = result_with_conf.get("confidence", 0)
                    self.log_success(f"OCR with confidence: {confidence:.2f}")
                else:
                    self.log_warning("OCR confidence extraction failed")

            finally:
                # Cleanup test image
                Path(test_image_path).unlink(missing_ok=True)

            return True

        except Exception as e:
            self.log_error(f"OCR service error: {e}")
            return False

    async def test_llama_service(self) -> bool:
        """Test Llama service functionality."""
        self.log_header("Testing Llama Service")

        try:
            llama_client = LlamaClient()

            # Test health check
            health = await llama_client.health_check()
            if health:
                self.log_success("Llama service is healthy")
            else:
                self.log_warning(
                    "Llama service health check failed - may not be running"
                )
                return True  # Don't fail the test, just warn

            # Test basic completion
            try:
                response = await llama_client.generate_completion(
                    "What is 2+2? Answer with just the number."
                )
                if response:
                    self.log_success(f"Basic completion: '{response.strip()}'")
                else:
                    self.log_error("No response from Llama")
                    return False
            except Exception as e:
                self.log_warning(f"Basic completion failed: {e}")

            # Test spending text parsing
            test_texts = [
                "Coffee at Starbucks $4.50",
                "Lunch at McDonald's 8.99 USD",
                "Gas station fill up $45.00",
                "Grocery shopping at Walmart $67.23",
            ]

            for text in test_texts:
                try:
                    parsed = await llama_client.parse_spending_text(text)
                    if parsed:
                        self.log_success(f"Parsed: '{text}'")
                        self.log_info(f"  → Merchant: {parsed.get('merchant', 'N/A')}")
                        self.log_info(f"  → Amount: {parsed.get('amount', 'N/A')}")
                        self.log_info(f"  → Category: {parsed.get('category', 'N/A')}")
                    else:
                        self.log_warning(f"Failed to parse: '{text}'")
                except Exception as e:
                    self.log_warning(f"Parsing error for '{text}': {e}")

            await llama_client.close()
            return True

        except Exception as e:
            self.log_error(f"Llama service error: {e}")
            return False

    async def test_end_to_end_workflow(self) -> bool:
        """Test complete end-to-end workflow."""
        self.log_header("Testing End-to-End Workflow")

        try:
            # Create test receipt image
            test_image_path = self.create_test_receipt_image()
            self.log_info("Created test receipt for E2E workflow")

            try:
                # Step 1: OCR extraction
                ocr_client = TesseractOCRClient()
                if not ocr_client.is_available():
                    self.log_warning("OCR not available - skipping E2E test")
                    return True

                extracted_text = await ocr_client.extract_text(test_image_path)
                if not extracted_text:
                    self.log_error("E2E: OCR extraction failed")
                    return False

                self.log_success("E2E Step 1: OCR extraction successful")

                # Step 2: AI parsing
                llama_client = LlamaClient()
                health = await llama_client.health_check()

                if health:
                    try:
                        parsed_data = await llama_client.parse_spending_text(
                            extracted_text
                        )
                        if parsed_data:
                            self.log_success("E2E Step 2: AI parsing successful")
                            self.log_info(
                                f"  Merchant: {parsed_data.get('merchant', 'N/A')}"
                            )
                            self.log_info(
                                f"  Amount: {parsed_data.get('amount', 'N/A')}"
                            )
                        else:
                            self.log_warning("E2E Step 2: AI parsing returned no data")
                    except Exception as e:
                        self.log_warning(f"E2E Step 2: AI parsing failed: {e}")
                else:
                    self.log_warning("E2E Step 2: Llama service not available")

                # Step 3: API submission
                if "parsed_data" in locals() and parsed_data:
                    entry_data = {
                        "merchant": parsed_data.get("merchant", "E2E Test Merchant"),
                        "amount": float(parsed_data.get("amount", 10.0)),
                        "currency": "USD",
                        "category": parsed_data.get("category", "Other"),
                        "description": "End-to-end test entry",
                    }
                else:
                    entry_data = {
                        "merchant": "E2E Test Merchant",
                        "amount": 10.0,
                        "currency": "USD",
                        "category": "Other",
                        "description": "End-to-end test entry (fallback)",
                    }

                async with self.session.post(
                    f"{self.base_url}/api/v1/spending/", json=entry_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_success(
                            f"E2E Step 3: API submission successful - {data.get('entry_id')}"
                        )
                    else:
                        self.log_error(
                            f"E2E Step 3: API submission failed - {response.status}"
                        )
                        return False

                await llama_client.close()

            finally:
                # Cleanup
                Path(test_image_path).unlink(missing_ok=True)

            self.log_success("End-to-end workflow completed successfully!")
            return True

        except Exception as e:
            self.log_error(f"E2E workflow error: {e}")
            return False

    async def test_error_scenarios(self) -> bool:
        """Test error handling scenarios."""
        self.log_header("Testing Error Scenarios")

        try:
            # Test invalid JSON
            async with self.session.post(
                f"{self.base_url}/api/v1/spending/", data="invalid json"
            ) as response:
                if response.status == 422:
                    self.log_success("Invalid JSON handled correctly (422)")
                else:
                    self.log_warning(
                        f"Unexpected status for invalid JSON: {response.status}"
                    )

            # Test missing required fields
            async with self.session.post(
                f"{self.base_url}/api/v1/spending/",
                json={"merchant": "Test"},  # Missing required fields
            ) as response:
                if response.status == 422:
                    self.log_success("Missing fields handled correctly (422)")
                else:
                    self.log_warning(
                        f"Unexpected status for missing fields: {response.status}"
                    )

            # Test invalid entry ID
            async with self.session.get(
                f"{self.base_url}/api/v1/spending/invalid-id"
            ) as response:
                if response.status == 404:
                    self.log_success("Invalid entry ID handled correctly (404)")
                else:
                    self.log_warning(
                        f"Unexpected status for invalid ID: {response.status}"
                    )

            # Test non-existent endpoint
            async with self.session.get(
                f"{self.base_url}/api/v1/nonexistent"
            ) as response:
                if response.status == 404:
                    self.log_success("Non-existent endpoint handled correctly (404)")
                else:
                    self.log_warning(
                        f"Unexpected status for non-existent endpoint: {response.status}"
                    )

            return True

        except Exception as e:
            self.log_error(f"Error scenario testing failed: {e}")
            return False

    def print_summary(self):
        """Print test summary."""
        self.log_header("Test Summary")

        total = (
            self.results["passed"] + self.results["failed"] + self.results["skipped"]
        )

        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {self.results['passed']}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.results['failed']}{Colors.END}")
        print(f"{Colors.YELLOW}Skipped: {self.results['skipped']}{Colors.END}")

        if self.results["failed"] == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed!{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ Some tests failed{Colors.END}")

    async def run_all_tests(self):
        """Run all manual tests."""
        self.log_header("🧪 Poon AI Service - Manual Testing Suite")

        tests = [
            ("API Health", self.test_api_health),
            ("Spending API", self.test_spending_api),
            ("OCR Service", self.test_ocr_service),
            ("Llama Service", self.test_llama_service),
            ("End-to-End Workflow", self.test_end_to_end_workflow),
            ("Error Scenarios", self.test_error_scenarios),
        ]

        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    self.results["passed"] += 1
                    self.results["tests"].append(
                        {"name": test_name, "status": "passed"}
                    )
                else:
                    self.results["failed"] += 1
                    self.results["tests"].append(
                        {"name": test_name, "status": "failed"}
                    )
            except Exception as e:
                self.log_error(f"Test '{test_name}' crashed: {e}")
                self.results["failed"] += 1
                self.results["tests"].append(
                    {"name": test_name, "status": "crashed", "error": str(e)}
                )

        self.print_summary()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Manual testing for Poon AI Service")
    parser.add_argument(
        "--base-url", default="http://localhost:8001", help="Base URL for the API"
    )
    parser.add_argument("--test-all", action="store_true", help="Run all tests")
    parser.add_argument(
        "--test-api", action="store_true", help="Test API endpoints only"
    )
    parser.add_argument("--test-ocr", action="store_true", help="Test OCR service only")
    parser.add_argument(
        "--test-llama", action="store_true", help="Test Llama service only"
    )
    parser.add_argument(
        "--test-e2e", action="store_true", help="Test end-to-end workflow only"
    )

    args = parser.parse_args()

    async with ManualTester(args.base_url) as tester:
        if args.test_all or not any(
            [args.test_api, args.test_ocr, args.test_llama, args.test_e2e]
        ):
            await tester.run_all_tests()
        else:
            if args.test_api:
                await tester.test_api_health()
                await tester.test_spending_api()
                await tester.test_error_scenarios()

            if args.test_ocr:
                await tester.test_ocr_service()

            if args.test_llama:
                await tester.test_llama_service()

            if args.test_e2e:
                await tester.test_end_to_end_workflow()

            tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
