#!/bin/bash
# Run Triton integration tests

echo "=========================================="
echo "TRITON INTEGRATION TEST SUITE"
echo "=========================================="
echo ""

# Check if API is running
echo "Checking API availability..."
curl -s http://localhost:8000/api/triton/status > /dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: API is not running at http://localhost:8000"
    echo "Please start the API first with: python main.py"
    exit 1
fi
echo "✓ API is running"
echo ""

# Run tests
echo "Running test scenarios..."
echo ""

# Test 1: New Business
echo "1. Testing NEW BUSINESS bind..."
python test_triton_realistic.py test_new_business.json
echo ""

# Test 2: Renewal
echo "2. Testing RENEWAL bind..."
python test_triton_realistic.py test_renewal.json
echo ""

# Test 3: Rebind (should detect existing)
echo "3. Testing REBIND detection..."
python test_triton_realistic.py test_rebind.json
echo ""

# Test 4: Issue
echo "4. Testing ISSUE transaction..."
python test_triton_realistic.py test_issue.json
echo ""

# Test 5: Real data
echo "5. Testing with REAL Triton data..."
python test_triton_realistic.py TEST.json Test2.json
echo ""

# Compare results
echo "=========================================="
echo "COMPARING ALL RESULTS"
echo "=========================================="
python test_triton_realistic.py --compare test_new_business.json test_renewal.json test_rebind.json test_issue.json TEST.json Test2.json

echo ""
echo "Tests completed. Check log files for details."