# PowerShell version of the test curl command

$headers = @{
    "Content-Type" = "application/json"
    "X-API-Key" = "triton_test_key"
}

$body = @{
    "transaction_type" = "NEW BUSINESS"
    "policy_number" = "TEST-POLICY-001"
    "insured_name" = "Test Corporation Inc"
    "insured_address1" = "123 Main Street"
    "insured_city" = "Miami"
    "insured_state" = "FL"
    "insured_zip" = "33101"
    "insured_country" = "US"
    "premium" = 5000
    "effective_date" = "2025-01-01"
    "expiration_date" = "2026-01-01"
    "coverage_type" = "General Liability"
    "limits" = "1000000/2000000"
    "deductible" = 5000
    "producer_code" = "PROD001"
    "underwriter" = "John Smith"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/triton/transaction/new?sync_mode=true" `
    -Method POST `
    -Headers $headers `
    -Body $body