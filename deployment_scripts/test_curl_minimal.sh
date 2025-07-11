#!/bin/bash

# Minimal test payload for Triton new business transaction
curl -X POST "http://localhost:8000/api/triton/transaction/new?sync_mode=true" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: triton_test_key" \
  -d '{
    "transaction_type": "NEW BUSINESS",
    "policy_number": "TEST-POLICY-001",
    "insured_name": "Test Corporation Inc",
    "insured_address1": "123 Main Street",
    "insured_city": "Miami", 
    "insured_state": "FL",
    "insured_zip": "33101",
    "insured_country": "US",
    "premium": 5000,
    "effective_date": "2025-01-01",
    "expiration_date": "2026-01-01",
    "coverage_type": "General Liability",
    "limits": "1000000/2000000",
    "deductible": 5000,
    "producer_code": "PROD001",
    "underwriter": "John Smith"
  }'