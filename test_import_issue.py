#!/usr/bin/env python3
"""Test to isolate the import issue"""
import sys
import os

print("1. Script started")

# Add path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
print("2. Path added")

try:
    print("3. About to import test_bind_workflow_base...")
    from test_bind_workflow_base import *
    print("4. Successfully imported test_bind_workflow_base")
except Exception as e:
    print(f"4. FAILED to import test_bind_workflow_base: {e}")
    sys.exit(1)

try:
    print("5. About to import transaction_handler...")
    from app.services.transaction_handler import get_transaction_handler
    print("6. Successfully imported transaction_handler")
except Exception as e:
    print(f"6. FAILED to import transaction_handler: {e}")

print("7. All imports complete")

# Test with and without JSON argument
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--json', type=str)
args = parser.parse_args()

if args.json:
    print(f"8. JSON file specified: {args.json}")
else:
    print("8. No JSON file specified")

print("9. Script completed successfully")