import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from app.services.ims.auth_service import get_auth_service
from app.services.ims.insured_service import get_insured_service
from app.services.ims.data_access_service import get_data_access_service
from app.services.ims.underwriter_service import get_underwriter_service
from app.services.ims.quote_service import get_quote_service
from app.services.ims.quote_options_service import get_quote_options_service
from app.services.ims.payload_processor_service import get_payload_processor_service
from app.services.ims.bind_service import get_bind_service
from app.services.ims.issue_service import get_issue_service

logger = logging.getLogger(__name__)


class TransactionHandler:
    """Handles complete transaction workflow from payload to completion."""
    
    def __init__(self):
        self.auth_service = get_auth_service()
        self.insured_service = get_insured_service()
        self.data_service = get_data_access_service()
        self.underwriter_service = get_underwriter_service()
        self.quote_service = get_quote_service()
        self.quote_options_service = get_quote_options_service()
        self.payload_processor = get_payload_processor_service()
        self.bind_service = get_bind_service()
        self.issue_service = get_issue_service()
    
    def process_transaction(self, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """
        Process a complete transaction from payload reception to completion.
        
        Args:
            payload: The Triton transaction payload
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (success, results, message)
        """
        results = {
            "transaction_id": payload.get("transaction_id"),
            "transaction_type": payload.get("transaction_type"),
            "start_time": datetime.utcnow().isoformat()
        }
        
        try:
            # Validate payload
            is_valid, validation_error = self.payload_processor.validate_payload(payload)
            if not is_valid:
                return False, results, f"Payload validation failed: {validation_error}"
            
            transaction_type = payload.get("transaction_type", "").lower()
            logger.info(f"Processing {transaction_type} transaction: {payload.get('transaction_id')}")
            
            # 1. Authenticate
            auth_success, auth_message = self.auth_service.login()
            if not auth_success:
                return False, results, f"Authentication failed: {auth_message}"
            
            # For issue transactions, we need to find the existing quote
            if transaction_type == "issue":
                policy_number = payload.get("policy_number")
                if not policy_number:
                    return False, results, "Issue transaction requires policy_number"
                
                logger.info(f"Looking up existing quote for policy {policy_number}")
                success, quote_info, message = self.data_service.get_quote_by_policy_number(policy_number)
                if not success:
                    return False, results, f"Failed to find quote: {message}"
                
                quote_guid = quote_info.get("QuoteGuid")
                if not quote_guid:
                    return False, results, "Quote GUID not found for policy"
                
                results["quote_guid"] = quote_guid
                results["insured_guid"] = quote_info.get("InsuredGuid")
                results["policy_number"] = policy_number
                
                # Issue the policy
                logger.info(f"Issuing policy for quote {quote_guid}")
                success, issue_date, message = self.issue_service.issue_policy(quote_guid)
                if not success:
                    return False, results, f"Issue failed: {message}"
                
                results["issue_date"] = issue_date
                results["issue_status"] = "completed"
                results["end_time"] = datetime.utcnow().isoformat()
                results["status"] = "completed"
                
                logger.info(f"Successfully issued policy: {issue_date}")
                
                summary_msg = self._build_summary_message(results, payload)
                return True, results, summary_msg
            
            # For all other transaction types, continue with the normal flow
            # 2. Find/Create Insured
            success, insured_guid, message = self.insured_service.find_or_create_insured(payload)
            if not success:
                return False, results, f"Insured processing failed: {message}"
            results["insured_guid"] = insured_guid
            
            # 3. Find Producer
            success, producer_info, message = self.data_service.process_producer_from_payload(payload)
            if not success:
                return False, results, f"Producer lookup failed: {message}"
            results["producer_contact_guid"] = producer_info.get("ProducerContactGUID")
            results["producer_location_guid"] = producer_info.get("ProducerLocationGUID")
            
            # 4. Find Underwriter
            success, underwriter_guid, message = self.underwriter_service.process_underwriter_from_payload(payload)
            if not success:
                return False, results, f"Underwriter lookup failed: {message}"
            results["underwriter_guid"] = underwriter_guid
            
            # 5. Create Quote
            success, quote_guid, message = self.quote_service.create_quote_from_payload(
                payload=payload,
                insured_guid=results["insured_guid"],
                producer_contact_guid=results["producer_contact_guid"],
                producer_location_guid=results["producer_location_guid"],
                underwriter_guid=results["underwriter_guid"]
            )
            if not success:
                return False, results, f"Quote creation failed: {message}"
            results["quote_guid"] = quote_guid
            
            # 6. Add Quote Options
            success, option_info, message = self.quote_options_service.auto_add_quote_options(quote_guid)
            if not success:
                return False, results, f"Quote options failed: {message}"
            results["quote_option_guid"] = option_info.get("QuoteOptionGuid")
            results["line_guid"] = option_info.get("LineGuid")
            results["line_name"] = option_info.get("LineName")
            results["company_location"] = option_info.get("CompanyLocation")
            
            # 7. Process Payload (Store data, update policy number, register premium)
            success, process_result, message = self.payload_processor.process_payload(
                payload=payload,
                quote_guid=results["quote_guid"],
                quote_option_guid=results["quote_option_guid"]
            )
            if not success:
                return False, results, f"Payload processing failed: {message}"
            
            # 8. Handle transaction-specific operations
            if transaction_type == "bind":
                logger.info(f"Binding quote {quote_guid} for transaction {payload.get('transaction_id')}")
                success, policy_number, message = self.bind_service.bind_quote(quote_guid)
                if not success:
                    return False, results, f"Bind failed: {message}"
                results["bound_policy_number"] = policy_number
                results["bind_status"] = "completed"
                logger.info(f"Successfully bound policy: {policy_number}")
                
            
            # Complete
            results["end_time"] = datetime.utcnow().isoformat()
            results["status"] = "completed"
            
            summary_msg = self._build_summary_message(results, payload)
            return True, results, summary_msg
            
        except Exception as e:
            error_msg = f"Unexpected error in transaction processing: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results["error"] = str(e)
            results["status"] = "failed"
            return False, results, error_msg
    
    def _build_summary_message(self, results: Dict[str, Any], payload: Dict[str, Any]) -> str:
        """Build a summary message for the completed transaction."""
        transaction_type = payload.get("transaction_type", "").lower()
        msg_parts = [
            f"Transaction {payload.get('transaction_id')} completed successfully.",
            f"Type: {transaction_type}",
            f"Insured: {payload.get('insured_name')}",
            f"Quote: {results.get('quote_guid')}",
            f"Premium: ${payload.get('net_premium', 0):,.2f}"
        ]
        
        if transaction_type == "bind" and results.get("bound_policy_number"):
            msg_parts.append(f"Bound Policy Number: {results.get('bound_policy_number')}")
        elif transaction_type == "issue" and results.get("issue_date"):
            msg_parts.append(f"Issue Date: {results.get('issue_date')}")
            msg_parts.append(f"Policy Number: {payload.get('policy_number')}")
        else:
            msg_parts.append(f"Policy Number (stored): {payload.get('policy_number')}")
        
        return " | ".join(msg_parts)


# Singleton instance
_transaction_handler = None


def get_transaction_handler() -> TransactionHandler:
    """Get singleton instance of transaction handler."""
    global _transaction_handler
    if _transaction_handler is None:
        _transaction_handler = TransactionHandler()
    return _transaction_handler