"""Test script to validate API client functionality"""
import api_client

print("Testing API Client...")
print("=" * 50)

# Test 1: Get available companies
print("\n1. Fetching available companies...")
companies = api_client.get_available_companies()
print(f"   Available companies: {companies[:5]}..." if len(companies) > 5 else f"   Available companies: {companies}")

if companies:
    # Test 2: Get history for first company
    first_company = companies[0]
    print(f"\n2. Fetching history for '{first_company}'...")
    history = api_client.get_company_history(first_company)
    
    if history:
        print(f"   Records found: {len(history)}")
        print(f"   First record keys: {list(history[0].keys())[:5]}")
        print(f"   First record sample:")
        for key, value in history[0].items():
            if isinstance(value, (list, dict)):
                print(f"      {key}: {type(value).__name__} (length={len(value) if isinstance(value, (list, dict)) else 'N/A'})")
            else:
                print(f"      {key}: {value}")
    else:
        print("   No history data returned")
else:
    print("   No companies available")

# Test 3: Specific test for "14D" as mentioned in PLAN.md
print("\n3. Testing specific symbol '14D'...")
try:
    history_14d = api_client.get_company_history("14D")
    if history_14d:
        print(f"   [OK] Successfully fetched history for 14D")
        print(f"   First record keys: {list(history_14d[0].keys())}")
    else:
        print(f"   [FAIL] No data for 14D")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n" + "=" * 50)
print("API Client validation complete!")
