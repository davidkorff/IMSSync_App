#!/usr/bin/env python3
"""
Script to create duplicates of test JSON files with updated IDs
Usage: python create_test_files.py <number>
Example: python create_test_files.py 7
"""
import json
import sys
import os
import uuid
from datetime import datetime, timedelta

def generate_new_uuid():
    """Generate a new UUID string"""
    return str(uuid.uuid4())

def update_json_file(input_file, output_file, number_suffix):
    """
    Update a JSON file with new IDs based on the number suffix
    
    Args:
        input_file: Path to the input JSON file
        output_file: Path to the output JSON file
        number_suffix: Number to use for generating new IDs
    """
    # Read the original file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Calculate new opportunity_id (base it on the suffix)
    base_opportunity_id = 106205  # Original from test4 files
    new_opportunity_id = base_opportunity_id + (number_suffix * 1000)
    
    # Calculate new expiring_opportunity_id if present
    if "expiring_opportunity_id" in data and data["expiring_opportunity_id"]:
        base_expiring_id = 98828  # Original from test4 files
        new_expiring_id = base_expiring_id + (number_suffix * 1000)
        data["expiring_opportunity_id"] = new_expiring_id
    
    # Update opportunity_id
    data["opportunity_id"] = new_opportunity_id
    
    # Update policy_number
    if "policy_number" in data and data["policy_number"]:
        # Format: SPG0000089-251 -> SPG0000089-25X where X is the suffix
        parts = data["policy_number"].split('-')
        if len(parts) == 2:
            data["policy_number"] = f"{parts[0]}-{parts[1][:-1]}{number_suffix}"
        else:
            # Fallback: just append the number
            data["policy_number"] = f"{data['policy_number']}-{number_suffix}"
    
    # Update expiring_policy_number if present
    if "expiring_policy_number" in data and data["expiring_policy_number"]:
        # Format: GAH-98828-241111 -> GAH-XXXXX-241111
        parts = data["expiring_policy_number"].split('-')
        if len(parts) >= 2:
            parts[1] = str(new_expiring_id) if "expiring_opportunity_id" in data else f"{parts[1][:-1]}{number_suffix}"
            data["expiring_policy_number"] = '-'.join(parts)
    
    # Generate new transaction_id (always new UUID)
    data["transaction_id"] = generate_new_uuid()
    
    # Generate new prior_transaction_id if present (new UUID)
    if "prior_transaction_id" in data and data["prior_transaction_id"]:
        data["prior_transaction_id"] = generate_new_uuid()
    
    # Update transaction_date to current time
    data["transaction_date"] = datetime.now().isoformat() + "+00:00"
    
    # Update midterm_endt_id if present
    if "midterm_endt_id" in data and data["midterm_endt_id"]:
        data["midterm_endt_id"] = data["midterm_endt_id"] + (number_suffix * 100)
    
    # Ensure midterm_endt_premium is properly formatted if present
    if "midterm_endt_premium" in data and data["midterm_endt_premium"]:
        # Convert to float then back to string to ensure consistent format
        try:
            premium_value = float(data["midterm_endt_premium"])
            data["midterm_endt_premium"] = premium_value  # Store as number, not string
        except (ValueError, TypeError):
            # If conversion fails, leave as is
            pass
    
    # Write the updated file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"Created: {output_file}")
    print(f"  - opportunity_id: {new_opportunity_id}")
    print(f"  - policy_number: {data.get('policy_number', 'N/A')}")
    print(f"  - transaction_id: {data['transaction_id']}")
    print()

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python create_test_files.py <number>")
        print("Example: python create_test_files.py 7")
        sys.exit(1)
    
    try:
        number_suffix = int(sys.argv[1])
    except ValueError:
        print(f"Error: '{sys.argv[1]}' is not a valid number")
        sys.exit(1)
    
    if number_suffix < 1 or number_suffix > 999:
        print("Error: Number must be between 1 and 999")
        sys.exit(1)
    
    # Define the test files to process
    test_files = [
        "test4bind.json",
        "test4bind2.json",
        "test4unbind.json",
        "test4issue.json",
        "test4endt.json",
        "test4cancel.json",
        "test4reinstate.json"
    ]
    
    print(f"\nCreating test files with suffix {number_suffix}...")
    print("=" * 60)
    
    # Process each file
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"Warning: {test_file} not found, skipping...")
            continue
        
        # Create output filename
        # test4bind.json -> test7bind.json (if suffix is 7)
        output_file = test_file.replace("test4", f"test{number_suffix}")
        
        try:
            update_json_file(test_file, output_file, number_suffix)
        except Exception as e:
            print(f"Error processing {test_file}: {e}")
            continue
    
    print("=" * 60)
    print(f"Successfully created test files with suffix {number_suffix}")
    
    # Print summary of the workflow
    print("\nSuggested test workflow:")
    print(f"1. Bind:        python test_3_new_business_bind_v2.py --json test{number_suffix}bind.json")
    print(f"2. Unbind:      python test_6_unbind.py --json test{number_suffix}unbind.json")
    print(f"3. Bind again:  python test_3_new_business_bind_v2.py --json test{number_suffix}bind2.json")
    print(f"4. Issue:       python test_5_issue_policy.py --json test{number_suffix}issue.json")
    print(f"5. Endorsement: python test_7_endorsement.py --json test{number_suffix}endt.json")
    print(f"6. Cancel:      python test_8_cancellation.py --json test{number_suffix}cancel.json")
    print(f"7. Reinstate:   python test_9_reinstatement.py --json test{number_suffix}reinstate.json")

if __name__ == "__main__":
    main()