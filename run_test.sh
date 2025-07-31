#!/bin/bash
# Test runner script that handles Python environment issues

echo "Checking Python environment..."

# Try to find a Python with the required modules
for PYTHON in python3.9 python3.11 python3.10 python3.12 python3; do
    if command -v $PYTHON &> /dev/null; then
        echo "Testing $PYTHON..."
        if $PYTHON -c "import dotenv" 2>/dev/null; then
            echo "✓ Found working Python: $PYTHON"
            echo "Running test..."
            exec $PYTHON test_3_new_business_bind.py "$@"
        fi
    fi
done

echo "✗ No Python installation found with required modules."
echo ""
echo "The test requires these modules: python-dotenv, requests, lxml, zeep"
echo ""
echo "To fix this, you can:"
echo "1. Install modules for Python 3.12:"
echo "   sudo apt-get update && sudo apt-get install python3-pip"
echo "   python3 -m pip install -r requirements.txt"
echo ""
echo "2. Or use a virtual environment:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
echo "3. Or install Python 3.11:"
echo "   sudo apt-get install python3.11 python3.11-pip"
echo "   python3.11 -m pip install -r requirements.txt"