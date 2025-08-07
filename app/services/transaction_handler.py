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
from app.services.ims.unbind_service import get_unbind_service
from app.services.ims.endorsement_service import get_endorsement_service

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
        self.unbind_service = get_unbind_service()
        self.endorsement_service = get_endorsement_service()
    
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
            
            # 2. Store transaction first (no QuoteGuid)
            logger.info("Storing transaction data")
            success, trans_result, message = self.data_service.store_triton_transaction(payload)
            if not success:
                logger.warning(f"Transaction storage warning: {message}")
            else:
                results["transaction_stored"] = trans_result.get("Status", "Unknown")
            
            # 3. Check for rebind if this is a bind transaction
            if transaction_type == "bind":
                logger.info("Checking for existing quote")
                opportunity_id = payload.get("opportunity_id")
                
                if opportunity_id:
                    # Check if quote already exists for this opportunity_id
                    success, quote_info, message = self.data_service.get_quote_by_opportunity_id(opportunity_id)
                    if success and quote_info:
                        # Quote exists - check if already bound
                        quote_guid = quote_info.get("QuoteGuid")
                        logger.info(f"Found existing quote {quote_guid} for opportunity_id {opportunity_id}")
                        
                        # Check bound status
                        success, is_bound, bound_message = self.data_service.check_quote_bound_status(quote_guid)
                        if not success:
                            return False, results, f"Failed to check bound status: {bound_message}"
                        
                        if is_bound:
                            # Policy already bound - error
                            return False, results, "Policy Already Bound"
                        
                        # Quote exists but not bound - proceed to rebind
                        logger.info("Quote exists but not bound - proceeding with rebind")
                        results["rebind"] = True
                        results["quote_guid"] = quote_guid
                        results["quote_option_guid"] = quote_info.get("QuoteOptionGuid")
                        
                        # Process payload to update data and bind
                        success, process_result, message = self.payload_processor.process_payload(
                            payload=payload,
                            quote_guid=quote_guid,
                            quote_option_guid=quote_info.get("QuoteOptionGuid")
                        )
                        if not success:
                            return False, results, f"Payload processing failed: {message}"
                        
                        # Bind the existing quote
                        logger.info(f"Binding existing quote {quote_guid}")
                        success, bind_result, message = self.bind_service.bind_quote(quote_guid)
                        if not success:
                            return False, results, f"Bind failed: {message}"
                        
                        results["bound_policy_number"] = bind_result.get("policy_number")
                        results["bind_status"] = "completed"
                        
                        # Include invoice data if available
                        if bind_result.get("invoice_data"):
                            results["invoice_data"] = bind_result["invoice_data"]
                        results["end_time"] = datetime.utcnow().isoformat()
                        results["status"] = "completed"
                        
                        summary_msg = self._build_summary_message(results, payload)
                        return True, results, summary_msg
                    else:
                        logger.info(f"No existing quote found for opportunity_id {opportunity_id}")
                        results["rebind"] = False
                
                # No existing quote - continue with normal flow to create new quote
            
            # For issue, unbind, and midterm_endorsement transactions, we need to find the existing quote
            elif transaction_type in ["issue", "unbind", "midterm_endorsement"]:
                # First try to find by option_id if provided
                option_id = payload.get("opportunity_id") or payload.get("option_id")
                policy_number = payload.get("policy_number")
                
                if option_id:
                    logger.info(f"Looking up existing quote by option_id: {option_id}")
                    success, quote_info, message = self.data_service.get_quote_by_option_id(int(option_id))
                    if not success and policy_number:
                        # Fall back to policy number if option_id lookup fails and policy_number is provided
                        logger.info(f"Option ID lookup failed, trying policy number: {policy_number}")
                        success, quote_info, message = self.data_service.get_quote_by_policy_number(policy_number)
                elif policy_number:
                    logger.info(f"Looking up existing quote by policy number: {policy_number}")
                    success, quote_info, message = self.data_service.get_quote_by_policy_number(policy_number)
                else:
                    return False, results, f"{transaction_type.capitalize()} transaction requires either option_id or policy_number"
                
                if not success:
                    return False, results, f"Failed to find quote: {message}"
                
                quote_guid = quote_info.get("QuoteGuid")
                if not quote_guid:
                    return False, results, "Quote GUID not found"
                
                results["quote_guid"] = quote_guid
                # Only set these if they came from the full policy number lookup
                if "InsuredGuid" in quote_info:
                    results["insured_guid"] = quote_info.get("InsuredGuid")
                if "PolicyNumber" in quote_info:
                    results["policy_number"] = quote_info.get("PolicyNumber")
                
                if transaction_type == "issue":
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
                    
                elif transaction_type == "unbind":
                    # Unbind the policy
                    logger.info(f"Unbinding policy for quote {quote_guid}")
                    success, message = self.unbind_service.unbind_policy(quote_guid)
                    if not success:
                        return False, results, f"Unbind failed: {message}"
                    
                    results["unbind_status"] = "completed"
                    results["end_time"] = datetime.utcnow().isoformat()
                    results["status"] = "completed"
                    
                    logger.info(f"Successfully unbound policy {results.get('policy_number', policy_number)}")
                
                elif transaction_type == "midterm_endorsement":
                    # Process the endorsement
                    logger.info(f"Processing midterm endorsement for quote {quote_guid}")
                    
                    # Get endorsement details from payload
                    endorsement_premium = payload.get("gross_premium", 0)
                    effective_date = payload.get("midterm_endt_effective_from") or payload.get("effective_date")
                    endorsement_comment = payload.get("midterm_endt_description", "Midterm Endorsement")
                    
                    # Create the endorsement
                    if option_id:
                        # Use opportunity_id if available
                        success, endorsement_result, message = self.endorsement_service.endorse_policy_by_opportunity_id(
                            opportunity_id=int(option_id),
                            endorsement_premium=endorsement_premium,
                            effective_date=effective_date,
                            comment=endorsement_comment,
                            bind_endorsement=True  # Auto-bind endorsement
                        )
                    else:
                        # Fall back to using quote_guid
                        success, endorsement_result, message = self.endorsement_service.endorse_policy_by_quote_guid(
                            quote_guid=quote_guid,
                            endorsement_premium=endorsement_premium,
                            effective_date=effective_date,
                            comment=endorsement_comment,
                            bind_endorsement=True  # Auto-bind endorsement
                        )
                    
                    if not success:
                        return False, results, f"Endorsement failed: {message}"
                    
                    # Update results with endorsement information
                    endorsement_quote_guid = endorsement_result.get("EndorsementQuoteGuid")
                    endorsement_quote_option_guid = endorsement_result.get("QuoteOptionGuid")
                    
                    results["endorsement_quote_guid"] = endorsement_quote_guid
                    results["endorsement_quote_option_guid"] = endorsement_quote_option_guid
                    results["endorsement_number"] = endorsement_result.get("EndorsementNumber")
                    results["endorsement_status"] = "completed"
                    results["endorsement_premium"] = endorsement_premium
                    results["endorsement_effective_date"] = effective_date
                    
                    # Process the payload to register premium (like in bind flow)
                    # This calls spProcessTritonPayload which will call UpdatePremiumHistoricV3
                    if endorsement_quote_guid and endorsement_quote_option_guid:
                        logger.info("Processing endorsement payload to register premium")
                        success, process_result, message = self.payload_processor.process_payload(
                            payload=payload,
                            quote_guid=endorsement_quote_guid,
                            quote_option_guid=endorsement_quote_option_guid
                        )
                        if not success:
                            logger.warning(f"Failed to process endorsement payload: {message}")
                    
                    # Include invoice data if available
                    if endorsement_result.get("InvoiceNumber"):
                        results["invoice_number"] = endorsement_result["InvoiceNumber"]
                    
                    results["end_time"] = datetime.utcnow().isoformat()
                    results["status"] = "completed"
                    
                    logger.info(f"Successfully created endorsement #{endorsement_result.get('EndorsementNumber')} for policy {results.get('policy_number', policy_number)}")
                
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
            
            # 5. Handle renewal logic if needed
            renewal_of_quote_guid = None
            opportunity_type = payload.get("opportunity_type", "").lower()
            
            if opportunity_type == "renewal":
                # Check for expiring policy to link renewal
                expiring_policy_number = payload.get("expiring_policy_number")
                if expiring_policy_number:
                    logger.info(f"Looking up expiring policy: {expiring_policy_number}")
                    success, expiring_quote_info, message = self.data_service.get_quote_by_expiring_policy_number(expiring_policy_number)
                    if success and expiring_quote_info:
                        renewal_of_quote_guid = expiring_quote_info.get("QuoteGuid")
                        logger.info(f"Found expiring quote {renewal_of_quote_guid} for policy {expiring_policy_number}")
                        results["renewal_of_quote_guid"] = renewal_of_quote_guid
                    else:
                        logger.warning(f"No expiring quote found for policy {expiring_policy_number}")
            
            # 6. Create Quote
            success, quote_guid, message = self.quote_service.create_quote_from_payload(
                payload=payload,
                insured_guid=results["insured_guid"],
                producer_contact_guid=results["producer_contact_guid"],
                producer_location_guid=results["producer_location_guid"],
                underwriter_guid=results["underwriter_guid"],
                renewal_of_quote_guid=renewal_of_quote_guid
            )
            if not success:
                return False, results, f"Quote creation failed: {message}"
            results["quote_guid"] = quote_guid
            
            # 7. Add Quote Options
            success, option_info, message = self.quote_options_service.auto_add_quote_options(quote_guid)
            if not success:
                return False, results, f"Quote options failed: {message}"
            results["quote_option_guid"] = option_info.get("QuoteOptionGuid")
            results["line_guid"] = option_info.get("LineGuid")
            results["line_name"] = option_info.get("LineName")
            results["company_location"] = option_info.get("CompanyLocation")
            
            # 8. Process Payload (Store data, update policy number, register premium)
            success, process_result, message = self.payload_processor.process_payload(
                payload=payload,
                quote_guid=results["quote_guid"],
                quote_option_guid=results["quote_option_guid"]
            )
            if not success:
                return False, results, f"Payload processing failed: {message}"
            
            # 9. Handle transaction-specific operations
            if transaction_type == "bind":
                logger.info(f"Binding quote {quote_guid} for transaction {payload.get('transaction_id')}")
                success, bind_result, message = self.bind_service.bind_quote(quote_guid)
                if not success:
                    return False, results, f"Bind failed: {message}"
                
                # Extract policy number and invoice data from bind result
                results["bound_policy_number"] = bind_result.get("policy_number")
                results["bind_status"] = "completed"
                
                # Include invoice data if available
                if bind_result.get("invoice_data"):
                    results["invoice_data"] = bind_result["invoice_data"]
                    logger.info(f"Successfully bound policy: {bind_result.get('policy_number')} with invoice data")
                else:
                    logger.info(f"Successfully bound policy: {bind_result.get('policy_number')} (no invoice data)")
                
            
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
        elif transaction_type == "unbind" and results.get("unbind_status") == "completed":
            msg_parts.append(f"Policy Number: {payload.get('policy_number')}")
            msg_parts.append("Status: Successfully unbound")
        elif transaction_type == "midterm_endorsement" and results.get("endorsement_status") == "completed":
            msg_parts.append(f"Policy Number: {payload.get('policy_number')}")
            msg_parts.append(f"Endorsement Number: {results.get('endorsement_number')}")
            msg_parts.append(f"Endorsement Premium: ${results.get('endorsement_premium', 0):,.2f}")
            msg_parts.append(f"Effective Date: {results.get('endorsement_effective_date')}")
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