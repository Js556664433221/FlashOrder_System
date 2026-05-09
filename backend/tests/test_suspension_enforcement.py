"""
Test script to verify Suspension Enforcement.

Scenario:
1. A salesman places an order successfully
2. Admin suspends the salesman
3. Salesman attempts to place another order (should fail with 403)
4. Admin activates the salesman again
5. Salesman can place orders again

USAGE:
    1. Start the backend server: cd backend && uvicorn app.main:app --reload --port 8002
    2. Run this test: python tests/test_suspension_enforcement.py
"""

import requests
import sys

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


def get_users():
    """Get list of all users."""
    response = requests.get(f"{API_BASE}/admin/users", headers=HEADERS_ADMIN)
    return response.json()


def get_user_status(user_id: int):
    """Get status of a specific user."""
    users = get_users()
    for user in users:
        if user["id"] == user_id:
            return user["status"]
    return None


def toggle_user_status(user_id: int):
    """Toggle a user's status (Admin action)."""
    response = requests.patch(
        f"{API_BASE}/admin/users/{user_id}/status",
        headers=HEADERS_ADMIN
    )
    return response


def get_products():
    """Get available products."""
    response = requests.get(f"{API_BASE}/products/", headers=HEADERS_SALESMAN)
    if response.status_code == 200:
        return response.json()
    return []


def create_order(customer_name: str = "Test Customer", delivery_method: str = "Pickup"):
    """Attempt to create an order."""
    products = get_products()
    if not products:
        return None, "No products available", None

    # Use the first available product
    product = products[0]
    order_data = {
        "items": [{"product_id": product["id"], "quantity": 1}],
        "customer_name": customer_name,
        "delivery_method": delivery_method
    }

    response = requests.post(
        f"{API_BASE}/orders/",
        json=order_data,
        headers=HEADERS_SALESMAN
    )
    return response, response.text, response.status_code


def run_tests():
    print_header("SUSPENSION ENFORCEMENT TEST SUITE")
    print("Testing: User suspension blocks order creation")
    print(f"API Base: {API_BASE}")

    all_passed = True
    salesman_user_id = 2

    # Test 1: Check initial user status
    print_header("TEST 1: Check Initial User Status")
    status = get_user_status(salesman_user_id)
    initial_status = status
    print_result(
        "Salesman user exists",
        status is not None,
        f"Found user with status: {status}"
    )

    # Test 2: Place order while user is Active
    print_header("TEST 2: Place Order (User is Active)")
    response, text, status_code = create_order("Active Customer")
    order_while_active = status_code == 200
    print_result(
        "Order placement succeeds when Active",
        order_while_active,
        f"Status: {status_code}, Response: {text[:100]}..."
    )
    if not order_while_active:
        all_passed = False

    # Test 3: Admin suspends the user
    print_header("TEST 3: Admin Suspends User")
    response = toggle_user_status(salesman_user_id)
    if response.status_code == 200:
        result = response.json()
        new_status = result.get("status")
        print_result(
            "Admin can toggle user status",
            True,
            f"User status changed to: {new_status}"
        )
        print_result(
            "Suspended user has 'Suspended' status",
            new_status == "Suspended",
            f"Status: {new_status}"
        )
    else:
        print_result("Admin toggle failed", False, f"Status: {response.status_code}")
        all_passed = False

    # Test 4: Verify user status in users list
    print_header("TEST 4: Verify User Status Updated")
    current_status = get_user_status(salesman_user_id)
    print_result(
        "User status shows 'Suspended'",
        current_status == "Suspended",
        f"Current status in system: {current_status}"
    )
    if current_status != "Suspended":
        all_passed = False

    # Test 5: Attempt to place order while Suspended
    print_header("TEST 5: Place Order While Suspended (Should Fail)")
    response, text, status_code = create_order("Suspended Customer")
    order_while_suspended = status_code == 403
    print_result(
        "Order blocked with 403 Forbidden",
        order_while_suspended,
        f"Status: {status_code}, Response: {text[:100]}..."
    )
    print_result(
        "Error message is 'Account is suspended'",
        "Account is suspended" in text,
        f"Message: {text}"
    )
    if not order_while_suspended or "Account is suspended" not in text:
        all_passed = False

    # Test 6: Admin reactivates the user
    print_header("TEST 6: Admin Reactivates User")
    response = toggle_user_status(salesman_user_id)
    if response.status_code == 200:
        result = response.json()
        new_status = result.get("status")
        print_result(
            "Admin can reactivate user",
            new_status == "Active",
            f"User status changed to: {new_status}"
        )
    else:
        print_result("Admin reactivate failed", False, f"Status: {response.status_code}")
        all_passed = False

    # Test 7: Verify user is Active again
    print_header("TEST 7: Verify User is Active Again")
    current_status = get_user_status(salesman_user_id)
    print_result(
        "User status shows 'Active'",
        current_status == "Active",
        f"Current status in system: {current_status}"
    )
    if current_status != "Active":
        all_passed = False

    # Test 8: Place order after reactivation
    print_header("TEST 8: Place Order After Reactivation")
    response, text, status_code = create_order("Reactivated Customer")
    order_after_reactivation = status_code == 200
    print_result(
        "Order succeeds after reactivation",
        order_after_reactivation,
        f"Status: {status_code}, Response: {text[:100]}..."
    )
    if not order_after_reactivation:
        all_passed = False

    # Summary
    print_header("TEST SUMMARY")
    if all_passed:
        print("  [ALL TESTS PASSED]")
        print("  Suspension enforcement is working correctly!")
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
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)