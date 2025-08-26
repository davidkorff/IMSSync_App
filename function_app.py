import azure.functions as func
import json
import logging
import logging.handlers
import os
from datetime import datetime
from typing import Dict, Any

# Import the existing business logic
from app.api.process_transaction import process_triton_transaction
from app.services.ims.payload_processor_service import get_payload_processor_service

# Create logs directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Generate log filename with timestamp for this session
log_filename = os.path.join(log_dir, f"azure_func_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging with both file and console handlers
log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# File handler - writes to log file
file_handler = logging.FileHandler(log_filename, mode='w')  # 'w' mode ensures file is reset on restart
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)  # Capture all levels in file

# Console handler - for terminal output
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.handlers.clear()  # Clear any existing handlers
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)
logger.info(f"Azure Functions logging initialized. Log file: {log_filename}")

# Create Function App with function-level auth
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.function_name("httpTrigger1")
@app.route(route="api/triton/transaction/new", methods=["POST"])
async def process_transaction(req: func.HttpRequest) -> func.HttpResponse:
    """
    Process a new transaction from Triton.
    This reuses the exact same business logic as the FastAPI endpoint.
    """
    try:
        # Log the incoming request with more details
        logger.info(f"Received transaction request from {req.headers.get('X-Forwarded-For', req.headers.get('Remote-Addr', 'unknown'))}")
        
        # Parse the JSON payload
        try:
            payload = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON payload"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Log transaction details
        transaction_id = payload.get('transaction_id', 'unknown')
        transaction_type = payload.get('transaction_type', 'unknown')
        logger.info(f"Processing transaction: {transaction_id} - Type: {transaction_type}")
        
        # Process using the existing business logic
        result = process_triton_transaction(payload)
        
        # Log result
        if result["success"]:
            logger.info(f"Successfully processed transaction: {transaction_id}")
            status_code = 200
        else:
            logger.error(f"Failed to process transaction: {transaction_id} - {result.get('message')}")
            status_code = 400
        
        # Return the response
        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=status_code
        )
        
    except Exception as e:
        logger.error(f"Error processing transaction: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": str(e),
                "message": "Internal server error processing transaction"
            }),
            mimetype="application/json",
            status_code=500
        )


@app.function_name("httpTrigger2")
@app.route(route="api/triton/transaction-types", methods=["GET"])
async def get_transaction_types(req: func.HttpRequest) -> func.HttpResponse:
    """Get supported transaction types."""
    try:
        # Get transaction types from the payload processor service
        payload_processor = get_payload_processor_service()
        transaction_types = list(payload_processor.TRANSACTION_TYPES.keys())
        
        return func.HttpResponse(
            json.dumps({
                "transaction_types": transaction_types,
                "descriptions": payload_processor.TRANSACTION_TYPES
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error getting transaction types: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.function_name("httpTrigger3")
@app.route(route="api/triton/status", methods=["GET"])
async def triton_status(req: func.HttpRequest) -> func.HttpResponse:
    """Check Triton API status."""
    logger.debug("Triton status check requested")
    return func.HttpResponse(
        json.dumps({
            "status": "operational",
            "api": "triton",
            "deployment": "azure-functions"
        }),
        mimetype="application/json",
        status_code=200
    )


@app.function_name("httpTrigger4")
@app.route(route="api/ims/status", methods=["GET"])
async def ims_status(req: func.HttpRequest) -> func.HttpResponse:
    """Check IMS API status."""
    logger.debug("IMS status check requested")
    return func.HttpResponse(
        json.dumps({
            "status": "operational",
            "api": "ims",
            "deployment": "azure-functions"
        }),
        mimetype="application/json",
        status_code=200
    )


@app.function_name("httpTrigger5")
@app.route(route="health", methods=["GET"])
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    logger.debug("Health check requested")
    try:
        # Check if we can access configuration
        ims_configured = bool(os.getenv("IMS_ONE_USERNAME"))
        
        return func.HttpResponse(
            json.dumps({
                "status": "healthy",
                "version": "1.0.0",
                "deployment": "azure-functions",
                "ims_configured": ims_configured,
                "endpoints": {
                    "triton": "/api/triton",
                    "ims": "/api/ims"
                }
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "status": "unhealthy",
                "error": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )


@app.function_name("httpTrigger6")
@app.route(route="", methods=["GET"])
async def root(req: func.HttpRequest) -> func.HttpResponse:
    """Root endpoint - basic info."""
    logger.debug("Root endpoint accessed")
    return func.HttpResponse(
        json.dumps({
            "service": "RSG Integration Service",
            "deployment": "Azure Functions",
            "health_check": "/api/health",
            "endpoints": {
                "process_transaction": "/api/triton/transaction/new",
                "transaction_types": "/api/triton/transaction-types",
                "health": "/api/health"
            }
        }),
        mimetype="application/json",
        status_code=200
    )