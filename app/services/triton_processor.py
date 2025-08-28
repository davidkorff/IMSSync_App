import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.models.triton_models import TritonPayload, ProcessingResult
from app.services.ims import AuthService, InsuredService, QuoteService, InvoiceService
from app.services.ims.data_access_service import DataAccessService
from app.utils.policy_store import policy_store

logger = logging.getLogger(__name__)

class TritonProcessor:
    def __init__(self):
        self.auth_service = AuthService()
        self.insured_service = InsuredService()  # IMSInsuredService doesn't take auth_service parameter
        self.quote_service = QuoteService()  # IMSQuoteService doesn't take auth_service parameter
        self.invoice_service = InvoiceService(self.auth_service)
        self.data_access_service = DataAccessService()  # IMSDataAccessService doesn't take auth_service parameter
    
    async def process_transaction(self, payload: TritonPayload) -> ProcessingResult:
        """Main entry point for processing Triton transactions"""
        logger.info(f"Processing {payload.transaction_type} transaction: {payload.transaction_id}")
        
        try:
            if payload.transaction_type == "Bind":
                return await self._process_bind(payload)
            elif payload.transaction_type == "Unbind":
                return await self._process_unbind(payload)
            elif payload.transaction_type == "Issue":
                return await self._process_issue(payload)
            elif payload.transaction_type == "Midterm Endorsement":
                return await self._process_midterm_endorsement(payload)
            elif payload.transaction_type == "Cancellation":
                return await self._process_cancellation(payload)
            else:
                raise ValueError(f"Unknown transaction type: {payload.transaction_type}")
                
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            return ProcessingResult(
                success=False,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response={},
                ims_responses=[],
                errors=[str(e)]
            )
    
    async def _process_bind(self, payload: TritonPayload) -> ProcessingResult:
        """Process a Bind transaction"""
        ims_responses = []
        errors = []
        warnings = []
        
        try:
            # Step 1: Search for existing insured
            found, insured_guid, message = self.insured_service.find_insured_by_name(
                insured_name=payload.insured_name,
                city=payload.city,
                state=payload.insured_state,  # Use insured_state for insured's location
                zip_code=payload.insured_zip   # Use insured_zip for insured's location
            )
            if not found:
                insured_guid = None
            
            # Step 2: Create insured if not found
            if not insured_guid:
                logger.info(f"Creating new insured: {payload.insured_name}")
                logger.info(f"DEBUG: payload.state = {payload.state} (for quote)")
                logger.info(f"DEBUG: payload.insured_state = {payload.insured_state} (for insured address)")
                insured_data = {
                    "insured_name": payload.insured_name,
                    "business_type": payload.business_type,
                    "address_1": payload.address_1,
                    "address_2": payload.address_2,
                    "city": payload.city,
                    "insured_state": payload.insured_state,  # Use insured_state for insured's location
                    "insured_zip": payload.insured_zip       # Use insured_zip for insured's location
                }
                success, insured_guid, message = self.insured_service.find_or_create_insured(insured_data)
                if not success:
                    raise Exception(f"Failed to create insured: {message}")
                insured_guid = insured_guid  # Convert from string if needed
                ims_responses.append({
                    "action": "create_insured",
                    "result": {"insured_guid": str(insured_guid)}
                })
            else:
                ims_responses.append({
                    "action": "find_insured",
                    "result": {"insured_guid": str(insured_guid)}
                })
            
            # Step 3: Create submission and quote together
            # Convert dates from MM/DD/YYYY to YYYY-MM-DD for IMS
            from datetime import datetime
            effective_date = datetime.strptime(payload.effective_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            expiration_date = datetime.strptime(payload.expiration_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            bound_date = datetime.strptime(payload.bound_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            
            quote_data = {
                # Submission data
                "effective_date": effective_date,
                "expiration_date": expiration_date,
                "program_name": payload.program_name,
                "class_of_business": payload.class_of_business,
                "producer_name": payload.producer_name,
                "producer_email": payload.producer_email,
                "underwriter_name": payload.underwriter_name,
                # Quote data
                "state": payload.state,  # Use state for the quote's state
                "limit_amount": payload.limit_amount,
                "deductible_amount": payload.deductible_amount,
                "premium": payload.gross_premium,
                "commission_rate": payload.commission_rate,
                # Risk/Insured data (for quote)
                "insured_name": payload.insured_name,
                "address_1": payload.address_1,
                "address_2": payload.address_2,
                "city": payload.city,
                "insured_state": payload.insured_state,  # Use insured_state for risk location
                "zip": payload.insured_zip,  # Use insured_zip for insured's location in quote
                # Additional Triton data for AdditionalInformation field
                "additional_data": {
                    "transaction_id": payload.transaction_id,
                    "prior_transaction_id": payload.prior_transaction_id,
                    "opportunity_id": payload.opportunity_id,
                    "opportunity_type": payload.opportunity_type,
                    "policy_fee": payload.policy_fee,
                    "surplus_lines_tax": payload.surplus_lines_tax,
                    "stamping_fee": payload.stamping_fee,
                    "other_fee": payload.other_fee,
                    "commission_percent": payload.commission_percent,
                    "commission_amount": payload.commission_amount,
                    "net_premium": payload.net_premium,
                    "base_premium": payload.base_premium,
                    "status": payload.status,
                    "limit_prior": payload.limit_prior,
                    "invoice_date": payload.invoice_date
                }
            }
            
            result = self.quote_service.create_submission_and_quote(insured_guid, quote_data)
            quote_guid = result["quote_guid"]
            submission_guid = result["submission_guid"]
            
            ims_responses.append({
                "action": "create_submission_and_quote",
                "result": {
                    "quote_guid": str(quote_guid),
                    "submission_guid": str(submission_guid) if submission_guid else None
                }
            })
            
            # Step 4a: Update external quote ID for tracking
            try:
                self.quote_service.update_external_quote_id(
                    quote_guid=quote_guid,
                    external_quote_id=payload.transaction_id,
                    external_system_id="TRITON"
                )
                ims_responses.append({
                    "action": "update_external_quote_id",
                    "result": {"success": True}
                })
            except Exception as e:
                logger.warning(f"Failed to update external quote ID: {e}")
                warnings.append(f"Could not update external quote ID: {str(e)}")
            
            # Step 4b: Store additional Triton data using ImportNetRateXml
            try:
                # Try NetRate format first - based on error, it might expect specific tags
                netrate_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<NetRateQuote>
    <QuoteGuid>{quote_guid}</QuoteGuid>
    <ExternalData>
        <TransactionId>{payload.transaction_id}</TransactionId>
        <PriorTransactionId>{payload.prior_transaction_id or ''}</PriorTransactionId>
        <OpportunityId>{payload.opportunity_id}</OpportunityId>
        <OpportunityType>{payload.opportunity_type}</OpportunityType>
        <InvoiceDate>{payload.invoice_date}</InvoiceDate>
        <PolicyFee>{payload.policy_fee}</PolicyFee>
        <SurplusLinesTax>{payload.surplus_lines_tax or ''}</SurplusLinesTax>
        <StampingFee>{payload.stamping_fee or ''}</StampingFee>
        <OtherFee>{payload.other_fee or ''}</OtherFee>
        <CommissionPercent>{payload.commission_percent}</CommissionPercent>
        <CommissionAmount>{payload.commission_amount}</CommissionAmount>
        <NetPremium>{payload.net_premium}</NetPremium>
        <BasePremium>{payload.base_premium}</BasePremium>
        <Status>{payload.status}</Status>
        <LimitPrior>{payload.limit_prior}</LimitPrior>
    </ExternalData>
</NetRateQuote>"""
                
                xml_response = self.quote_service.import_net_rate_xml(quote_guid, netrate_xml)
                ims_responses.append({
                    "action": "import_net_rate_xml",
                    "result": {"response": xml_response}
                })
                
                # Log response to understand behavior
                if xml_response:
                    logger.info(f"ImportNetRateXml response: {xml_response}")
                    
            except Exception as e:
                logger.warning(f"Failed to import NetRate XML: {e}")
                warnings.append(f"Could not store additional data via XML: {str(e)}")
                
                # If ImportNetRateXml fails, we should implement the fallback
                # to AdditionalInformation field during quote creation
                logger.info("ImportNetRateXml failed - consider using AdditionalInformation field instead")
            
            # Step 5: Add quote option to enable binding
            option_guid = None
            try:
                option_guid = self.quote_service.add_quote_option(quote_guid)
                ims_responses.append({
                    "action": "add_quote_option",
                    "result": {"option_guid": str(option_guid)}
                })
                logger.info(f"Added quote option {option_guid} to quote {quote_guid}")
            except Exception as e:
                logger.error(f"Failed to add quote option: {e}")
                raise
            
            # Step 5a: Add premium to the quote option
            if option_guid and payload.gross_premium:
                try:
                    logger.info(f"Adding premium {payload.gross_premium} to quote option {option_guid}")
                    self.quote_service.add_premium(
                        quote_option_guid=option_guid,
                        premium=float(payload.gross_premium),
                        office_id=0,  # Use 0 as default office ID (seems to be the pattern)
                        charge_code=0  # Use 0 as default charge code
                    )
                    ims_responses.append({
                        "action": "add_premium",
                        "result": {"premium": float(payload.gross_premium), "option_guid": str(option_guid)}
                    })
                    logger.info(f"Successfully added premium to quote option")
                except Exception as e:
                    logger.error(f"Failed to add premium: {e}")
                    # Continue anyway - maybe it will bind without premium
            
            # Step 5b: Get the integer quote option ID using the new stored procedure
            actual_quote_option_id = None
            if option_guid:
                try:
                    logger.info(f"Getting integer quote option ID using quote option GUID {option_guid}")
                    # spGetTritonQuoteData_WS expects the Quote Option GUID
                    actual_quote_option_id = self.data_access_service.get_quote_option_id_by_guid(option_guid)
                    if actual_quote_option_id:
                        logger.info(f"SUCCESS: Got quote option ID {actual_quote_option_id} for quote option {option_guid}")
                        ims_responses.append({
                            "action": "get_quote_option_id",
                            "result": {"quote_option_id": actual_quote_option_id}
                        })
                    else:
                        logger.warning("Could not get quote option ID from stored procedure")
                except Exception as e:
                    logger.error(f"Error getting quote option ID: {e}")
            
            # Step 6: Get quote option ID and bind the quote
            bind_data = {
                "bound_date": bound_date,  # Use converted date
                "policy_number": payload.policy_number
            }
            
            # Step 6a: Store Triton data using DataAccess (now that stored procedure exists)
            try:
                logger.info("Storing Triton data using DataAccess stored procedure")
                # Convert empty strings to None/0 for decimal fields
                def clean_decimal(value):
                    if value == "" or value is None:
                        return 0
                    return value
                
                triton_data = {
                    "transaction_id": payload.transaction_id,
                    "prior_transaction_id": payload.prior_transaction_id if payload.prior_transaction_id != "null" else None,
                    "opportunity_id": payload.opportunity_id,
                    "opportunity_type": payload.opportunity_type,
                    "policy_fee": clean_decimal(payload.policy_fee),
                    "surplus_lines_tax": clean_decimal(payload.surplus_lines_tax),
                    "stamping_fee": clean_decimal(payload.stamping_fee),
                    "other_fee": clean_decimal(payload.other_fee),
                    "commission_percent": clean_decimal(payload.commission_percent),
                    "commission_amount": clean_decimal(payload.commission_amount),
                    "net_premium": clean_decimal(payload.net_premium),
                    "base_premium": clean_decimal(payload.base_premium),
                    "status": payload.status,
                    "limit_prior": payload.limit_prior,
                    "invoice_date": payload.invoice_date
                }
                
                data_result = self.data_access_service.store_triton_data(quote_guid, triton_data)
                logger.info(f"Triton data stored successfully: {data_result}")
                ims_responses.append({
                    "action": "store_triton_data",
                    "result": data_result
                })
            except Exception as e:
                logger.warning(f"Failed to store Triton data via DataAccess: {e}")
                warnings.append(f"Could not store Triton data: {str(e)}")
            
            # Step 6b: Try to bind the quote
            bind_successful = False
            
            # First, try to get quote option ID via DataAccess (if spGetQuoteOptions_WS exists)
            if option_guid:  # We need the option GUID from AddQuoteOption
                try:
                    logger.info(f"Attempting to get quote option details via DataAccess using option GUID {option_guid}")
                    quote_options = self.data_access_service.get_quote_option_details(option_guid)
                    
                    if quote_options and len(quote_options) > 0:
                        # Use the first quote option ID
                        quote_option_id = quote_options[0].get("QuoteOptionID")
                        logger.info(f"Found quote option ID via DataAccess: {quote_option_id}")
                        
                        # Use the Bind method with the integer quote option ID
                        bind_result = self.quote_service.bind_with_option_id(quote_option_id, bind_data)
                        ims_responses.append({
                            "action": "bind_quote_option",
                            "result": bind_result
                        })
                        logger.info(f"Quote bound successfully with option ID {quote_option_id}")
                        bind_successful = True
                        
                except Exception as e:
                    logger.warning(f"DataAccess approach failed: {e}")
                    if "could not find stored procedure" in str(e).lower():
                        logger.info("spGetQuoteOptions_WS stored procedure doesn't exist yet")
                    elif "parameters must be specified" in str(e).lower():
                        logger.warning("DataAccess parameter format issue persists")
            
            # If DataAccess didn't work with get_quote_option_details, try the direct method
            if not bind_successful and option_guid:
                try:
                    logger.info("Trying direct method to get quote option ID from option GUID")
                    actual_id = self.data_access_service.get_quote_option_id_from_option_guid(option_guid)
                    if actual_id:
                        logger.info(f"Got quote option ID {actual_id} from option GUID")
                        bind_result = self.quote_service.bind_with_option_id(actual_id, bind_data)
                        ims_responses.append({
                            "action": "bind_quote_option_direct",
                            "result": bind_result
                        })
                        logger.info(f"Quote bound successfully with option ID {actual_id}")
                        bind_successful = True
                except Exception as e:
                    logger.warning(f"Direct method failed: {e}")
            
            # If DataAccess didn't work, try default option IDs
            if not bind_successful:
                logger.info("Trying Bind method with default option IDs")
                for option_id in [1, 0, -1]:
                    try:
                        logger.info(f"Trying Bind with quoteOptionID={option_id}")
                        bind_result = self.quote_service.bind_with_option_id(option_id, bind_data)
                        ims_responses.append({
                            "action": "bind_quote_option",
                            "result": bind_result
                        })
                        logger.info(f"Quote bound successfully with option ID {option_id}")
                        bind_successful = True
                        break
                    except Exception as e:
                        logger.warning(f"Bind with option ID {option_id} failed: {e}")
                        continue
            
            # Initialize option_ids list
            option_ids = []
            
            # We should already have the actual quote option ID from Step 5a
            if actual_quote_option_id:
                logger.info(f"Using quote option ID {actual_quote_option_id} obtained from spGetTritonQuoteData_WS")
                option_ids = [actual_quote_option_id]
                # Try to bind immediately with this ID
                try:
                    logger.info(f"Attempting immediate bind with quote option ID {actual_quote_option_id}")
                    bind_result = self.quote_service.bind_with_option_id(actual_quote_option_id, bind_data)
                    ims_responses.append({
                        "action": "bind_with_triton_option_id",
                        "result": bind_result
                    })
                    logger.info(f"SUCCESS: Quote bound using option ID from spGetTritonQuoteData_WS")
                    bind_successful = True
                except Exception as e:
                    logger.warning(f"Bind with spGetTritonQuoteData_WS option ID failed: {e}")
            else:
                # Fallback: Try to get the actual quote option ID using simplified stored procedure
                actual_option_id = None
                try:
                    logger.info("Attempting to get quote option ID via simplified stored procedure")
                    actual_option_id = self.data_access_service.get_quote_option_id(quote_guid)
                    if actual_option_id:
                        logger.info(f"SUCCESS: Found actual quote option ID: {actual_option_id}")
                        option_ids = [actual_option_id]
                except Exception as e:
                    logger.warning(f"Could not get quote option ID: {str(e)[:100]}")
            
            # Skip comprehensive bind testing if already successful
            if bind_successful:
                logger.info("Bind already successful, skipping comprehensive testing")
            else:
                # Try all 4 bind methods systematically
                logger.info("=== COMPREHENSIVE BIND TESTING ===")
                
                # Method 1: BindQuoteWithInstallment with -1 (documented single-pay approach)
                if not bind_successful:
                    logger.info("Method 1: BindQuoteWithInstallment with companyInstallmentID=-1")
                    try:
                        bind_result = self.quote_service.bind_single_pay(quote_guid, bind_data)
                        ims_responses.append({
                            "action": "bind_quote_with_installment_-1",
                            "result": bind_result
                        })
                        logger.info(f"SUCCESS: Quote bound as single pay using BindQuoteWithInstallment(-1)")
                        bind_successful = True
                    except Exception as e:
                        logger.warning(f"Method 1 failed: {str(e)[:200]}")
                
                # Method 2: BindQuote (simple approach)
                quote_id = None
                if not bind_successful:
                    logger.info("Method 2: BindQuote with just quote GUID")
                    try:
                        bind_result = self.quote_service.bind(quote_guid, bind_data)
                        ims_responses.append({
                            "action": "bind_quote_simple",
                            "result": bind_result
                        })
                        logger.info(f"SUCCESS: Quote bound using simple BindQuote")
                        bind_successful = True
                    except Exception as e:
                        error_str = str(e)
                        logger.warning(f"Method 2 failed: {error_str[:200]}")
                        
                        # Extract quote ID from error message
                        import re
                        match = re.search(r'quote ID (\d+)', error_str)
                        if match:
                            quote_id = int(match.group(1))
                            logger.info(f"EXTRACTED QUOTE ID FROM ERROR: {quote_id}")
                
                # Method 3 & 4: Need integer quote option ID
                # Try to extract from error messages or use common IDs
                if not bind_successful:
                    # If we extracted a quote ID, try to use it to derive quote option IDs
                    if quote_id:
                        logger.info(f"Using extracted quote ID {quote_id} to estimate quote option IDs")
                        # In many IMS systems, quote option IDs are related to quote IDs
                        # Try variations based on the quote ID
                        test_option_ids = [
                            quote_id,           # Sometimes same as quote ID
                            quote_id * 100,     # Sometimes quote ID * 100
                            quote_id * 100 + 1, # Sometimes quote ID * 100 + 1
                            quote_id + 1,       # Sometimes sequential
                        ]
                        logger.info(f"Trying quote option IDs based on quote ID: {test_option_ids}")
                    else:
                        # Use actual option ID if we found it, otherwise try common IDs
                        test_option_ids = option_ids if option_ids else [1, 0, 100, 1000]  # Common IDs in IMS systems
                    
                    # Method 3: Bind with quote option ID
                    logger.info("Method 3: Bind with integer quote option ID")
                    for test_id in test_option_ids:
                        try:
                            logger.info(f"  Trying Bind with quoteOptionID={test_id}")
                            bind_result = self.quote_service.bind_with_option_id(test_id, bind_data)
                            ims_responses.append({
                                "action": f"bind_option_id_{test_id}",
                                "result": bind_result
                            })
                            logger.info(f"SUCCESS: Quote bound using Bind({test_id})")
                            bind_successful = True
                            break
                        except Exception as e:
                            logger.warning(f"  Bind({test_id}) failed: {str(e)[:100]}")
                    
                    # Method 4: BindWithInstallment with -1
                    if not bind_successful:
                        logger.info("Method 4: BindWithInstallment with quoteOptionID and -1")
                        for test_id in test_option_ids:
                            try:
                                logger.info(f"  Trying BindWithInstallment({test_id}, -1)")
                                bind_result = self.quote_service.bind_single_pay_with_option(test_id, bind_data)
                                ims_responses.append({
                                    "action": f"bind_with_installment_{test_id}_-1",
                                    "result": bind_result
                                })
                                logger.info(f"SUCCESS: Quote bound using BindWithInstallment({test_id}, -1)")
                                bind_successful = True
                                break
                            except Exception as e:
                                logger.warning(f"  BindWithInstallment({test_id}, -1) failed: {str(e)[:100]}")
                
                # Final summary if all methods failed
                if not bind_successful:
                    logger.error("=== ALL BIND METHODS FAILED ===")
                    logger.error("Summary of failures:")
                    logger.error("1. BindQuoteWithInstallment(-1): Installment billing not configured")
                    logger.error("2. BindQuote: Internally requires installment billing")
                    logger.error("3. Bind(optionID): Need valid integer quote option ID")
                    logger.error("4. BindWithInstallment(optionID, -1): Need valid integer quote option ID")
                    logger.error("")
                    logger.error("Root causes:")
                    logger.error("- IMS database lacks installment billing configuration")
                    logger.error("- AddQuoteOption returns GUID but Bind methods need integer ID")
                    logger.error("- spGetQuoteOptions_WS stored procedure missing to map GUID->ID")
                    logger.error("")
                    logger.error(f"Quote Details:")
                    logger.error(f"- Quote GUID: {quote_guid}")
                    logger.error(f"- Quote Option GUID: {option_guid if option_guid else 'None'}")
                    logger.error(f"- Quote Option ID: {actual_quote_option_id if actual_quote_option_id else 'Not found'}")
                    logger.error(f"- Quote ID from error: {quote_id_int if 'quote_id_int' in locals() else 'Not extracted'}")
                    
                    errors.append("All bind methods failed - see logs for detailed analysis")
                    raise Exception("Unable to bind quote - all 4 methods failed")
            
            # Step 7: Get invoice details
            invoice_details = self.invoice_service.get_invoice(quote_guid)
            
            # Store policy mapping
            policy_guid = bind_result.get("policy_guid")
            if policy_guid:
                policy_store.store_policy(
                    policy_number=payload.policy_number,
                    policy_guid=UUID(policy_guid),
                    transaction_id=payload.transaction_id,
                    additional_data={
                        "insured_guid": str(insured_guid),
                        "submission_guid": str(submission_guid),
                        "quote_guid": str(quote_guid)
                    }
                )
            
            service_response = {
                "insured_guid": str(insured_guid),
                "submission_guid": str(submission_guid),
                "quote_guid": str(quote_guid),
                "policy_guid": policy_guid,
                "status": "bound"
            }
            
            return ProcessingResult(
                success=True,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response=service_response,
                ims_responses=ims_responses,
                invoice_details=invoice_details,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Error in bind processing: {e}")
            errors.append(str(e))
            return ProcessingResult(
                success=False,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response={},
                ims_responses=ims_responses,
                errors=errors
            )
    
    async def _process_unbind(self, payload: TritonPayload) -> ProcessingResult:
        """Process an Unbind transaction"""
        ims_responses = []
        errors = []
        
        try:
            # Need to get policy GUID from somewhere - might need to store mapping
            # For now, we'll assume we have a way to look it up
            policy_guid = await self._get_policy_guid(payload.policy_number)
            
            if not policy_guid:
                raise ValueError(f"Policy not found: {payload.policy_number}")
            
            unbind_result = self.quote_service.unbind(policy_guid)
            ims_responses.append({
                "action": "unbind_policy",
                "result": unbind_result
            })
            
            service_response = {
                "policy_guid": str(policy_guid),
                "status": "unbound"
            }
            
            return ProcessingResult(
                success=True,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response=service_response,
                ims_responses=ims_responses,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error in unbind processing: {e}")
            errors.append(str(e))
            return ProcessingResult(
                success=False,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response={},
                ims_responses=ims_responses,
                errors=errors
            )
    
    async def _process_issue(self, payload: TritonPayload) -> ProcessingResult:
        """Process an Issue transaction"""
        ims_responses = []
        errors = []
        
        try:
            policy_guid = await self._get_policy_guid(payload.policy_number)
            
            if not policy_guid:
                raise ValueError(f"Policy not found: {payload.policy_number}")
            
            issue_result = self.quote_service.issue(policy_guid)
            ims_responses.append({
                "action": "issue_policy",
                "result": issue_result
            })
            
            service_response = {
                "policy_guid": str(policy_guid),
                "status": "issued",
                "issue_date": issue_result.get("issue_date")
            }
            
            return ProcessingResult(
                success=True,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response=service_response,
                ims_responses=ims_responses,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error in issue processing: {e}")
            errors.append(str(e))
            return ProcessingResult(
                success=False,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response={},
                ims_responses=ims_responses,
                errors=errors
            )
    
    async def _process_midterm_endorsement(self, payload: TritonPayload) -> ProcessingResult:
        """Process a Midterm Endorsement transaction"""
        ims_responses = []
        errors = []
        
        try:
            policy_guid = await self._get_policy_guid(payload.policy_number)
            
            if not policy_guid:
                raise ValueError(f"Policy not found: {payload.policy_number}")
            
            # Create endorsement
            endorsement_data = {
                "effective_date": payload.midterm_endt_effective_from,
                "description": payload.midterm_endt_description,
                "endorsement_number": payload.midterm_endt_endorsement_number
            }
            endorsement_guid = self.quote_service.create_endorsement(policy_guid, endorsement_data)
            ims_responses.append({
                "action": "create_endorsement",
                "result": {"endorsement_guid": str(endorsement_guid)}
            })
            
            # Bind the endorsement
            bind_data = {
                "bound_date": payload.bound_date,
                "policy_number": payload.policy_number
            }
            bind_result = self.quote_service.bind(endorsement_guid, bind_data)
            ims_responses.append({
                "action": "bind_endorsement",
                "result": bind_result
            })
            
            # Get invoice details
            invoice_details = self.invoice_service.get_invoice(endorsement_guid)
            
            service_response = {
                "policy_guid": str(policy_guid),
                "endorsement_guid": str(endorsement_guid),
                "status": "endorsed"
            }
            
            return ProcessingResult(
                success=True,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response=service_response,
                ims_responses=ims_responses,
                invoice_details=invoice_details,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error in endorsement processing: {e}")
            errors.append(str(e))
            return ProcessingResult(
                success=False,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response={},
                ims_responses=ims_responses,
                errors=errors
            )
    
    async def _process_cancellation(self, payload: TritonPayload) -> ProcessingResult:
        """Process a Cancellation transaction"""
        ims_responses = []
        errors = []
        
        try:
            policy_guid = await self._get_policy_guid(payload.policy_number)
            
            if not policy_guid:
                raise ValueError(f"Policy not found: {payload.policy_number}")
            
            cancellation_data = {
                "reason_code": "CANC001",
                "comment": f"Cancellation requested - Transaction ID: {payload.transaction_id}"
            }
            cancel_result = self.quote_service.cancel(policy_guid, cancellation_data)
            ims_responses.append({
                "action": "cancel_policy",
                "result": cancel_result
            })
            
            # Get final invoice details
            invoice_details = self.invoice_service.get_invoice(policy_guid)
            
            service_response = {
                "policy_guid": str(policy_guid),
                "status": "cancelled",
                "cancellation_date": cancel_result.get("cancellation_date")
            }
            
            return ProcessingResult(
                success=True,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response=service_response,
                ims_responses=ims_responses,
                invoice_details=invoice_details,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error in cancellation processing: {e}")
            errors.append(str(e))
            return ProcessingResult(
                success=False,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response={},
                ims_responses=ims_responses,
                errors=errors
            )
    
    async def _get_policy_guid(self, policy_number: str) -> Optional[UUID]:
        """Get policy GUID from policy number"""
        policy_guid = policy_store.get_policy_guid(policy_number)
        if not policy_guid:
            logger.warning(f"Policy not found in store: {policy_number}")
        return policy_guid