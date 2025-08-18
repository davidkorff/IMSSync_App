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
from app.services.ims.cancellation_service import get_cancellation_service
from app.services.ims.reinstatement_service import get_reinstatement_service

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
        self.cancellation_service = get_cancellation_service()
        self.reinstatement_service = get_reinstatement_service()
    
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
            
            # For issue, unbind, midterm_endorsement, cancellation, and reinstatement transactions, we need to find the existing quote
            elif transaction_type in ["issue", "unbind", "midterm_endorsement", "cancellation", "reinstatement"]:
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
                    # NEW FLOW: Use ProcessFlatEndorsement with proper quote chain handling
                    logger.info(f"Processing midterm endorsement using new flow")
                    
                    # Step 1: Find the latest quote in the chain using opportunity_id
                    if not option_id:
                        return False, results, "Midterm endorsement requires opportunity_id"
                    
                    logger.info(f"Finding latest quote in chain for opportunity_id: {option_id}")
                    success, latest_quote_info, message = self.data_service.get_latest_quote_by_opportunity_id(int(option_id))
                    
                    if not success or not latest_quote_info:
                        return False, results, f"Failed to find latest quote: {message}"
                    
                    latest_quote_guid = latest_quote_info.get("QuoteGuid")
                    control_no = latest_quote_info.get("ControlNo")
                    chain_level = latest_quote_info.get("ChainLevel", 0)
                    
                    logger.info(f"Found latest quote {latest_quote_guid} at chain level {chain_level}")
                    results["original_quote_guid"] = latest_quote_guid
                    results["control_no"] = control_no
                    
                    # Step 2: Get total existing premium from all invoices
                    logger.info(f"Calculating total existing premium for control_no: {control_no}")
                    success, existing_premium, message = self.data_service.get_policy_premium_total(control_no)
                    
                    if not success:
                        logger.warning(f"Failed to get existing premium, using 0: {message}")
                        existing_premium = 0.0
                    
                    # Step 3: Calculate new total premium
                    # Handle string or float values for premium
                    midterm_premium = payload.get("midterm_endt_premium", payload.get("gross_premium", 0))
                    if isinstance(midterm_premium, str):
                        try:
                            new_endorsement_premium = float(midterm_premium) if midterm_premium else 0.0
                        except (ValueError, TypeError):
                            new_endorsement_premium = 0.0
                    else:
                        new_endorsement_premium = float(midterm_premium) if midterm_premium else 0.0
                    
                    total_premium = existing_premium + new_endorsement_premium
                    
                    logger.info(f"Premium calculation - Existing: ${existing_premium:,.2f}, "
                              f"New endorsement: ${new_endorsement_premium:,.2f}, "
                              f"Total: ${total_premium:,.2f}")
                    
                    # Step 4: Get endorsement effective date
                    # First try midterm_endt_effective_from, then transaction_date
                    effective_date_str = payload.get("midterm_endt_effective_from")
                    if not effective_date_str:
                        effective_date_str = payload.get("transaction_date")
                    
                    if effective_date_str:
                        try:
                            # Parse ISO format date
                            from dateutil import parser
                            effective_dt = parser.parse(effective_date_str)
                            effective_date = effective_dt.strftime("%m/%d/%Y")
                        except:
                            # Fallback to current date if parsing fails
                            effective_date = datetime.now().strftime("%m/%d/%Y")
                    else:
                        effective_date = datetime.now().strftime("%m/%d/%Y")
                    
                    endorsement_comment = payload.get("midterm_endt_description", "Midterm Endorsement")
                    
                    # Get midterm_endt_id for duplicate check
                    midterm_endt_id = payload.get("midterm_endt_id")
                    if midterm_endt_id:
                        logger.info(f"Midterm endorsement ID: {midterm_endt_id}")
                    
                    logger.info(f"Using endorsement effective date: {effective_date}")
                    
                    # Step 5: Create endorsement using Triton_ProcessFlatEndorsement wrapper
                    logger.info("Creating endorsement using Triton_ProcessFlatEndorsement wrapper")
                    success, endorsement_result, message = self.endorsement_service.create_flat_endorsement_triton(
                        opportunity_id=int(option_id),
                        endorsement_premium=new_endorsement_premium,
                        effective_date=effective_date,
                        comment=endorsement_comment,
                        midterm_endt_id=midterm_endt_id
                    )
                    
                    if not success:
                        return False, results, f"Failed to create flat endorsement: {message}"
                    
                    # Extract the new endorsement quote guid
                    endorsement_quote_guid = endorsement_result.get("NewQuoteGuid")
                    if not endorsement_quote_guid:
                        return False, results, "ProcessFlatEndorsement did not return NewQuoteGuid"
                    
                    logger.info(f"Created endorsement quote: {endorsement_quote_guid}")
                    
                    # Check if QuoteOptionGuid was returned from the stored procedure
                    endorsement_quote_option_guid = endorsement_result.get("NewQuoteOptionGuid")
                    if endorsement_quote_option_guid:
                        logger.info(f"Retrieved QuoteOptionGuid from stored procedure: {endorsement_quote_option_guid}")
                    
                    # Update results with endorsement information
                    results["endorsement_quote_guid"] = endorsement_quote_guid
                    results["endorsement_number"] = endorsement_result.get("EndorsementNumber")
                    results["original_premium"] = endorsement_result.get("OriginalPremium")
                    results["new_total_premium"] = endorsement_result.get("NewPremium")
                    results["premium_change"] = endorsement_result.get("PremiumChange")
                    results["endorsement_status"] = "unbound"
                    results["endorsement_effective_date"] = effective_date
                    
                    # Step 6: Get quote option for the endorsement (if not already provided)
                    if not endorsement_quote_option_guid:
                        # ProcessFlatEndorsement creates the quote option, so we just need to retrieve it
                        logger.info(f"Getting quote option for endorsement quote {endorsement_quote_guid}")
                        
                        # Simple query to get the QuoteOptionGuid from tblQuoteOptions
                        query = f"""
                            SELECT TOP 1 QuoteOptionGUID 
                            FROM tblQuoteOptions 
                            WHERE QuoteGUID = '{endorsement_quote_guid}'
                        """
                        
                        try:
                            # Try using a simple query instead of the failing stored procedure
                            success, result_xml, message = self.data_service.execute_dataset(
                                "spExecuteSQL",  # Generic SQL execution procedure
                            ["SQL", query]
                        )
                        
                            if success and result_xml:
                                import xml.etree.ElementTree as ET
                                root = ET.fromstring(result_xml)
                                table = root.find('.//Table')
                                if table:
                                    option_guid_elem = table.find('QuoteOptionGUID')
                                    if option_guid_elem is not None and option_guid_elem.text:
                                        endorsement_quote_option_guid = option_guid_elem.text.strip()
                                        logger.info(f"Found quote option: {endorsement_quote_option_guid}")
                        except:
                            # If that doesn't work, try the original method
                            logger.warning("Could not retrieve quote option GUID via query, trying spGetQuoteOptions")
                            success, option_info, message = self.data_service.execute_dataset(
                                "spGetQuoteOptions",
                                ["QuoteGuid", str(endorsement_quote_guid)]
                            )
                            
                            if success and option_info:
                                # Parse to get QuoteOptionGuid
                                import xml.etree.ElementTree as ET
                                try:
                                    root = ET.fromstring(option_info)
                                    table = root.find('.//Table')
                                    if table:
                                        option_guid_elem = table.find('QuoteOptionGuid')
                                        if option_guid_elem is not None and option_guid_elem.text:
                                            endorsement_quote_option_guid = option_guid_elem.text.strip()
                                except:
                                    pass
                    
                    if endorsement_quote_option_guid:
                        results["endorsement_quote_option_guid"] = endorsement_quote_option_guid
                        logger.info(f"Successfully retrieved quote option: {endorsement_quote_option_guid}")
                    else:
                        logger.warning("Could not retrieve quote option GUID - will use placeholder")
                    
                    # Step 7: Apply fees if needed (check criteria)
                    # TODO: Add fee application logic here if needed
                    
                    # Step 8: Process the payload to register in Triton tables
                    if endorsement_quote_guid:
                        # Use the quote option GUID if we have it, otherwise use a placeholder
                        if not endorsement_quote_option_guid:
                            endorsement_quote_option_guid = "00000000-0000-0000-0000-000000000000"
                            logger.warning(f"No QuoteOptionGuid found, using placeholder: {endorsement_quote_option_guid}")
                        
                        logger.info(f"Processing endorsement payload to register in Triton tables")
                        logger.info(f"  QuoteGuid: {endorsement_quote_guid}")
                        logger.info(f"  QuoteOptionGuid: {endorsement_quote_option_guid}")
                        
                        success, process_result, message = self.payload_processor.process_payload(
                            payload=payload,
                            quote_guid=endorsement_quote_guid,
                            quote_option_guid=endorsement_quote_option_guid
                        )
                        if not success:
                            logger.error(f"Failed to process endorsement payload: {message}")
                            logger.warning("Endorsement data NOT stored in tblTritonQuoteData")
                        else:
                            logger.info("Successfully registered endorsement in Triton tables")
                            if process_result:
                                logger.debug(f"Payload processing result: {process_result}")
                    
                    # Step 9: Bind the endorsement
                    logger.info(f"Binding endorsement quote {endorsement_quote_guid}")
                    success, bind_result, message = self.bind_service.bind_quote(endorsement_quote_guid)
                    
                    if success:
                        results["endorsement_policy_number"] = bind_result.get("policy_number")
                        results["endorsement_status"] = "completed"
                        logger.info(f"Successfully bound endorsement: {bind_result.get('policy_number')}")
                    else:
                        logger.error(f"Failed to bind endorsement: {message}")
                        return False, results, f"Endorsement bind failed: {message}"
                    
                    # Step 10: Get invoice data after successful endorsement
                    if endorsement_quote_guid:
                        logger.info(f"Retrieving invoice data for endorsement quote {endorsement_quote_guid}")
                        invoice_success, invoice_data, invoice_message = self.data_service.get_invoice_data(endorsement_quote_guid)
                        
                        if invoice_success:
                            results["invoice_data"] = invoice_data
                            logger.info(f"Successfully retrieved invoice data for endorsement")
                        else:
                            logger.warning(f"Failed to retrieve invoice data for endorsement: {invoice_message}")
                    
                    results["end_time"] = datetime.utcnow().isoformat()
                    results["status"] = "completed"
                    
                    # Convert premium_change to float for formatting
                    premium_change_val = results.get('premium_change', 0)
                    if isinstance(premium_change_val, str):
                        try:
                            premium_change_val = float(premium_change_val)
                        except:
                            premium_change_val = 0
                    
                    logger.info(f"Successfully created endorsement #{results.get('endorsement_number')} "
                              f"for policy {results.get('policy_number', policy_number)} "
                              f"with premium change of ${premium_change_val:,.2f}")
                
                elif transaction_type == "cancellation":
                    # Process the cancellation
                    logger.info(f"Processing cancellation for quote {quote_guid}")
                    
                    # Get cancellation details from payload
                    cancellation_type = payload.get("cancellation_type", "flat")
                    
                    # Use policy_cancellation_date if provided, otherwise use transaction_date
                    cancellation_date_str = payload.get("policy_cancellation_date")
                    if cancellation_date_str:
                        try:
                            # Handle various date formats
                            if '-' in cancellation_date_str:
                                # ISO format (YYYY-MM-DD)
                                from dateutil import parser
                                cancellation_dt = parser.parse(cancellation_date_str)
                                effective_date = cancellation_dt.strftime("%m/%d/%Y")
                            else:
                                # Assume already in MM/DD/YYYY format
                                effective_date = cancellation_date_str
                        except:
                            effective_date = datetime.now().strftime("%m/%d/%Y")
                    else:
                        # Fall back to transaction_date
                        transaction_date_str = payload.get("transaction_date")
                        if transaction_date_str:
                            try:
                                # Parse ISO format date
                                from dateutil import parser
                                transaction_dt = parser.parse(transaction_date_str)
                                effective_date = transaction_dt.strftime("%m/%d/%Y")
                            except:
                                effective_date = datetime.now().strftime("%m/%d/%Y")
                        else:
                            effective_date = datetime.now().strftime("%m/%d/%Y")
                    
                    # Get cancellation specifics
                    reason_code = payload.get("cancellation_reason_code", 30)  # Default to "Insured Request"
                    cancellation_comment = payload.get("cancellation_reason", "Policy Cancellation")
                    
                    # Get refund amount - check both possible field names
                    refund_amount = payload.get("refund_amount") or payload.get("policy_cancellation_premium")
                    if refund_amount:
                        logger.info(f"Using refund amount from payload: ${refund_amount:,.2f}")
                    
                    logger.info(f"Cancellation details - Type: {cancellation_type}, Effective: {effective_date}, Reason: {reason_code}")
                    
                    # Create the cancellation
                    if option_id:
                        # Use opportunity_id if available
                        success, cancellation_result, message = self.cancellation_service.cancel_policy_by_opportunity_id(
                            opportunity_id=int(option_id),
                            cancellation_type=cancellation_type,
                            effective_date=effective_date,
                            reason_code=reason_code,
                            comment=cancellation_comment,
                            refund_amount=refund_amount
                        )
                    else:
                        # Fall back to using quote_guid
                        success, cancellation_result, message = self.cancellation_service.cancel_policy_by_quote_guid(
                            quote_guid=quote_guid,
                            cancellation_type=cancellation_type,
                            effective_date=effective_date,
                            reason_code=reason_code,
                            comment=cancellation_comment,
                            refund_amount=refund_amount
                        )
                    
                    if not success:
                        return False, results, f"Cancellation failed: {message}"
                    
                    # Update results with cancellation information
                    # Handle both field names for the cancellation quote guid
                    cancellation_quote_guid = cancellation_result.get("CancellationQuoteGuid") or cancellation_result.get("NewQuoteGuid")
                    cancellation_quote_option_guid = cancellation_result.get("NewQuoteOptionGuid") or cancellation_result.get("QuoteOptionGuid")
                    
                    if not cancellation_quote_guid:
                        logger.warning("No cancellation quote GUID returned from procedure")
                    else:
                        logger.info(f"Created cancellation quote: {cancellation_quote_guid}")
                        if cancellation_quote_option_guid:
                            logger.info(f"Cancellation QuoteOptionGuid: {cancellation_quote_option_guid}")
                    
                    results["cancellation_quote_guid"] = cancellation_quote_guid
                    results["cancellation_quote_option_guid"] = cancellation_quote_option_guid
                    results["cancellation_type"] = cancellation_type
                    results["cancellation_effective_date"] = effective_date
                    results["refund_amount"] = cancellation_result.get("RefundAmount") or cancellation_result.get("ReturnPremium")
                    results["original_premium"] = cancellation_result.get("PolicyPremium") or cancellation_result.get("OriginalPremium")
                    
                    # Bind the cancellation quote
                    if cancellation_quote_guid:
                        logger.info(f"Binding cancellation quote {cancellation_quote_guid}")
                        success, bind_result, message = self.bind_service.bind_quote(cancellation_quote_guid)
                        
                        if success:
                            results["cancellation_policy_number"] = bind_result.get("policy_number")
                            results["cancellation_status"] = "completed"
                            logger.info(f"Successfully bound cancellation: {bind_result.get('policy_number')}")
                        else:
                            logger.error(f"Failed to bind cancellation: {message}")
                            return False, results, f"Cancellation bind failed: {message}"
                    
                    # Process the payload to register in Triton tables if we have the quote guid
                    if cancellation_quote_guid:
                        logger.info(f"Processing cancellation payload to register in Triton tables")
                        logger.info(f"  QuoteGuid: {cancellation_quote_guid}")
                        logger.info(f"  QuoteOptionGuid: {cancellation_quote_option_guid or '00000000-0000-0000-0000-000000000000'}")
                        
                        # Use the payload processor to store the cancellation data
                        success, processing_result, processing_message = self.payload_processor.process_payload(
                            payload=payload,
                            quote_guid=cancellation_quote_guid,
                            quote_option_guid=cancellation_quote_option_guid or "00000000-0000-0000-0000-000000000000"
                        )
                        
                        if not success:
                            logger.error(f"Failed to process cancellation payload: {processing_message}")
                            logger.warning("Cancellation data NOT stored in tblTritonQuoteData")
                        else:
                            logger.info("Cancellation data stored in tblTritonQuoteData")
                    
                    results["end_time"] = datetime.utcnow().isoformat()
                    results["status"] = "completed"
                    
                    refund_val = results.get('refund_amount', 0)
                    if refund_val:
                        try:
                            refund_val = abs(float(refund_val))
                        except:
                            refund_val = 0
                    else:
                        refund_val = 0
                    
                    logger.info(f"Successfully cancelled policy {results.get('policy_number', policy_number)} "
                              f"with refund of ${refund_val:,.2f}")
                
                elif transaction_type == "reinstatement":
                    # Process the reinstatement
                    logger.info(f"Processing reinstatement for opportunity_id {option_id}")
                    
                    # Get reinstatement details from payload
                    reinstatement_premium = payload.get("gross_premium", 0)
                    
                    # Use transaction_date as the reinstatement effective date
                    transaction_date_str = payload.get("transaction_date")
                    if transaction_date_str:
                        try:
                            # Parse ISO format date
                            from dateutil import parser
                            transaction_dt = parser.parse(transaction_date_str)
                            effective_date = transaction_dt.strftime("%m/%d/%Y")
                        except:
                            effective_date = datetime.now().strftime("%m/%d/%Y")
                    else:
                        effective_date = datetime.now().strftime("%m/%d/%Y")
                    
                    reinstatement_comment = payload.get("reinstatement_reason", "Policy Reinstatement")
                    
                    logger.info(f"Reinstatement details - Premium: ${reinstatement_premium:,.2f}, Effective: {effective_date}")
                    
                    # Create the reinstatement
                    if option_id:
                        # Use opportunity_id if available
                        success, reinstatement_result, message = self.reinstatement_service.reinstate_policy_by_opportunity_id(
                            opportunity_id=int(option_id),
                            reinstatement_premium=reinstatement_premium,
                            effective_date=effective_date,
                            comment=reinstatement_comment
                        )
                    else:
                        # This shouldn't happen for reinstatement, but handle it
                        return False, results, "Reinstatement requires opportunity_id"
                    
                    if not success:
                        return False, results, f"Reinstatement failed: {message}"
                    
                    # Update results with reinstatement information
                    reinstatement_quote_guid = reinstatement_result.get("NewQuoteGuid")
                    
                    results["reinstatement_quote_guid"] = reinstatement_quote_guid
                    results["reinstatement_quote_option_guid"] = reinstatement_result.get("QuoteOptionGuid")
                    results["original_quote_guid"] = reinstatement_result.get("OriginalQuoteGuid")
                    results["cancellation_quote_guid"] = reinstatement_result.get("CancellationQuoteGuid")
                    results["reinstatement_status"] = "unbound"
                    results["reinstatement_effective_date"] = effective_date
                    results["reinstatement_premium"] = reinstatement_result.get("ReinstatementPremium")
                    results["cancellation_refund"] = reinstatement_result.get("CancellationRefund")
                    results["net_premium_change"] = reinstatement_result.get("NetPremiumChange")
                    results["reinstatement_number"] = reinstatement_result.get("ReinstatementNumber")
                    
                    # Process the payload to register in Triton tables
                    if reinstatement_quote_guid and reinstatement_result.get("QuoteOptionGuid"):
                        logger.info("Processing reinstatement payload to register in Triton tables")
                        success, process_result, message = self.payload_processor.process_payload(
                            payload=payload,
                            quote_guid=reinstatement_quote_guid,
                            quote_option_guid=reinstatement_result.get("QuoteOptionGuid")
                        )
                        if not success:
                            logger.warning(f"Failed to process reinstatement payload: {message}")
                    
                    # Bind the reinstatement
                    logger.info(f"Binding reinstatement quote {reinstatement_quote_guid}")
                    success, bind_result, message = self.bind_service.bind_quote(reinstatement_quote_guid)
                    
                    if success:
                        results["reinstatement_policy_number"] = bind_result.get("policy_number")
                        results["reinstatement_status"] = "completed"
                        logger.info(f"Successfully bound reinstatement: {bind_result.get('policy_number')}")
                    else:
                        logger.error(f"Failed to bind reinstatement: {message}")
                        return False, results, f"Reinstatement bind failed: {message}"
                    
                    # Get invoice data after successful reinstatement
                    if reinstatement_quote_guid:
                        logger.info(f"Retrieving invoice data for reinstatement quote {reinstatement_quote_guid}")
                        invoice_success, invoice_data, invoice_message = self.data_service.get_invoice_data(reinstatement_quote_guid)
                        
                        if invoice_success:
                            results["invoice_data"] = invoice_data
                            logger.info(f"Successfully retrieved invoice data for reinstatement")
                        else:
                            logger.warning(f"Failed to retrieve invoice data for reinstatement: {invoice_message}")
                    
                    results["end_time"] = datetime.utcnow().isoformat()
                    results["status"] = "completed"
                    
                    logger.info(f"Successfully reinstated policy {results.get('policy_number', policy_number)}")
                
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
            
            # Convert premium values to float for formatting
            premium_change = results.get('premium_change', 0)
            if isinstance(premium_change, str):
                try:
                    premium_change = float(premium_change)
                except:
                    premium_change = 0
            
            new_total_premium = results.get('new_total_premium', 0)
            if isinstance(new_total_premium, str):
                try:
                    new_total_premium = float(new_total_premium)
                except:
                    new_total_premium = 0
                    
            msg_parts.append(f"Premium Change: ${premium_change:,.2f}")
            msg_parts.append(f"New Total Premium: ${new_total_premium:,.2f}")
            msg_parts.append(f"Effective Date: {results.get('endorsement_effective_date')}")
        elif transaction_type == "cancellation" and results.get("cancellation_status") == "completed":
            msg_parts.append(f"Policy Number: {payload.get('policy_number')}")
            msg_parts.append(f"Cancellation Type: {results.get('cancellation_type')}")
            msg_parts.append(f"Effective Date: {results.get('cancellation_effective_date')}")
            if results.get("refund_amount"):
                msg_parts.append(f"Refund Amount: ${abs(float(results.get('refund_amount', 0))):,.2f}")
        elif transaction_type == "reinstatement" and results.get("reinstatement_status") == "completed":
            msg_parts.append(f"Policy Number: {results.get('reinstatement_policy_number', payload.get('policy_number'))}")
            msg_parts.append(f"Reinstatement Number: {results.get('reinstatement_number')}")
            msg_parts.append(f"Reinstatement Premium: ${results.get('reinstatement_premium', 0):,.2f}")
            msg_parts.append(f"Effective Date: {results.get('reinstatement_effective_date')}")
            if results.get("net_premium_change"):
                msg_parts.append(f"Net Premium Change: ${results.get('net_premium_change', 0):,.2f}")
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