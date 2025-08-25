#!/usr/bin/env python3
"""
Test script to demonstrate the new bulk testing features
"""

import csv
import json
from datetime import datetime

def create_sample_csv():
    """Create a sample CSV file for testing"""
    sample_file = "test_transactions_sample.csv"
    
    # Sample data with different transaction types
    sample_data = [
        {
            "opportunity_id": "12345",
            "record_type": "Opportunity",
            "record_id": "12345",
            "transaction_type": "bind",
            "payload": json.dumps({
                "transaction_id": "abc123de-4567-89ef-0123-456789abcdef",
                "prior_transaction_id": None,
                "opportunity_id": 12345,
                "policy_number": "TEST-12345-2025",
                "expiring_policy_number": None,
                "midterm_endt_id": None,
                "insured_name": "Test Company 1",
                "producer_name": "John Doe",
                "underwriter_name": "Jane Smith",
                "base_premium": 5000,
                "transaction_type": "bind",
                "effective_date": "01/01/2025",
                "expiration_date": "01/01/2026"
            })
        },
        {
            "opportunity_id": "12345",
            "record_type": "Opportunity",
            "record_id": "12345",
            "transaction_type": "issue",
            "payload": json.dumps({
                "transaction_id": "def456ab-7890-12cd-3456-789012cdefab",
                "prior_transaction_id": "abc123de-4567-89ef-0123-456789abcdef",
                "opportunity_id": 12345,
                "policy_number": "TEST-12345-2025",
                "expiring_policy_number": None,
                "midterm_endt_id": None,
                "insured_name": "Test Company 1",
                "producer_name": "John Doe",
                "underwriter_name": "Jane Smith",
                "base_premium": 5000,
                "transaction_type": "issue",
                "effective_date": "01/01/2025",
                "expiration_date": "01/01/2026"
            })
        },
        {
            "opportunity_id": "67890",
            "record_type": "Quote",
            "record_id": "67890",
            "transaction_type": "bind",
            "payload": json.dumps({
                "transaction_id": "fed321cb-0987-65dc-ba43-210987fedcba",
                "prior_transaction_id": None,
                "opportunity_id": 67890,
                "policy_number": "TEST-67890-2025",
                "expiring_policy_number": "TEST-67890-2024",
                "midterm_endt_id": None,
                "insured_name": "Test Company 2",
                "producer_name": "Alice Johnson",
                "underwriter_name": "Bob Wilson",
                "base_premium": 7500,
                "transaction_type": "bind",
                "effective_date": "02/01/2025",
                "expiration_date": "02/01/2026"
            })
        },
        {
            "opportunity_id": "67890",
            "record_type": "Opportunity",
            "record_id": "67890",
            "transaction_type": "endorsement",
            "payload": json.dumps({
                "transaction_id": "bcd789ef-3210-9876-fedc-ba4321098765",
                "prior_transaction_id": "fed321cb-0987-65dc-ba43-210987fedcba",
                "opportunity_id": 67890,
                "policy_number": "TEST-67890-2025",
                "expiring_policy_number": "TEST-67890-2024",
                "midterm_endt_id": "ENDT-001",
                "insured_name": "Test Company 2",
                "producer_name": "Alice Johnson",
                "underwriter_name": "Bob Wilson",
                "base_premium": 8000,
                "midterm_endt_premium": 500,
                "transaction_type": "endorsement",
                "effective_date": "03/01/2025",
                "expiration_date": "02/01/2026"
            })
        }
    ]
    
    # Write to CSV
    with open(sample_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["opportunity_id", "record_type", "record_id", "transaction_type", "payload"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_data)
    
    print(f"Created sample CSV file: {sample_file}")
    print(f"  Contains {len(sample_data)} test transactions")
    return sample_file

def demonstrate_modifications():
    """Show how the modifications work"""
    print("\n" + "="*60)
    print("DEMONSTRATION OF MODIFICATION FEATURES")
    print("="*60)
    
    # Example payload
    original = {
        "transaction_id": "abc123de-4567-89ef-0123-456789abcdef",
        "prior_transaction_id": "def456ab-7890-12cd-3456-789012cdefab",
        "opportunity_id": 12345,
        "policy_number": "TEST-12345-2025",
        "expiring_policy_number": "TEST-12345-2024",
        "midterm_endt_id": "ENDT-001",
        "producer_name": "Original Producer",
        "underwriter_name": "Original Underwriter"
    }
    
    print("\nOriginal values:")
    print(f"  opportunity_id: {original['opportunity_id']}")
    print(f"  policy_number: {original['policy_number']}")
    print(f"  expiring_policy_number: {original['expiring_policy_number']}")
    print(f"  midterm_endt_id: {original['midterm_endt_id']}")
    print(f"  transaction_id: ...{original['transaction_id'][-10:]}")
    print(f"  prior_transaction_id: ...{original['prior_transaction_id'][-10:]}")
    print(f"  producer_name: {original['producer_name']}")
    print(f"  underwriter_name: {original['underwriter_name']}")
    
    print("\n" + "-"*40)
    print("With parameter=42:")
    print("  opportunity_id: 12345 → 1234542")
    print("  policy_number: TEST-12345-2025 → TEST-12345-202542")
    print("  expiring_policy_number: TEST-12345-2024 → TEST-12345-202442")
    print("  midterm_endt_id: ENDT-001 → ENDT-00142")
    print("  transaction_id: ...89abcdef → ...89000042")
    print("  prior_transaction_id: ...12cdefab → ...12000042")
    
    print("\n" + "-"*40)
    print("With parameter=139:")
    print("  opportunity_id: 12345 → 12345139")
    print("  transaction_id: ...89abcdef → ...89000139")
    print("  prior_transaction_id: ...12cdefab → ...12000139")
    
    print("\n" + "-"*40)
    print("With --names flag:")
    print("  producer_name: Original Producer → Mike Woodworth")
    print("  underwriter_name: Original Underwriter → Christina Rentas")

def main():
    print("\n" + "="*60)
    print("BULK TRANSACTION TESTING - NEW FEATURES DEMO")
    print("="*60)
    
    # Create sample CSV
    sample_file = create_sample_csv()
    
    # Show modification examples
    demonstrate_modifications()
    
    print("\n" + "="*60)
    print("USAGE EXAMPLES")
    print("="*60)
    
    print("\n1. Basic run (no modifications):")
    print(f"   python3 bulk_test_transactions.py '{sample_file}'")
    
    print("\n2. With parameter number 42:")
    print(f"   python3 bulk_test_transactions.py '{sample_file}' -p 42")
    
    print("\n3. With parameter 139 and default names:")
    print(f"   python3 bulk_test_transactions.py '{sample_file}' -p 139 --names")
    
    print("\n4. Step through each transaction interactively:")
    print(f"   python3 bulk_test_transactions.py '{sample_file}' --step")
    
    print("\n5. Step through with parameter and names:")
    print(f"   python3 bulk_test_transactions.py '{sample_file}' -p 42 --names --step")
    
    print("\n6. Process specific rows (2-3) with stepping:")
    print(f"   python3 bulk_test_transactions.py '{sample_file}' --start 2 --end 3 --step")
    
    print("\n7. Run with verbose output:")
    print(f"   python3 bulk_test_transactions.py '{sample_file}' -p 42 --verbose")
    
    print("\n" + "="*60)
    print("OUTPUT FILES")
    print("="*60)
    
    print("\nThe script generates two output files:")
    print("\n1. CSV Output File (bulk_test_output_TIMESTAMP_pNN.csv):")
    print("   - Contains all original CSV columns")
    print("   - Plus: modified_payload (JSON with your modifications)")
    print("   - Plus: processing_status (SUCCESS/FAILED/SKIPPED)")
    print("   - Plus: processing_message (error messages or success info)")
    print("   - Plus: response_data (API response details)")
    print("   - Plus: timestamp (when processed)")
    
    print("\n2. JSON Results File (bulk_test_results_TIMESTAMP_pNN.json):")
    print("   - Summary statistics")
    print("   - Detailed results for each transaction")
    print("   - Success/failure counts")
    
    print("\n" + "="*60)
    print("STEP-THROUGH MODE")
    print("="*60)
    
    print("\nWhen using --step, for each transaction you'll see:")
    print("  - Transaction details (type, IDs, names, premium)")
    print("  - Options:")
    print("    • Press Enter: Process the transaction")
    print("    • Press 's': Skip this transaction")
    print("    • Press 'q': Quit and save results")
    
    print("\n" + "="*60)
    print("For your actual CSV file, use:")
    print("python3 bulk_test_transactions.py 'ims_payloads_from_triton (1).csv' -p 42 --names --step")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()