#!/usr/bin/env python3
"""
Comprehensive API Performance Test Suite
Tests all endpoints and measures response times to identify slow APIs.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Tuple
import aiohttp
import sys

# Base URL for the AI service
BASE_URL = "http://localhost:8001"

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []

    async def test_endpoint(
        self,
        session: aiohttp.ClientSession,
        method: str,
        endpoint: str,
        data: Dict[str, Any] = None,
        expected_status: int = 200,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Test a single endpoint and measure performance."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            if method.upper() == "GET":
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    response_data = await response.json()
                    status = response.status
            elif method.upper() == "POST":
                async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    response_data = await response.json()
                    status = response.status
            else:
                raise ValueError(f"Unsupported method: {method}")

            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds

            result = {
                "endpoint": endpoint,
                "method": method,
                "status": status,
                "response_time_ms": round(response_time, 2),
                "expected_status": expected_status,
                "success": status == expected_status,
                "data": response_data if status == expected_status else None,
                "error": None
            }

            if status != expected_status:
                result["error"] = f"Expected {expected_status}, got {status}"

        except asyncio.TimeoutError:
            result = {
                "endpoint": endpoint,
                "method": method,
                "status": None,
                "response_time_ms": timeout * 1000,
                "expected_status": expected_status,
                "success": False,
                "data": None,
                "error": f"Timeout after {timeout}s"
            }
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            result = {
                "endpoint": endpoint,
                "method": method,
                "status": None,
                "response_time_ms": round(response_time, 2),
                "expected_status": expected_status,
                "success": False,
                "data": None,
                "error": str(e)
            }

        self.results.append(result)
        return result

    async def run_all_tests(self):
        """Run all API tests."""
        print("🚀 Starting comprehensive API performance tests...")
        print(f"Testing against: {self.base_url}")
        print("=" * 80)

        async with aiohttp.ClientSession() as session:
            # Test cases: (method, endpoint, data, expected_status, timeout)
            test_cases = [
                # Health endpoints
                ("GET", "/health", None, 200, 5),
                ("GET", "/api/v1/health/", None, 200, 5),
                ("GET", "/api/v1/health/detailed", None, 200, 10),
                ("GET", "/api/v1/health/readiness", None, 200, 5),
                ("GET", "/api/v1/health/liveness", None, 200, 5),

                # Documentation endpoints
                ("GET", "/docs", None, 200, 5),
                ("GET", "/openapi.json", None, 200, 5),

                # Spending endpoints
                ("GET", "/api/v1/spending/", None, 200, 10),
                ("POST", "/api/v1/spending/process/text", {
                    "text": "coffee 100 baht",
                    "language": "en"
                }, 200, 30),
                ("POST", "/api/v1/spending/process/text", {
                    "text": "กาแฟ 150 บาท",
                    "language": "th"
                }, 200, 30),
                ("POST", "/api/v1/spending/", {
                    "amount": 100.0,
                    "currency": "THB",
                    "merchant": "Test Merchant",
                    "category": "Food & Dining",
                    "payment_method": "Cash",
                    "description": "Test spending entry",
                    "occurred_at": "2024-01-01T12:00:00Z"
                }, 201, 10),

                # AI Learning endpoints
                ("GET", "/api/v1/ai/insights", None, 200, 15),
                ("GET", "/api/v1/ai/improvement-suggestions", None, 200, 15),
                ("GET", "/api/v1/ai/confidence-calibration", None, 200, 10),

                # Category Mapping endpoints
                ("GET", "/api/v1/mappings/", None, 200, 10),
                ("POST", "/api/v1/mappings/test", {
                    "text": "restaurant",
                    "language": "en"
                }, 200, 15),
                ("GET", "/api/v1/mappings/analytics", None, 200, 10),

                # Smart Insights endpoints
                ("GET", "/api/v1/insights/", None, 200, 20),
                ("GET", "/api/v1/insights/spending-score", None, 200, 15),
                ("GET", "/api/v1/insights/predictions/next-month", None, 200, 20),
                ("GET", "/api/v1/insights/budget-alerts", None, 200, 15),
                ("GET", "/api/v1/insights/recommendations", None, 200, 15),

                # Metrics endpoint
                ("GET", "/metrics", None, 200, 5),
            ]

            # Run tests concurrently for better performance measurement
            tasks = []
            for method, endpoint, data, expected_status, timeout in test_cases:
                task = self.test_endpoint(session, method, endpoint, data, expected_status, timeout)
                tasks.append(task)

            # Execute all tests
            await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        self.analyze_results()

    def analyze_results(self):
        """Analyze test results and provide performance insights."""
        print("\n📊 API Performance Analysis")
        print("=" * 80)

        successful_tests = [r for r in self.results if r["success"]]
        failed_tests = [r for r in self.results if not r["success"]]

        print(f"✅ Successful tests: {len(successful_tests)}/{len(self.results)}")
        print(f"❌ Failed tests: {len(failed_tests)}")

        if successful_tests:
            response_times = [r["response_time_ms"] for r in successful_tests]
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)

            print(f"\n⏱️  Response Time Statistics:")
            print(f"   Average: {avg_response_time:.2f}ms")
            print(f"   Minimum: {min_response_time:.2f}ms")
            print(f"   Maximum: {max_response_time:.2f}ms")

            # Identify slow endpoints (> 5000ms)
            slow_endpoints = [r for r in successful_tests if r["response_time_ms"] > 5000]
            if slow_endpoints:
                print(f"\n🐌 Slow endpoints (>5s):")
                for endpoint in slow_endpoints:
                    print(f"   {endpoint['method']} {endpoint['endpoint']}: {endpoint['response_time_ms']:.2f}ms")

            # Identify very slow endpoints (> 10000ms)
            very_slow_endpoints = [r for r in successful_tests if r["response_time_ms"] > 10000]
            if very_slow_endpoints:
                print(f"\n🚨 Very slow endpoints (>10s):")
                for endpoint in very_slow_endpoints:
                    print(f"   {endpoint['method']} {endpoint['endpoint']}: {endpoint['response_time_ms']:.2f}ms")

        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   {test['method']} {test['endpoint']}: {test['error']}")

        # Detailed results
        print(f"\n📋 Detailed Results:")
        print("-" * 80)
        for result in sorted(self.results, key=lambda x: x.get("response_time_ms", 0)):
            status_icon = "✅" if result["success"] else "❌"
            response_time = result["response_time_ms"]
            endpoint = f"{result['method']} {result['endpoint']}"

            if result["success"]:
                print(f"{status_icon} {endpoint:<50} {response_time:>8.2f}ms")
            else:
                print(f"{status_icon} {endpoint:<50} {result['error']}")

        # Performance recommendations
        self.provide_recommendations()

    def provide_recommendations(self):
        """Provide performance optimization recommendations."""
        print(f"\n💡 Performance Optimization Recommendations:")
        print("-" * 80)

        successful_tests = [r for r in self.results if r["success"]]
        if not successful_tests:
            print("❌ No successful tests to analyze")
            return

        # Analyze AI endpoints
        ai_endpoints = [r for r in successful_tests if "/ai/" in r["endpoint"] or "process/text" in r["endpoint"]]
        if ai_endpoints:
            avg_ai_time = sum(r["response_time_ms"] for r in ai_endpoints) / len(ai_endpoints)
            if avg_ai_time > 3000:
                print("🤖 AI Endpoints are slow:")
                print("   - Consider implementing request caching")
                print("   - Optimize Llama model parameters")
                print("   - Add connection pooling for Ollama")
                print("   - Implement async processing for heavy operations")

        # Analyze database endpoints
        db_endpoints = [r for r in successful_tests if "/spending/" in r["endpoint"] and r["method"] == "GET"]
        if db_endpoints:
            avg_db_time = sum(r["response_time_ms"] for r in db_endpoints) / len(db_endpoints)
            if avg_db_time > 1000:
                print("🗄️  Database Endpoints are slow:")
                print("   - Add database indexes")
                print("   - Implement query optimization")
                print("   - Add database connection pooling")
                print("   - Consider read replicas")

        # Analyze insights endpoints
        insights_endpoints = [r for r in successful_tests if "/insights/" in r["endpoint"]]
        if insights_endpoints:
            avg_insights_time = sum(r["response_time_ms"] for r in insights_endpoints) / len(insights_endpoints)
            if avg_insights_time > 2000:
                print("📊 Insights Endpoints are slow:")
                print("   - Implement background processing")
                print("   - Add result caching")
                print("   - Optimize aggregation queries")
                print("   - Consider pre-computed insights")

async def main():
    """Main function to run the API tests."""
    tester = APITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        sys.exit(1)
