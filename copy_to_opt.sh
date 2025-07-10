#!/bin/bash
# Copy the simplified integration files to /opt/IMSSync_App

echo "Copying simplified integration files..."

# Source directory (current)
SRC="/mnt/c/Users/david/OneDrive/Documents/RSG/RSG Integration"

# Target directory
DEST="/opt/IMSSync_App"

# Copy the new simplified files
echo "📁 Copying new processor and client..."
cp "$SRC/app/services/triton_processor.py" "$DEST/app/services/" 2>/dev/null
cp "$SRC/app/services/ims_client.py" "$DEST/app/services/" 2>/dev/null
cp "$SRC/app/config/triton_config.py" "$DEST/app/config/" 2>/dev/null

# Copy the updated route
echo "📁 Copying updated routes..."
cp "$SRC/app/api/source_routes.py" "$DEST/app/api/" 2>/dev/null

# Fix the import in workflow_orchestrator
echo "🔧 Fixing import error..."
sed -i 's/from app.services.ims.invoice_service import IMSInvoiceService/from app.services.ims.invoice_service import InvoiceService as IMSInvoiceService/' "$DEST/app/services/ims/workflow_orchestrator.py" 2>/dev/null

echo "✅ Files copied and import fixed!"
echo ""
echo "Now run:"
echo "cd /opt/IMSSync_App"
echo "python3 -m uvicorn app.main:app --port 8001 --reload"