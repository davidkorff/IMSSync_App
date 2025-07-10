import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import xml.etree.ElementTree as ET
from app.services.ims_soap_client import IMSSoapClient
from app.core.config import settings

logger = logging.getLogger(__name__)

class InvoiceService:
    def __init__(self, environment: Optional[str] = None):
        self.environment = environment  # For compatibility, but not used
        self.soap_client = None
        self._initialized = False
        
    def _ensure_initialized(self):
        """Ensure SOAP client is initialized"""
        if not self._initialized:
            # Get config from settings
            config_file = settings.get("ims_config_file", "Development.config")
            environment_config = settings.dict()
            
            self.soap_client = IMSSoapClient(config_file, environment_config)
            
            # Login to IMS
            username = settings.ims_username
            password = settings.ims_password
            
            try:
                self.soap_client.login(username, password)
                self._initialized = True
                logger.info("Invoice service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize invoice service: {str(e)}")
                raise
    
    async def get_invoice_by_policy_number(
        self, 
        policy_number: str,
        include_payment_info: bool = True,
        format_currency: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve invoice data from IMS by policy number
        
        Args:
            policy_number: The policy number to search for
            include_payment_info: Whether to include payment method details
            format_currency: Whether to format currency values
            
        Returns:
            Dictionary containing invoice data formatted for Triton
        """
        self._ensure_initialized()
        
        try:
            # Query IMS for invoice data
            # NOTE: This is pseudo-code for the stored procedure call
            # The actual stored procedure name needs to be determined
            result = self.soap_client.execute_data_set(
                "GetLatestInvoiceByPolicy",  # This SP needs to be created
                {"PolicyNumber": policy_number}
            )
            
            if not result:
                logger.warning(f"No invoice data returned for policy: {policy_number}")
                return None
            
            # Parse the dataset result
            invoice_data = self._parse_invoice_dataset(result)
            
            if not invoice_data:
                return None
            
            # Transform to Triton format
            transformed_data = self._transform_to_triton_format(
                invoice_data, 
                include_payment_info,
                format_currency
            )
            
            # Add retrieval timestamp
            transformed_data["retrieved_at"] = datetime.utcnow().isoformat() + "Z"
            
            return transformed_data
            
        except Exception as e:
            logger.error(f"Error retrieving invoice for policy {policy_number}: {str(e)}")
            raise
    
    async def get_invoice_by_quote_id(
        self,
        quote_id: str,
        include_payment_info: bool = True,
        format_currency: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve invoice data from IMS by quote ID (external reference)
        """
        self._ensure_initialized()
        
        try:
            # First, get policy number from quote ID
            result = self.soap_client.execute_data_set(
                "GetPolicyByExternalQuoteId",  # This SP needs to be created
                {"ExternalQuoteId": quote_id, "ExternalSystemId": "TRITON"}
            )
            
            if not result:
                logger.warning(f"No policy found for quote ID: {quote_id}")
                return None
            
            # Extract policy number from result
            policy_data = self._parse_dataset_single_row(result)
            policy_number = policy_data.get("PolicyNumber")
            
            if not policy_number:
                logger.warning(f"No policy number found for quote ID: {quote_id}")
                return None
            
            # Now get invoice by policy number
            return await self.get_invoice_by_policy_number(
                policy_number,
                include_payment_info,
                format_currency
            )
            
        except Exception as e:
            logger.error(f"Error retrieving invoice for quote {quote_id}: {str(e)}")
            raise
    
    def _parse_invoice_dataset(self, dataset_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse IMS dataset result into structured invoice data
        
        This is pseudo-code showing expected structure from IMS
        """
        try:
            # Extract tables from dataset
            tables = dataset_result.get('diffgr:diffgram', {}).get('NewDataSet', {})
            
            # Expected tables from stored procedure:
            # - InvoiceHeader: Main invoice information
            # - InvoiceLineItems: Individual line items
            # - PolicyInfo: Policy details
            # - InsuredInfo: Insured/customer information
            # - PaymentInfo: Payment methods and terms
            # - AgentInfo: Agent/agency details
            
            invoice_header = tables.get('InvoiceHeader', [])
            if not invoice_header:
                return None
            
            # Get first (latest) invoice
            if isinstance(invoice_header, list):
                invoice_header = invoice_header[0]
            
            # Build invoice data structure
            invoice_data = {
                "invoice_number": invoice_header.get("InvoiceNumber"),
                "invoice_date": invoice_header.get("InvoiceDate"),
                "due_date": invoice_header.get("DueDate"),
                "total_amount": float(invoice_header.get("TotalAmount", 0)),
                "subtotal": float(invoice_header.get("Subtotal", 0)),
                "tax_total": float(invoice_header.get("TaxTotal", 0)),
                "status": invoice_header.get("Status"),
                
                # Line items
                "line_items": self._parse_line_items(tables.get('InvoiceLineItems', [])),
                
                # Policy info
                "policy": self._parse_policy_info(tables.get('PolicyInfo', {})),
                
                # Insured info
                "insured": self._parse_insured_info(tables.get('InsuredInfo', {})),
                
                # Billing info (may be different from insured)
                "billing": self._parse_billing_info(tables.get('BillingInfo', {})),
                
                # Payment info
                "payment": self._parse_payment_info(tables.get('PaymentInfo', {})),
                
                # Agent info
                "agent": self._parse_agent_info(tables.get('AgentInfo', {}))
            }
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"Error parsing invoice dataset: {str(e)}")
            return None
    
    def _parse_line_items(self, line_items_data: Any) -> List[Dict[str, Any]]:
        """Parse invoice line items"""
        if not line_items_data:
            return []
        
        # Ensure it's a list
        if not isinstance(line_items_data, list):
            line_items_data = [line_items_data]
        
        items = []
        for item in line_items_data:
            items.append({
                "description": item.get("Description"),
                "amount": float(item.get("Amount", 0)),
                "quantity": int(item.get("Quantity", 1)),
                "unit_price": float(item.get("UnitPrice", 0)),
                "tax_rate": float(item.get("TaxRate", 0)),
                "tax_amount": float(item.get("TaxAmount", 0))
            })
        
        return items
    
    def _parse_policy_info(self, policy_data: Dict) -> Dict[str, Any]:
        """Parse policy information"""
        if not policy_data:
            return {}
        
        if isinstance(policy_data, list):
            policy_data = policy_data[0]
        
        return {
            "policy_number": policy_data.get("PolicyNumber"),
            "quote_number": policy_data.get("QuoteNumber"),
            "effective_date": policy_data.get("EffectiveDate"),
            "expiration_date": policy_data.get("ExpirationDate"),
            "coverage_type": policy_data.get("CoverageType"),
            "carrier": policy_data.get("CarrierName"),
            "limits": {
                "per_occurrence": policy_data.get("LimitPerOccurrence"),
                "aggregate": policy_data.get("LimitAggregate")
            },
            "deductible": float(policy_data.get("Deductible", 0))
        }
    
    def _parse_insured_info(self, insured_data: Dict) -> Dict[str, Any]:
        """Parse insured/customer information"""
        if not insured_data:
            return {}
        
        if isinstance(insured_data, list):
            insured_data = insured_data[0]
        
        return {
            "name": insured_data.get("InsuredName"),
            "dba": insured_data.get("DBAName"),
            "tax_id": insured_data.get("TaxID"),
            "address": {
                "street1": insured_data.get("Address1"),
                "street2": insured_data.get("Address2"),
                "city": insured_data.get("City"),
                "state": insured_data.get("State"),
                "zip": insured_data.get("ZipCode")
            },
            "contact": {
                "name": insured_data.get("ContactName"),
                "email": insured_data.get("Email"),
                "phone": insured_data.get("Phone")
            }
        }
    
    def _parse_billing_info(self, billing_data: Dict) -> Dict[str, Any]:
        """Parse billing information"""
        if not billing_data:
            return {}
        
        if isinstance(billing_data, list):
            billing_data = billing_data[0]
        
        return {
            "name": billing_data.get("BillingName"),
            "attention": billing_data.get("AttentionTo"),
            "address": {
                "street1": billing_data.get("Address1"),
                "street2": billing_data.get("Address2"),
                "city": billing_data.get("City"),
                "state": billing_data.get("State"),
                "zip": billing_data.get("ZipCode")
            },
            "contact": {
                "name": billing_data.get("ContactName"),
                "email": billing_data.get("Email"),
                "phone": billing_data.get("Phone")
            }
        }
    
    def _parse_payment_info(self, payment_data: Dict) -> Dict[str, Any]:
        """Parse payment information"""
        if not payment_data:
            return {}
        
        if isinstance(payment_data, list):
            payment_data = payment_data[0]
        
        return {
            "terms": payment_data.get("PaymentTerms", "Net 30"),
            "due_date": payment_data.get("DueDate"),
            "methods": {
                "ach": {
                    "enabled": payment_data.get("ACHEnabled", "true").lower() == "true",
                    "bank_name": payment_data.get("ACHBankName"),
                    "routing_number": payment_data.get("ACHRoutingNumber"),
                    "account_number": payment_data.get("ACHAccountNumber"),
                    "account_name": payment_data.get("ACHAccountName")
                },
                "wire": {
                    "enabled": payment_data.get("WireEnabled", "true").lower() == "true",
                    "bank_name": payment_data.get("WireBankName"),
                    "swift_code": payment_data.get("WireSwiftCode"),
                    "routing_number": payment_data.get("WireRoutingNumber"),
                    "account_number": payment_data.get("WireAccountNumber")
                },
                "check": {
                    "enabled": payment_data.get("CheckEnabled", "true").lower() == "true",
                    "payable_to": payment_data.get("CheckPayableTo"),
                    "mail_to": {
                        "name": payment_data.get("CheckMailToName"),
                        "street": payment_data.get("CheckMailToStreet"),
                        "city": payment_data.get("CheckMailToCity"),
                        "state": payment_data.get("CheckMailToState"),
                        "zip": payment_data.get("CheckMailToZip")
                    }
                }
            },
            "online_payment_url": payment_data.get("OnlinePaymentURL")
        }
    
    def _parse_agent_info(self, agent_data: Dict) -> Dict[str, Any]:
        """Parse agent/agency information"""
        if not agent_data:
            return {}
        
        if isinstance(agent_data, list):
            agent_data = agent_data[0]
        
        return {
            "agency_name": agent_data.get("AgencyName"),
            "agent_name": agent_data.get("AgentName"),
            "agent_email": agent_data.get("AgentEmail"),
            "agent_phone": agent_data.get("AgentPhone"),
            "commission_rate": float(agent_data.get("CommissionRate", 0)),
            "commission_amount": float(agent_data.get("CommissionAmount", 0))
        }
    
    def _transform_to_triton_format(
        self,
        invoice_data: Dict[str, Any],
        include_payment_info: bool,
        format_currency: bool
    ) -> Dict[str, Any]:
        """
        Transform IMS invoice data to Triton's expected format
        """
        # Format currency helper
        def format_money(amount: float) -> str:
            return f"${amount:,.2f}" if format_currency else str(amount)
        
        # Build Triton-formatted response
        triton_data = {
            "invoice_number": invoice_data["invoice_number"],
            "invoice_date": invoice_data["invoice_date"],
            "due_date": invoice_data["due_date"],
            "invoice_id": invoice_data.get("invoice_id", invoice_data["invoice_number"]),
            
            # Header information
            "header": {
                "title": "INVOICE",
                "company_name": invoice_data["policy"]["carrier"],
                "company_address": {
                    "street": "100 Insurance Plaza",  # TODO: Get from carrier config
                    "city": "Hartford",
                    "state": "CT",
                    "zip": "06103"
                },
                "logo_url": f"https://assets.triton.com/carriers/{invoice_data['policy']['carrier'].lower().replace(' ', '-')}-logo.png"
            },
            
            # Billing information
            "bill_to": {
                "name": invoice_data["billing"]["name"] or invoice_data["insured"]["name"],
                "attention": invoice_data["billing"]["attention"],
                "address": invoice_data["billing"]["address"] or invoice_data["insured"]["address"]
            },
            
            # Insured information
            "insured": {
                "name": invoice_data["insured"]["name"],
                "dba": invoice_data["insured"]["dba"],
                "address": invoice_data["insured"]["address"]
            },
            
            # Policy information
            "policy_info": {
                "policy_number": invoice_data["policy"]["policy_number"],
                "quote_number": invoice_data["policy"]["quote_number"],
                "effective_date": self._format_date(invoice_data["policy"]["effective_date"]),
                "expiration_date": self._format_date(invoice_data["policy"]["expiration_date"]),
                "coverage": invoice_data["policy"]["coverage_type"],
                "limits": self._format_limits(invoice_data["policy"]["limits"]),
                "deductible": format_money(invoice_data["policy"]["deductible"])
            },
            
            # Line items
            "line_items": [
                {
                    "description": item["description"],
                    "amount": item["amount"],
                    "formatted_amount": format_money(item["amount"])
                }
                for item in invoice_data["line_items"]
            ],
            
            # Totals
            "totals": {
                "subtotal": invoice_data["subtotal"],
                "tax": invoice_data["tax_total"],
                "total": invoice_data["total_amount"],
                "formatted_subtotal": format_money(invoice_data["subtotal"]),
                "formatted_tax": format_money(invoice_data["tax_total"]),
                "formatted_total": format_money(invoice_data["total_amount"])
            },
            
            # Agent information
            "agent_info": {
                "agency": invoice_data["agent"]["agency_name"],
                "agent": invoice_data["agent"]["agent_name"],
                "phone": invoice_data["agent"]["agent_phone"],
                "email": invoice_data["agent"]["agent_email"]
            },
            
            # Standard notes
            "notes": [
                "Coverage is subject to policy terms, conditions, and exclusions.",
                "Please remit payment by the due date to ensure continuous coverage.",
                "For questions about this invoice, contact your agent."
            ],
            
            # Footer
            "footer": {
                "text": "Thank you for your business!",
                "website": f"www.{invoice_data['policy']['carrier'].lower().replace(' ', '')}.com",
                "phone": "1-800-INSURANCE"
            }
        }
        
        # Add payment information if requested
        if include_payment_info and invoice_data.get("payment"):
            payment_info = invoice_data["payment"]
            triton_data["payment_info"] = {
                "due_date": self._format_date(payment_info["due_date"]),
                "terms": payment_info["terms"],
                "methods": {}
            }
            
            # Add enabled payment methods
            if payment_info["methods"]["ach"]["enabled"]:
                triton_data["payment_info"]["methods"]["ach"] = {
                    "bank_name": payment_info["methods"]["ach"]["bank_name"],
                    "routing_number": payment_info["methods"]["ach"]["routing_number"],
                    "account_number": self._mask_account_number(payment_info["methods"]["ach"]["account_number"]),
                    "account_name": payment_info["methods"]["ach"]["account_name"]
                }
            
            if payment_info["methods"]["wire"]["enabled"]:
                triton_data["payment_info"]["methods"]["wire"] = {
                    "bank_name": payment_info["methods"]["wire"]["bank_name"],
                    "swift_code": payment_info["methods"]["wire"]["swift_code"],
                    "routing_number": payment_info["methods"]["wire"]["routing_number"],
                    "account_number": self._mask_account_number(payment_info["methods"]["wire"]["account_number"]),
                    "reference": invoice_data["invoice_number"]
                }
            
            if payment_info["methods"]["check"]["enabled"]:
                triton_data["payment_info"]["methods"]["check"] = {
                    "payable_to": payment_info["methods"]["check"]["payable_to"],
                    "mail_to": payment_info["methods"]["check"]["mail_to"],
                    "memo": f"Policy #{invoice_data['policy']['policy_number']}"
                }
            
            if payment_info.get("online_payment_url"):
                triton_data["payment_info"]["online_payment_url"] = payment_info["online_payment_url"]
        
        return triton_data
    
    def _format_date(self, date_str: str) -> str:
        """Format date from YYYY-MM-DD to MM/DD/YYYY"""
        if not date_str:
            return ""
        
        try:
            # Parse ISO date
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%m/%d/%Y")
        except:
            # Return as-is if parsing fails
            return date_str
    
    def _format_limits(self, limits: Dict[str, Any]) -> str:
        """Format coverage limits for display"""
        per_occ = limits.get("per_occurrence", 0)
        aggregate = limits.get("aggregate", 0)
        
        if per_occ and aggregate:
            return f"${per_occ:,} per occurrence / ${aggregate:,} aggregate"
        elif per_occ:
            return f"${per_occ:,} per occurrence"
        elif aggregate:
            return f"${aggregate:,} aggregate"
        else:
            return "See policy for details"
    
    def _mask_account_number(self, account_number: str) -> str:
        """Mask account number for security"""
        if not account_number:
            return ""
        
        # Show only last 4 digits
        if len(account_number) > 4:
            return f"****{account_number[-4:]}"
        else:
            return "****"
    
    def _parse_dataset_single_row(self, dataset_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single row from dataset result"""
        try:
            tables = dataset_result.get('diffgr:diffgram', {}).get('NewDataSet', {}).get('Table', [])
            if not isinstance(tables, list):
                tables = [tables]
            
            if tables and len(tables) > 0:
                return tables[0]
            
            return {}
        except Exception as e:
            logger.error(f"Error parsing single row dataset: {str(e)}")
            return {}