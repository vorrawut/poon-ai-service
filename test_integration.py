#!/usr/bin/env python3
"""
Integration test script for Llama4 AI Service
Tests the complete pipeline from text input to database storage
"""

import asyncio
from datetime import datetime
import sys

import aiohttp

# Test configuration
BASE_URL = "http://localhost:8001"
TEST_CASES = [
    {
        "name": "English Coffee Purchase",
        "text": "Coffee at Starbucks 120 baht cash",
        "expected_merchant": "Starbucks",
        "expected_amount": 120.0,
        "expected_category": "Food & Dining",
    },
    {
        "name": "Thai Food Purchase",
        "text": "ซื้อข้าวผัด 50 บาท เงินสด",
        "expected_merchant": None,  # May vary
        "expected_amount": 50.0,
        "expected_category": "Food & Dining",
    },
    {
        "name": "Transportation",
        "text": "Grab taxi to airport 250 baht by card",
        "expected_merchant": "Grab",
        "expected_amount": 250.0,
        "expected_category": "Transportation",
    },
    {
        "name": "Shopping",
        "text": "Bought shirt at Central 890 baht credit card",
        "expected_merchant": "Central",
        "expected_amount": 890.0,
        "expected_category": "Shopping",
    },
]


class IntegrationTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
        self.test_results = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_health(self):
        """Check if the AI service is healthy"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Service health: {health_data}")
                    return True
                else:
                    print(f"❌ Service unhealthy: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Failed to check service health: {e}")
            return False

    async def check_ai_status(self):
        """Check if AI service (Llama4) is available"""
        try:
            async with self.session.get(f"{self.base_url}/ai/status") as response:
                if response.status == 200:
                    ai_status = await response.json()
                    print(f"🦙 AI Status: {ai_status}")
                    return ai_status.get("ai_available", False)
                else:
                    print(f"❌ AI status check failed: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Failed to check AI status: {e}")
            return False

    async def test_llama_parsing(self, test_case):
        """Test direct Llama4 parsing"""
        print(f"\n🧪 Testing: {test_case['name']}")
        print(f"   Input: {test_case['text']}")

        try:
            payload = {
                "text": test_case["text"],
                "language": "en",
                "context": {"test_case": test_case["name"]},
            }

            async with self.session.post(
                f"{self.base_url}/llama/parse", json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    print("   ✅ Parsed successfully!")
                    print(f"   📊 Confidence: {result.get('confidence', 0):.2f}")
                    print(f"   🏪 Merchant: {result.get('merchant', 'N/A')}")
                    print(f"   💰 Amount: {result.get('amount', 0)}")
                    print(f"   📂 Category: {result.get('category', 'N/A')}")
                    print(f"   💳 Payment: {result.get('payment_method', 'N/A')}")

                    # Validate results
                    validation = self.validate_result(test_case, result)
                    self.test_results.append(
                        {
                            "test_case": test_case["name"],
                            "success": True,
                            "validation": validation,
                            "result": result,
                        }
                    )

                    return result
                else:
                    error_data = (
                        await response.json()
                        if response.content_type == "application/json"
                        else {}
                    )
                    print(f"   ❌ Parsing failed: HTTP {response.status}")
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")

                    self.test_results.append(
                        {
                            "test_case": test_case["name"],
                            "success": False,
                            "error": f"HTTP {response.status}: {error_data.get('detail', 'Unknown')}",
                        }
                    )
                    return None

        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            self.test_results.append(
                {"test_case": test_case["name"], "success": False, "error": str(e)}
            )
            return None

    async def test_process_and_store(self, test_case):
        """Test processing text and storing in database"""
        print(f"\n💾 Testing storage for: {test_case['name']}")

        try:
            payload = {
                "text": test_case["text"],
                "language": "en",
                "use_ai_fallback": True,
                "context": {"test_case": test_case["name"]},
            }

            async with self.session.post(
                f"{self.base_url}/process/text/store", json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("   ✅ Processed and stored successfully!")
                    print(f"   🆔 Entry ID: {result.get('id', 'N/A')}")
                    print(f"   📊 Confidence: {result.get('confidence', 0):.2f}")

                    # Verify storage by retrieving the entry
                    entry_id = result.get("id")
                    if entry_id:
                        await self.verify_storage(entry_id)

                    return result
                else:
                    error_data = (
                        await response.json()
                        if response.content_type == "application/json"
                        else {}
                    )
                    print(f"   ❌ Process and store failed: HTTP {response.status}")
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    return None

        except Exception as e:
            print(f"   ❌ Process and store failed with exception: {e}")
            return None

    async def verify_storage(self, entry_id: str):
        """Verify that an entry was stored correctly"""
        try:
            async with self.session.get(
                f"{self.base_url}/spending/entries/{entry_id}"
            ) as response:
                if response.status == 200:
                    stored_entry = await response.json()
                    print("   ✅ Entry verified in database")
                    print(f"   📅 Created: {stored_entry.get('created_at', 'N/A')}")
                    return True
                else:
                    print(f"   ❌ Failed to verify storage: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Storage verification failed: {e}")
            return False

    async def get_statistics(self):
        """Get database statistics"""
        try:
            async with self.session.get(
                f"{self.base_url}/spending/statistics"
            ) as response:
                if response.status == 200:
                    stats = await response.json()
                    print("\n📊 Database Statistics:")
                    print(f"   Total Entries: {stats.get('total_entries', 0)}")
                    print(f"   Total Amount: ฿{stats.get('total_amount', 0):,.2f}")
                    print(
                        f"   Average Confidence: {stats.get('average_confidence', 0):.3f}"
                    )

                    method_breakdown = stats.get("method_breakdown", {})
                    if method_breakdown:
                        print("   Processing Methods:")
                        for method, count in method_breakdown.items():
                            print(f"     {method}: {count}")

                    return stats
                else:
                    print(f"   ❌ Failed to get statistics: HTTP {response.status}")
                    return None
        except Exception as e:
            print(f"   ❌ Statistics retrieval failed: {e}")
            return None

    def validate_result(self, test_case, result):
        """Validate parsing results against expected values"""
        validation = {
            "amount_correct": False,
            "merchant_correct": False,
            "category_correct": False,
            "confidence_acceptable": False,
        }

        # Check amount
        expected_amount = test_case.get("expected_amount")
        actual_amount = result.get("amount")
        if expected_amount and actual_amount:
            validation["amount_correct"] = abs(actual_amount - expected_amount) < 0.01

        # Check merchant (if expected)
        expected_merchant = test_case.get("expected_merchant")
        actual_merchant = result.get("merchant", "")
        if expected_merchant:
            validation["merchant_correct"] = (
                expected_merchant.lower() in actual_merchant.lower()
            )
        else:
            validation["merchant_correct"] = True  # No expectation

        # Check category
        expected_category = test_case.get("expected_category")
        actual_category = result.get("category", "")
        if expected_category:
            validation["category_correct"] = (
                expected_category.lower() in actual_category.lower()
            )

        # Check confidence
        confidence = result.get("confidence", 0)
        validation["confidence_acceptable"] = confidence >= 0.7

        return validation

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🧪 INTEGRATION TEST SUMMARY")
        print("=" * 60)

        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])

        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(
            f"Success Rate: {(successful_tests / total_tests * 100):.1f}%"
            if total_tests > 0
            else "N/A"
        )

        print("\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test_case']}")

            if result["success"] and "validation" in result:
                validation = result["validation"]
                validations = [
                    f"Amount: {'✅' if validation['amount_correct'] else '❌'}",
                    f"Merchant: {'✅' if validation['merchant_correct'] else '❌'}",
                    f"Category: {'✅' if validation['category_correct'] else '❌'}",
                    f"Confidence: {'✅' if validation['confidence_acceptable'] else '❌'}",
                ]
                print(f"     Validation: {' | '.join(validations)}")

            if not result["success"] and "error" in result:
                print(f"     Error: {result['error']}")


async def main():
    """Run integration tests"""
    print("🚀 Starting Llama4 AI Service Integration Tests")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")

    async with IntegrationTester(BASE_URL) as tester:
        # Check service health
        print("\n🔍 Checking service health...")
        if not await tester.check_health():
            print("❌ Service is not healthy. Please start the AI service first.")
            sys.exit(1)

        # Check AI availability
        print("\n🦙 Checking AI service availability...")
        ai_available = await tester.check_ai_status()
        if not ai_available:
            print("⚠️ AI service (Llama4) is not available. Some tests may fail.")
            print("Please ensure Ollama is running and Llama 3.2 model is installed.")

        # Run parsing tests
        print("\n🧪 Running parsing tests...")
        for test_case in TEST_CASES:
            await tester.test_llama_parsing(test_case)
            await asyncio.sleep(1)  # Small delay between tests

        # Run storage tests
        print("\n💾 Running storage tests...")
        for test_case in TEST_CASES:
            await tester.test_process_and_store(test_case)
            await asyncio.sleep(1)

        # Get final statistics
        await tester.get_statistics()

        # Print summary
        tester.print_summary()

        # Final verdict
        successful_tests = sum(1 for result in tester.test_results if result["success"])
        total_tests = len(tester.test_results)

        if successful_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Llama4 integration is working perfectly.")
            return 0
        elif successful_tests > 0:
            print(
                f"\n⚠️ PARTIAL SUCCESS: {successful_tests}/{total_tests} tests passed."
            )
            print("Check the failed tests and ensure Ollama is properly configured.")
            return 1
        else:
            print("\n❌ ALL TESTS FAILED! Please check your configuration.")
            print("Ensure the AI service is running and Ollama is properly set up.")
            return 2


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)
