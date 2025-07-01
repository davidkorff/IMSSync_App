#!/bin/bash

# Test TEST.json with curl
echo "=== Testing TEST.json flow to IMS ==="
echo ""
echo "Sending TEST.json to integration service..."

curl -X POST "http://localhost:8000/api/triton/transaction/new?sync_mode=true" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: triton_test_key" \
  -d @TEST.json \
  | python3 -m json.tool