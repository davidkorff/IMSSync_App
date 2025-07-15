#!/usr/bin/env python3
"""Verify the latest changes to IMS integration"""

import os
import sys

# Add the app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.ims_client import IMSClient

# Read the create_quote method
with open('app/services/ims_client.py', 'r') as f:
    content = f.read()
    
# Find the create_quote method
start = content.find('def create_quote(')
end = content.find('\n    def ', start + 1)
method = content[start:end]

# Check for key elements
print("Verification of create_quote method:")
print("=" * 50)

checks = [
    ("RiskInformation field", "'RiskInformation':" in method),
    ("AccountNumber field", "'AccountNumber':" in method),
    ("AdditionalInformation field", "'AdditionalInformation':" in method),
    ("ProgramID field", "'ProgramID':" in method),
    ("Passing quote object directly", "service.AddQuote(\n                quote," in method),
    ("BusinessType in RiskInformation", "'BusinessType': 9" in method)
]

all_passed = True
for check_name, passed in checks:
    status = "✓" if passed else "✗"
    print(f"{status} {check_name}")
    if not passed:
        all_passed = False

print("=" * 50)
if all_passed:
    print("✓ All checks passed! The method should include all required fields.")
else:
    print("✗ Some checks failed. Review the create_quote method.")

# Show the AddQuote call
print("\nAddQuote call:")
print("-" * 50)
call_start = method.find("result = service.AddQuote(")
call_end = method.find(")", call_start) + 1
print(method[call_start:call_end])