#!/bin/bash
# Fix the import error in the service

echo "Fixing import error in workflow_orchestrator.py..."

# The file to fix
FILE="/opt/IMSSync_App/app/services/ims/workflow_orchestrator.py"

# Make a backup
cp "$FILE" "$FILE.backup" 2>/dev/null

# Fix the import
sed -i 's/from app.services.ims.invoice_service import IMSInvoiceService/from app.services.ims.invoice_service import InvoiceService as IMSInvoiceService/' "$FILE"

echo "✅ Import fixed!"
echo ""
echo "Now try running the service again:"
echo "python3 -m uvicorn app.main:app --port 8001 --reload"