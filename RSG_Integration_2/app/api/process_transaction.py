import logging
from typing import Dict, Any

from app.services.transaction_handler import get_transaction_handler

logger = logging.getLogger(__name__)


def process_triton_transaction(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a transaction from Triton.
    
    This is the main entry point that will be called by the API endpoint.
    It handles the complete workflow automatically based on transaction type.
    
    Args:
        payload: The Triton transaction payload
        
    Returns:
        Dict containing the processing results
    """
    try:
        # Get the transaction handler
        handler = get_transaction_handler()
        
        # Process the transaction
        success, results, message = handler.process_transaction(payload)
        
        if success:
            return {
                "success": True,
                "message": message,
                "data": results
            }
        else:
            return {
                "success": False,
                "message": message,
                "data": results,
                "error": results.get("error")
            }
            
    except Exception as e:
        logger.error(f"Fatal error processing transaction: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Fatal error: {str(e)}",
            "error": str(e)
        }