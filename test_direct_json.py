#!/usr/bin/env python3
"""Direct test with hardcoded JSON data to bypass file loading issues"""

# Hardcode the TEST.json content
test_payload = {
  "umr": None,
  "agreement_number": None,
  "section_number": None,
  "class_of_business": "Home Health Agency",
  "program_name": "Allied Health",
  "policy_number": "GAH-106113-2510172",
  "expiring_policy_number": "GAH-106112-2510172",
  "underwriter_name": "Haley Crocombe",
  "producer_name": "Mike Woodworth",
  "invoice_date": "10/13/2025",
  "policy_fee": 250,
  "surplus_lines_tax": "",
  "stamping_fee": "",
  "other_fee": "",
  "insured_name": "Korff1 LLC",
  "insured_state": "OR",
  "insured_zip": "97078",
  "effective_date": "10/13/2025",
  "expiration_date": "10/13/2026",
  "bound_date": "07/16/2025",
  "opportunity_type": "Renewal",
  "business_type": "individual",
  "status": "bound",
  "limit_amount": "$1,000,000/$3,000,000",
  "limit_prior": "$1,000,000/$3,000,000",
  "deductible_amount": "$1,000",
  "gross_premium": 1714,
  "commission_rate": 17.5,
  "commission_percent": 0,
  "commission_amount": 0,
  "net_premium": 1714,
  "base_premium": 1558,
  "opportunity_id": 106113,
  "expiring_opportunity_id": 106112,
  "midterm_endt_id": None,
  "midterm_endt_description": None,
  "midterm_endt_effective_from": "",
  "midterm_endt_endorsement_number": None,
  "additional_insured": [],
  "address_1": "17229 SW Reem Ln",
  "address_2": "",
  "city": "Beaverton",
  "state": "OR",
  "zip": "97078",
  "transaction_id": "f44dd12c-ac11-432f-84e7-4245f346d596",
  "prior_transaction_id": None,
  "transaction_type": "bind",
  "transaction_date": "2025-07-16T14:09:23.522+00:00",
  "source_system": "triton"
}

# Now run the test
print("Testing bind with invoice data retrieval...")
print(f"Transaction ID: {test_payload['transaction_id']}")
print(f"Policy Number: {test_payload['policy_number']}")

try:
    from app.services.transaction_handler import get_transaction_handler
    
    handler = get_transaction_handler()
    success, results, message = handler.process_transaction(test_payload)
    
    print(f"\nSuccess: {success}")
    print(f"Message: {message}")
    
    if success and results.get('invoice_data'):
        invoice = results['invoice_data']
        print("\n✓ INVOICE DATA RETRIEVED:")
        print(f"  Invoice Number: {invoice.get('invoice_info', {}).get('invoice_num')}")
        print(f"  Policy Number: {invoice.get('invoice_info', {}).get('policy_number')}")
        print(f"  Premium: ${invoice.get('financial', {}).get('premium'):,.2f}")
        print(f"  Net Premium: ${invoice.get('financial', {}).get('net_premium'):,.2f}")
    elif success:
        print("\n⚠ Bind successful but no invoice data returned")
    
except Exception as e:
    print(f"Error: {e}")
    
    # If it's just the import error, show what would happen
    print("\n" + "="*60)
    print("What the test would do:")
    print("1. Process the bind transaction")
    print("2. After successful bind, call ryan_rptInvoice_WS with the quote GUID")
    print("3. Parse the invoice XML response to JSON")
    print("4. Include invoice data in the response")
    print("="*60)