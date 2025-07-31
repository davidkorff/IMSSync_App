#!/bin/bash
# Setup script for Triton integration test environment

echo "=================================================="
echo "Triton Integration Test Environment Setup"
echo "=================================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "1. Checking Python installation..."
python3 --version
if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

echo ""
echo "2. Setting up Python environment..."
export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}"
echo "   PYTHONPATH set to include: $SCRIPT_DIR"

echo ""
echo "3. Checking for virtual environment..."
if [ -d "venv" ]; then
    echo "   Found existing virtual environment"
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
    echo "   Virtual environment activated"
else
    echo "   No virtual environment found"
    echo "   Create one with: python3 -m venv venv"
fi

echo ""
echo "4. Installing dependencies..."
if [ -f "requirements.txt" ]; then
    echo "   Installing from requirements.txt..."
    pip install -r requirements.txt --quiet
    if [ $? -eq 0 ]; then
        echo "   ✓ Dependencies installed successfully"
    else
        echo "   ✗ Failed to install some dependencies"
    fi
else
    echo "   Warning: requirements.txt not found"
fi

echo ""
echo "5. Checking .env file..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "   Creating .env from .env.example..."
        cp .env.example .env
        echo "   ✓ Created .env file - please update with your credentials"
    else
        echo "   Warning: No .env or .env.example found"
    fi
else
    echo "   ✓ .env file exists"
fi

echo ""
echo "6. Checking test files..."
test_files=(
    "test_3_new_business_bind.py"
    "test_3_new_business_bind_v2.py"
    "test_api_client.py"
    "test_runner.py"
    "test.json"
)

for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file (not found)"
    fi
done

echo ""
echo "7. Testing imports..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    import dotenv
    print('   ✓ dotenv')
except: 
    print('   ✗ dotenv (install with: pip install python-dotenv)')
try:
    import requests
    print('   ✓ requests')
except:
    print('   ✗ requests')
try:
    import lxml
    print('   ✓ lxml')
except:
    print('   ✗ lxml')
try:
    import zeep
    print('   ✓ zeep')
except:
    print('   ✗ zeep')
"

echo ""
echo "=================================================="
echo "Setup complete!"
echo ""
echo "To run tests:"
echo "  1. Without JSON: python3 test_3_new_business_bind_v2.py"
echo "  2. With JSON:    python3 test_3_new_business_bind_v2.py --json test.json"
echo "  3. Using runner: python3 test_runner.py --json test.json"
echo "  4. API test:     python3 test_api_client.py --json test.json"
echo ""
echo "If you still have issues, try:"
echo "  - Create virtual env: python3 -m venv venv"
echo "  - Activate it: source venv/bin/activate"
echo "  - Install deps: pip install -r requirements.txt"
echo "=================================================="