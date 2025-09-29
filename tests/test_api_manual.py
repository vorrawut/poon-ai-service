#!/usr/bin/env python3
"""
Manual API testing script to verify all endpoints work as expected.
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import json

from fastapi.testclient import TestClient

# Import the app
from main import app


def test_health_endpoints():
    """Test all health endpoints."""
    print("🏥 Testing Health Endpoints...")

    with TestClient(app) as client:
        # Basic health check
        print("  ✓ Testing basic health check...")
        response = client.get("/api/v1/health/")
        print(f"    Status: {response.status_code}")
        print(f"    Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200

        # Detailed health check
        print("  ✓ Testing detailed health check...")
        response = client.get("/api/v1/health/detailed")
        print(f"    Status: {response.status_code}")
        print(f"    Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200


def test_spending_endpoints():
    """Test all spending endpoints."""
    print("\n💰 Testing Spending Endpoints...")

    with TestClient(app) as client:
        # Get all spending entries (should be empty initially)
        print("  ✓ Testing get all spending entries...")
        response = client.get("/api/v1/spending/")
        print(f"    Status: {response.status_code}")
        if response.status_code == 200:
            print(f"    Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"    Error: {response.text}")

        # Create a spending entry
        print("  ✓ Testing create spending entry...")
        spending_data = {
            "amount": 120.50,
            "merchant": "Test Cafe API",
            "description": "Coffee and pastry via API test",
            "category": "Food & Dining",
            "payment_method": "Credit Card",
        }
        response = client.post("/api/v1/spending/", json=spending_data)
        print(f"    Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"    Response: {json.dumps(result, indent=2)}")
            entry_id = result.get("entry_id")
            if entry_id:
                print(f"    Created entry ID: {entry_id}")
        else:
            print(f"    Error: {response.text}")

        # Test process text endpoint
        print("  ✓ Testing process text...")
        text_data = {
            "text": "I bought coffee for 50 baht at Starbucks using credit card",
            "language": "en",
        }
        response = client.post("/api/v1/spending/process/text", json=text_data)
        print(f"    Status: {response.status_code}")
        if response.status_code == 200:
            print(f"    Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"    Error: {response.text}")


def test_error_handling():
    """Test error handling."""
    print("\n🚨 Testing Error Handling...")

    with TestClient(app) as client:
        # Test invalid endpoint
        print("  ✓ Testing 404 error...")
        response = client.get("/api/v1/nonexistent")
        print(f"    Status: {response.status_code}")

        # Test invalid spending data
        print("  ✓ Testing invalid spending data...")
        invalid_data = {
            "amount": "not_a_number",
            "merchant": "",
        }
        response = client.post("/api/v1/spending/", json=invalid_data)
        print(f"    Status: {response.status_code}")
        print(f"    Error: {response.text}")


def main():
    """Run all API tests."""
    print("🧪 Manual API Testing for Poon AI Service")
    print("=" * 50)

    try:
        test_health_endpoints()
        test_spending_endpoints()
        test_error_handling()

        print("\n✅ All API tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
