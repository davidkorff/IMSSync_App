import azure.functions as func
import json
import logging
import os
from typing import Dict, Any

# Import the existing business logic
from app.api.process_transaction import process_triton_transaction
from app.services.ims.payload_processor_service import get_payload_processor_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        # Log the incoming request
        logger.info(f"Received transaction request")
        
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