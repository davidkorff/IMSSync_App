#!/bin/bash
# Test script to validate Docker setup

echo "=== Docker Setup Validation ==="
echo ""

# Check files exist
echo "Checking required files..."
files=("Dockerfile" "docker-compose.prod.yml" "deploy.sh" "ims-integration.service" ".env.example")
missing=0

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file MISSING"
        missing=$((missing + 1))
    fi
done

echo ""
echo "Checking monitoring configuration..."
if [ -f "monitoring/prometheus.yml" ]; then
    echo "✓ Prometheus config exists"
else
    echo "✗ Prometheus config MISSING"
fi

echo ""
echo "Checking new monitoring code..."
if [ -f "app/core/monitoring.py" ]; then
    echo "✓ Monitoring module exists"
    grep -q "track_transaction_start" app/core/monitoring.py && echo "✓ Monitoring functions present"
else
    echo "✗ Monitoring module MISSING"
fi

echo ""
echo "Checking enhanced routes..."
if grep -q "get_health_status" app/api/routes.py; then
    echo "✓ Enhanced health check present"
fi
if grep -q "/metrics" app/api/routes.py; then
    echo "✓ Metrics endpoint present"
fi

echo ""
if [ $missing -eq 0 ]; then
    echo "✅ All files present - ready for Docker deployment!"
    echo ""
    echo "To deploy:"
    echo "1. Ensure Docker is installed"
    echo "2. Copy .env.example to .env and configure"
    echo "3. Run: sudo ./deploy.sh"
else
    echo "❌ Some files missing - please check above"
fi