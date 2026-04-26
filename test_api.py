from api_client import get_available_companies, get_company_history

print("Available companies (first 10):")
companies = get_available_companies()
print(companies[:10])

print(f"\nTotal companies: {len(companies)}")

print("\nFirst historical record for 14D:")
history = get_company_history("14D")
if history:
    print(history[0])
else:
    print("No data returned")
