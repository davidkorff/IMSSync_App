#!/bin/bash

echo "=================================="
echo "Testing Invoice API Endpoint"
echo "=================================="

# Base URL - adjust if needed
BASE_URL="http://localhost:7071"

echo ""
echo "1. Test with no parameters (should return 400):"
curl -X GET "$BASE_URL/api/triton/invoice" -v

echo ""
echo ""
echo "2. Test with quote_guid:"
# Replace with actual quote GUID
curl -X GET "$BASE_URL/api/triton/invoice?quote_guid=12345678-1234-1234-1234-123456789012" -v

echo ""
echo ""
echo "3. Test with policy_number:"
# Replace with actual policy number
curl -X GET "$BASE_URL/api/triton/invoice?policy_number=POL-2025-001" -v

echo ""
echo ""
echo "4. Test with opportunity_id:"
# Replace with actual opportunity ID
curl -X GET "$BASE_URL/api/triton/invoice?opportunity_id=OPP-123456" -v

echo ""
echo ""
echo "5. Test with invoice_num:"
# Replace with actual invoice number
curl -X GET "$BASE_URL/api/triton/invoice?invoice_num=1001" -v

echo ""
echo "=================================="
echo "Replace the test values with actual data from your system"
echo "=================================="