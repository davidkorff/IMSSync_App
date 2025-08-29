#!/usr/bin/env python3
"""
Fix JSON formatting in CSV file
Converts Ruby-style values to proper JSON
"""
import csv
import json
import re
import sys

def fix_json_string(json_str):
    """Convert Ruby-style JSON to proper JSON"""
    if not json_str or json_str == '':
        return '{}'
    
    # The CSV reader should have already handled the double-quote escaping
    # So we should have proper quotes, just need to fix nil -> null
    
    # Replace Ruby nil with JSON null
    json_str = re.sub(r'\bnil\b', 'null', json_str)
    
    # Try to parse and validate
    try:
        parsed = json.loads(json_str)
        return json.dumps(parsed)  # Return properly formatted JSON
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse JSON: {e}")
        print(f"  Error position: char {e.pos}")
        print(f"  JSON around error: ...{json_str[max(0,e.pos-20):min(len(json_str),e.pos+20)]}...")
        # Try a more aggressive fix
        # The issue seems to be with how CSV is being parsed
        # Let's try to fix common patterns
        if '""' in json_str:
            # CSV escaped quotes still present - unescape them
            json_str = json_str.replace('""', '"')
            try:
                parsed = json.loads(json_str)
                return json.dumps(parsed)
            except:
                pass
        return json_str

def process_csv(input_file, output_file):
    """Process CSV file and fix JSON in payload column"""
    
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        rows = []
        for i, row in enumerate(reader, 1):
            if 'payload' in row:
                original = row['payload']
                row['payload'] = fix_json_string(original)
                
                # Validate the fixed JSON
                try:
                    json.loads(row['payload'])
                    print(f"Row {i}: ✓ Fixed and validated")
                except json.JSONDecodeError as e:
                    print(f"Row {i}: ✗ Still invalid after fix: {e}")
                    print(f"  Original: {original[:100]}...")
                    print(f"  Fixed: {row['payload'][:100]}...")
            
            rows.append(row)
    
    # Write fixed CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nFixed CSV saved to: {output_file}")
    print(f"Total rows processed: {len(rows)}")

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "Final_Deployment/triton_ims_queued_transactions.csv"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "Final_Deployment/triton_ims_queued_transactions_fixed.csv"
    
    print(f"Processing: {input_file}")
    print(f"Output to: {output_file}")
    
    process_csv(input_file, output_file)