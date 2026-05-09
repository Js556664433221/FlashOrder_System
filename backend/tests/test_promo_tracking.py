"""
Test script for Promo Code Usage Tracking.

Tests:
1. Create a promo code
2. Create orders with and without promo codes
3. Verify promo stats endpoint returns correct usage count and total discount
"""

import requests
import json

API_BASE = "http://localhost:8002"

HEADERS_SALESMAN = {
    "X-Simulated-Role": "salesman",
    "X-Simulated-User-Id": "2",
    "X-Simulated-Username": "test_salesman"
}

HEADERS_ADMIN = {
    "X-Simulated-Role": "admin",
    "X-Simulated-User-Id": "1",
    "X-Simulated-Username": "admin"
}


def print_header(text):
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")


def print_result(name: str, success: bool, detail: str = ""):
    status = "[PASS]" if success else "[FAIL]"
    print(f"  {status} | {name}")
    if detail:
        print(f"         {detail}")


def get_products():
    """Get available products."""
    response = requests.get(f"{API_BASE}/products/", headers=HEADERS_SALESMAN)
    if response.status_code == 200:
        return response.json()
    return []


def create_promo_code(code: str, discount_type: str = "percentage", value: float = 10):
    """Create a promo code (Admin)."""
    response = requests.post(
        f"{API_BASE}/admin/promo/",
        json={
            "code": code,
            "discount_type": discount_type,
            "value": value,
            "is_active": True
        },
        headers=HEADERS_ADMIN
    )
    return response


def create_order(customer_name: str = "Test Customer", promo_code: str = None):
    """Create an order (optionally with promo code)."""
    products = get_products()
    if not products:
        return None, "No products available", None

    product = products[0]
    order_data = {
        "items": [{"product_id": product["id"], "quantity": 1}],
        "customer_name": customer_name,
        "delivery_method": "Pickup"
    }
    if promo_code:
        order_data["promo_code"] = promo_code

    response = requests.post(
        f"{API_BASE}/orders/",
        json=order_data,
        headers=HEADERS_SALESMAN
    )
    return response, response.text, response.status_code


def get_promo_stats():
    """Get promo code stats (Admin)."""
    response = requests.get(
        f"{API_BASE}/admin/promo/stats",
        headers=HEADERS_ADMIN
    )
    return response.json()


def run_tests():
    print_header("PROMO CODE USAGE TRACKING TEST SUITE")
    print("Testing: Promo code usage tracking and statistics")
    print(f"API Base: {API_BASE}")

    all_passed = True
    test_promo_code = "TESTPROMO123"

    # Test 1: Create promo code
    print_header("TEST 1: Create Promo Code")
    response = create_promo_code(test_promo_code, "percentage", 10)
    if response.status_code == 201:
        promo = response.json()
        print_result("Promo code created", True, f"Code: {promo['code']}, Value: {promo['value']}%")
    elif response.status_code == 400 and "already exists" in response.text:
        print_result("Promo code already exists (OK)", True, "Using existing code")
    else:
        print_result("Failed to create promo", False, f"Status: {response.status_code}")
        all_passed = False

    # Test 2: Place order without promo
    print_header("TEST 2: Place Order WITHOUT Promo Code")
    response, text, status_code = create_order("Customer No Promo")
    if status_code == 200:
        order = response.json()
        print_result("Order created without promo", True, f"Order: {order['order_number']}")
        print_result("Applied promo is null", order.get('applied_promo_id') is None,
                     f"applied_promo_id: {order.get('applied_promo_id')}")
    else:
        print_result("Failed to create order", False, f"Status: {status_code}")
        all_passed = False

    # Test 3: Place order with promo
    print_header("TEST 3: Place Order WITH Promo Code")
    response, text, status_code = create_order("Customer With Promo", test_promo_code)
    if status_code == 200:
        order = response.json()
        promo_applied = order.get('applied_promo_id') is not None
        print_result("Order created with promo", True, f"Order: {order['order_number']}")
        print_result("Promo code ID saved to order", promo_applied,
                     f"applied_promo_id: {order.get('applied_promo_id')}")
        print_result("Discount applied", order.get('discount_amount', 0) > 0,
                     f"discount_amount: {order.get('discount_amount')}")
        if not promo_applied:
            all_passed = False
    else:
        print_result("Failed to create order with promo", False, f"Status: {status_code}, {text[:100]}")
        all_passed = False

    # Test 4: Place another order with promo
    print_header("TEST 4: Place Another Order WITH Promo Code")
    response, text, status_code = create_order("Customer With Promo 2", test_promo_code)
    if status_code == 200:
        order = response.json()
        print_result("Second order with promo created", True, f"Order: {order['order_number']}")
        print_result("Discount applied", order.get('discount_amount', 0) > 0,
                     f"discount_amount: {order.get('discount_amount')}")
    else:
        print_result("Failed to create second order", False, f"Status: {status_code}")
        all_passed = False

    # Test 5: Get promo stats
    print_header("TEST 5: Get Promo Stats")
    try:
        stats = get_promo_stats()
        print_result("Promo stats retrieved", True, f"Total promos: {len(stats)}")

        # Find our test promo
        test_promo_stats = next((p for p in stats if p['code'] == test_promo_code), None)
        if test_promo_stats:
            print_result("Test promo found in stats", True,
                        f"Code: {test_promo_stats['code']}")
            print_result("Usage count >= 2", test_promo_stats['usage_count'] >= 2,
                        f"Usage count: {test_promo_stats['usage_count']}")
            print_result("Total discount given > 0", test_promo_stats['total_discount_given'] > 0,
                        f"Total discount: {test_promo_stats['total_discount_given']}")
        else:
            print_result("Test promo not in stats", False, "Promo may not have been used")
            all_passed = False

        # Print all stats for review
        print_header("ALL PROMO STATS")
        for promo in stats:
            print(f"  {promo['code']}: {promo['usage_count']} uses, -{promo['total_discount_given']:.2f} total discount")

    except Exception as e:
        print_result("Failed to get promo stats", False, str(e))
        all_passed = False

    # Summary
    print_header("TEST SUMMARY")
    if all_passed:
        print("  [ALL TESTS PASSED]")
        print("  Promo code usage tracking is working correctly!")
    else:
        print("  [SOME TESTS FAILED]")
        print("  Please review the failed tests above.")

    print()
    return all_passed


if __name__ == "__main__":
    try:
        run_tests()
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot connect to API at", API_BASE)
        print("  Make sure the backend server is running on port 8002")
        print("  Start with: uvicorn app.main:app --reload --port 8002")
    except Exception as e:
        print(f"\n[ERROR] {e}")