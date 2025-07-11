"""
Invoice Microservice Implementation
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.microservices.core import (
    BaseMicroservice, 
    ServiceConfig, 
    ServiceResponse,
    ServiceError,
    get_service
)
from app.microservices.core.exceptions import ValidationError
from .models import (
    Invoice,
    InvoiceLineItem,
    InvoiceSearch,
    PaymentInfo,
    BillingInfo,
    GenerateInvoiceRequest,
    GenerateInvoiceResponse,
    AddPaymentRequest,
    AddPaymentResponse,
    InvoiceStatus
)


class InvoiceService(BaseMicroservice):
    """
    Microservice for managing invoices in IMS
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        if not config:
            config = ServiceConfig(
                name="invoice",
                version="1.0.0"
            )
        super().__init__(config)
        
        # Get data access service for queries
        self._data_service = None
    
    @property
    def data_service(self):
        """Lazy load data service"""
        if not self._data_service:
            self._data_service = get_service('data_access')
        return self._data_service
    
    def _on_initialize(self):
        """Service-specific initialization"""
        self.logger.info("Invoice service specific initialization")
    
    def _on_shutdown(self):
        """Service-specific shutdown"""
        self.logger.info("Invoice service specific shutdown")
    
    async def get_latest_by_policy(self, policy_number: str, max_attempts: int = 3) -> ServiceResponse:
        """
        Get latest invoice for a policy with retry logic
        
        Args:
            policy_number: Policy number
            max_attempts: Maximum retry attempts
            
        Returns:
            ServiceResponse with Invoice
        """
        self._log_operation("get_latest_by_policy", {"policy_number": policy_number})
        
        for attempt in range(max_attempts):
            try:
                # Call stored procedure to get latest invoice
                from app.microservices.data_access import CommandRequest
                command = CommandRequest(
                    command="GetLatestInvoiceByPolicy_WS",
                    parameters={"PolicyNumber": policy_number}
                )
                
                result = await self.data_service.execute_command(command)
                
                if result.success and result.data.result:
                    invoice = await self._parse_invoice_result(result.data.result)
                    if invoice:
                        return ServiceResponse(
                            success=True,
                            data=invoice
                        )
                
                # No invoice found yet
                if attempt < max_attempts - 1:
                    self.logger.info(
                        f"No invoice found for {policy_number}, "
                        f"attempt {attempt + 1}/{max_attempts}. Waiting 2s..."
                    )
                    await asyncio.sleep(2)
                
            except Exception as e:
                if attempt < max_attempts - 1:
                    self.logger.warning(f"Error getting invoice: {str(e)}. Retrying...")
                    await asyncio.sleep(2)
                else:
                    return self._handle_error(e, "get_latest_by_policy")
        
        # No invoice found after all attempts
        return ServiceResponse(
            success=True,
            data=None,
            warnings=[f"No invoice found for policy {policy_number} after {max_attempts} attempts"]
        )
    
    async def get_latest_by_quote(self, quote_id: str) -> ServiceResponse:
        """
        Get latest invoice for a quote
        
        Args:
            quote_id: Quote ID or GUID
            
        Returns:
            ServiceResponse with Invoice
        """
        self._log_operation("get_latest_by_quote", {"quote_id": quote_id})
        
        try:
            # Query for policy number by quote
            from app.microservices.data_access import QueryRequest
            query = QueryRequest(
                query="""
                SELECT TOP 1 p.PolicyNumber 
                FROM Policies p
                INNER JOIN Quotes q ON p.QuoteID = q.QuoteID
                WHERE q.QuoteGUID = @QuoteID OR q.QuoteNumber = @QuoteID
                """,
                parameters={"QuoteID": quote_id}
            )
            
            result = await self.data_service.execute_query(query)
            
            if result.success and result.data.row_count > 0:
                policy_number = result.data.tables[0]["rows"][0]["PolicyNumber"]
                return await self.get_latest_by_policy(policy_number)
            else:
                return ServiceResponse(
                    success=False,
                    error=f"No policy found for quote: {quote_id}"
                )
                
        except Exception as e:
            return self._handle_error(e, "get_latest_by_quote")
    
    async def generate_invoice(self, request: GenerateInvoiceRequest) -> ServiceResponse:
        """
        Generate a new invoice
        
        Args:
            request: Invoice generation request
            
        Returns:
            ServiceResponse with GenerateInvoiceResponse
        """
        self._log_operation("generate_invoice", {
            "policy_number": request.policy_number,
            "invoice_type": request.invoice_type
        })
        
        try:
            # Call IMS to generate invoice
            result = self.soap_client.service.GenerateInvoice(
                PolicyNumber=request.policy_number,
                InvoiceDate=(request.invoice_date or date.today()).isoformat()
            )
            
            if not result:
                raise ServiceError("Failed to generate invoice - no response from IMS")
            
            invoice_number = str(result)
            
            response = GenerateInvoiceResponse(
                success=True,
                invoice_number=invoice_number
            )
            
            # Generate PDF if requested
            if request.generate_pdf:
                pdf_result = await self.generate_invoice_pdf(invoice_number)
                if pdf_result.success:
                    response.pdf_path = pdf_result.data.get("pdf_path")
                else:
                    response.warnings.append("PDF generation failed")
            
            # Send emails if requested
            if request.send_to_insured or request.send_to_agent:
                # This would integrate with email service
                response.warnings.append("Email sending not yet implemented")
            
            return ServiceResponse(
                success=True,
                data=response,
                metadata={"action": "generated"}
            )
            
        except Exception as e:
            return self._handle_error(e, "generate_invoice")
    
    async def generate_invoice_pdf(self, invoice_number: str) -> ServiceResponse:
        """
        Generate PDF for an invoice
        
        Args:
            invoice_number: Invoice number
            
        Returns:
            ServiceResponse with PDF path
        """
        self._log_operation("generate_invoice_pdf", {"invoice_number": invoice_number})
        
        try:
            # Call IMS to generate PDF
            result = self.soap_client.service.GenerateInvoiceAsPDF(
                InvoiceNumber=invoice_number
            )
            
            if result:
                # Result should contain PDF path or bytes
                return ServiceResponse(
                    success=True,
                    data={
                        "pdf_path": str(result),
                        "invoice_number": invoice_number
                    }
                )
            else:
                return ServiceResponse(
                    success=False,
                    error="Failed to generate PDF"
                )
                
        except Exception as e:
            return self._handle_error(e, "generate_invoice_pdf")
    
    async def add_payment(self, request: AddPaymentRequest) -> ServiceResponse:
        """
        Add payment to an invoice
        
        Args:
            request: Payment request
            
        Returns:
            ServiceResponse with AddPaymentResponse
        """
        self._log_operation("add_payment", {
            "invoice_number": request.invoice_number,
            "amount": str(request.payment_amount)
        })
        
        try:
            # Get policy number for invoice
            policy_number = await self._get_policy_for_invoice(request.invoice_number)
            if not policy_number:
                return ServiceResponse(
                    success=False,
                    error=f"Invoice not found: {request.invoice_number}"
                )
            
            # Build payment data
            payment_data = {
                "PaymentAmount": str(request.payment_amount),
                "PaymentDate": request.payment_date.isoformat(),
                "PaymentMethod": request.payment_method,
                "CheckNumber": request.check_number or "",
                "TransactionID": request.transaction_id or "",
                "Notes": request.notes or ""
            }
            
            # Call IMS to add payment
            result = self.soap_client.service.AddPolicyPayment(
                PolicyNumber=policy_number,
                **payment_data
            )
            
            if result:
                # Get updated invoice to check status
                invoice_result = await self.get_latest_by_policy(policy_number)
                
                response = AddPaymentResponse(
                    success=True,
                    payment_id=str(result),
                    remaining_balance=Decimal("0"),  # Would need to calculate
                    invoice_status=InvoiceStatus.PAID if invoice_result.success else None
                )
                
                return ServiceResponse(
                    success=True,
                    data=response,
                    metadata={"action": "payment_added"}
                )
            else:
                return ServiceResponse(
                    success=False,
                    error="Failed to add payment"
                )
                
        except Exception as e:
            return self._handle_error(e, "add_payment")
    
    async def search_invoices(self, criteria: InvoiceSearch) -> ServiceResponse:
        """
        Search for invoices
        
        Args:
            criteria: Search criteria
            
        Returns:
            ServiceResponse with list of invoices
        """
        self._log_operation("search_invoices", criteria.dict(exclude_none=True))
        
        try:
            # Build query
            query = """
            SELECT 
                i.InvoiceID,
                i.InvoiceNumber,
                i.InvoiceDate,
                i.DueDate,
                i.TotalAmount,
                i.Status,
                p.PolicyNumber,
                q.QuoteNumber,
                ins.CorporationName as InsuredName
            FROM Invoices i
            INNER JOIN Policies p ON i.PolicyID = p.PolicyID
            INNER JOIN Quotes q ON p.QuoteID = q.QuoteID
            INNER JOIN Insureds ins ON q.InsuredGUID = ins.InsuredGUID
            WHERE 1=1
            """
            
            parameters = {}
            
            # Add search conditions
            if criteria.invoice_number:
                query += " AND i.InvoiceNumber = @InvoiceNumber"
                parameters["InvoiceNumber"] = criteria.invoice_number
            
            if criteria.policy_number:
                query += " AND p.PolicyNumber = @PolicyNumber"
                parameters["PolicyNumber"] = criteria.policy_number
            
            if criteria.insured_name:
                query += " AND ins.CorporationName LIKE @InsuredName"
                parameters["InsuredName"] = f"%{criteria.insured_name}%"
            
            if criteria.status:
                query += " AND i.Status = @Status"
                parameters["Status"] = criteria.status.value
            
            if criteria.date_from:
                query += " AND i.InvoiceDate >= @DateFrom"
                parameters["DateFrom"] = criteria.date_from.isoformat()
            
            if criteria.date_to:
                query += " AND i.InvoiceDate <= @DateTo"
                parameters["DateTo"] = criteria.date_to.isoformat()
            
            # Add ordering and pagination
            query += " ORDER BY i.InvoiceDate DESC"
            query += f" OFFSET {criteria.offset} ROWS FETCH NEXT {criteria.limit} ROWS ONLY"
            
            # Execute query
            from app.microservices.data_access import QueryRequest
            query_request = QueryRequest(
                query=query,
                parameters=parameters
            )
            
            result = await self.data_service.execute_query(query_request)
            
            if result.success and result.data.tables:
                invoices = []
                for row in result.data.tables[0]["rows"]:
                    # Create simplified invoice objects
                    invoice = Invoice(
                        invoice_number=row["InvoiceNumber"],
                        invoice_date=row["InvoiceDate"],
                        due_date=row["DueDate"],
                        total_amount=Decimal(str(row["TotalAmount"])),
                        status=InvoiceStatus(row["Status"]),
                        policy_number=row["PolicyNumber"],
                        quote_number=row["QuoteNumber"],
                        insured_name=row["InsuredName"],
                        # Default required fields
                        subtotal=Decimal(str(row["TotalAmount"])),
                        balance_due=Decimal("0"),
                        effective_date=date.today(),
                        expiration_date=date.today(),
                        created_date=datetime.now()
                    )
                    invoices.append(invoice)
                
                return ServiceResponse(
                    success=True,
                    data=invoices,
                    metadata={
                        "count": len(invoices),
                        "offset": criteria.offset,
                        "limit": criteria.limit
                    }
                )
            else:
                return ServiceResponse(
                    success=True,
                    data=[],
                    metadata={"count": 0}
                )
                
        except Exception as e:
            return self._handle_error(e, "search_invoices")
    
    async def _parse_invoice_result(self, ims_result: Any) -> Optional[Invoice]:
        """Parse IMS invoice result into Invoice model"""
        try:
            # Extract invoice header
            if not hasattr(ims_result, 'InvoiceHeader'):
                return None
            
            header = ims_result.InvoiceHeader
            
            # Create invoice
            invoice = Invoice(
                invoice_number=header.InvoiceNumber,
                invoice_date=header.InvoiceDate,
                due_date=header.DueDate,
                subtotal=Decimal(str(header.Subtotal)),
                tax_total=Decimal(str(header.TaxTotal)),
                total_amount=Decimal(str(header.TotalAmount)),
                balance_due=Decimal(str(header.TotalAmount)),  # Assuming unpaid
                status=InvoiceStatus(header.Status) if hasattr(header, 'Status') else InvoiceStatus.PENDING,
                created_date=datetime.now()
            )
            
            # Extract line items
            if hasattr(ims_result, 'InvoiceLineItems'):
                for item in ims_result.InvoiceLineItems:
                    line_item = InvoiceLineItem(
                        description=item.Description,
                        amount=Decimal(str(item.Amount)),
                        quantity=getattr(item, 'Quantity', 1),
                        tax_rate=Decimal(str(getattr(item, 'TaxRate', 0))),
                        tax_amount=Decimal(str(getattr(item, 'TaxAmount', 0)))
                    )
                    invoice.line_items.append(line_item)
            
            # Extract policy info
            if hasattr(ims_result, 'PolicyInfo'):
                policy = ims_result.PolicyInfo
                invoice.policy_number = policy.PolicyNumber
                invoice.quote_number = getattr(policy, 'QuoteNumber', None)
                invoice.effective_date = policy.EffectiveDate
                invoice.expiration_date = policy.ExpirationDate
                invoice.coverage_type = getattr(policy, 'CoverageType', None)
                invoice.carrier_name = getattr(policy, 'CarrierName', None)
            
            # Extract insured info
            if hasattr(ims_result, 'InsuredInfo'):
                insured = ims_result.InsuredInfo
                invoice.insured_name = insured.InsuredName
                invoice.insured_tax_id = getattr(insured, 'TaxID', None)
            
            # Extract billing info
            if hasattr(ims_result, 'BillingInfo'):
                billing = ims_result.BillingInfo
                invoice.billing_info = BillingInfo(
                    billing_name=billing.BillingName,
                    address1=billing.Address1,
                    city=billing.City,
                    state=billing.State,
                    zip_code=billing.ZipCode
                )
            
            # Extract payment info
            if hasattr(ims_result, 'PaymentInfo'):
                payment = ims_result.PaymentInfo
                invoice.payment_info = PaymentInfo(
                    payment_terms=payment.PaymentTerms,
                    due_date=invoice.due_date,
                    check_enabled=True,
                    check_payable_to=getattr(payment, 'CheckPayableTo', None)
                )
            
            return invoice
            
        except Exception as e:
            self.logger.error(f"Error parsing invoice result: {str(e)}")
            return None
    
    async def _get_policy_for_invoice(self, invoice_number: str) -> Optional[str]:
        """Get policy number for an invoice"""
        try:
            from app.microservices.data_access import QueryRequest
            query = QueryRequest(
                query="""
                SELECT TOP 1 p.PolicyNumber
                FROM Invoices i
                INNER JOIN Policies p ON i.PolicyID = p.PolicyID
                WHERE i.InvoiceNumber = @InvoiceNumber
                """,
                parameters={"InvoiceNumber": invoice_number}
            )
            
            result = await self.data_service.execute_query(query)
            
            if result.success and result.data.row_count > 0:
                return result.data.tables[0]["rows"][0]["PolicyNumber"]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting policy for invoice: {str(e)}")
            return None