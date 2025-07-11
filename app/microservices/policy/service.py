"""
Policy Microservice Implementation
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date
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
    Policy,
    PolicySearch,
    CancellationRequest,
    CancellationResponse,
    EndorsementRequest,
    EndorsementResponse,
    ReinstatementRequest,
    ReinstatementResponse,
    PolicyStatus
)


class PolicyService(BaseMicroservice):
    """
    Microservice for managing policies and lifecycle operations in IMS
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        if not config:
            config = ServiceConfig(
                name="policy",
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
        self.logger.info("Policy service specific initialization")
    
    def _on_shutdown(self):
        """Service-specific shutdown"""
        self.logger.info("Policy service specific shutdown")
    
    async def get_by_policy_number(self, policy_number: str) -> ServiceResponse:
        """
        Get policy by policy number
        
        Args:
            policy_number: Policy number
            
        Returns:
            ServiceResponse with Policy
        """
        self._log_operation("get_by_policy_number", {"policy_number": policy_number})
        
        try:
            # Get policy information
            result = self.soap_client.service.GetPolicyInformation(
                PolicyNumber=policy_number
            )
            
            if not result:
                return ServiceResponse(
                    success=False,
                    error=f"Policy not found: {policy_number}"
                )
            
            policy = self._map_ims_to_policy(result)
            
            return ServiceResponse(
                success=True,
                data=policy
            )
            
        except Exception as e:
            return self._handle_error(e, "get_by_policy_number")
    
    async def get_control_number(self, policy_number: str) -> ServiceResponse:
        """
        Get control number for a policy
        
        Args:
            policy_number: Policy number
            
        Returns:
            ServiceResponse with control number
        """
        self._log_operation("get_control_number", {"policy_number": policy_number})
        
        try:
            # Get control number
            result = self.soap_client.service.GetControlNumber(
                PolicyNumber=policy_number
            )
            
            if not result:
                return ServiceResponse(
                    success=False,
                    error=f"Control number not found for policy: {policy_number}"
                )
            
            return ServiceResponse(
                success=True,
                data={"control_number": str(result)},
                metadata={"policy_number": policy_number}
            )
            
        except Exception as e:
            return self._handle_error(e, "get_control_number")
    
    async def cancel_policy(self, request: CancellationRequest) -> ServiceResponse:
        """
        Cancel a policy
        
        Args:
            request: Cancellation request
            
        Returns:
            ServiceResponse with CancellationResponse
        """
        self._log_operation("cancel_policy", {
            "control_number": request.control_number,
            "cancellation_date": request.cancellation_date.isoformat()
        })
        
        try:
            # Build SOAP parameters
            params = {
                'ControlNumber': request.control_number,
                'CancellationDate': request.cancellation_date.isoformat(),
                'CancellationReasonID': request.cancellation_reason_id,
                'Comments': request.comments,
                'FlatCancel': 'true' if request.flat_cancel else 'false'
            }
            
            if request.user_guid:
                params['UserGuid'] = request.user_guid
            
            # Call custom stored procedure
            from app.microservices.data_access import CommandRequest
            command = CommandRequest(
                command="CancelPolicy_WS",
                parameters=params
            )
            
            result = await self.data_service.execute_command(command)
            
            if result.success and result.data.result:
                # Parse result
                ims_result = result.data.result
                
                response = CancellationResponse(
                    success=True,
                    policy_number=request.control_number,
                    cancellation_date=request.cancellation_date,
                    return_premium_amount=self._extract_decimal(ims_result, 'ReturnPremium'),
                    cancellation_id=self._extract_string(ims_result, 'CancellationID'),
                    ims_reference=self._extract_string(ims_result, 'Reference')
                )
                
                return ServiceResponse(
                    success=True,
                    data=response,
                    metadata={"action": "cancelled"}
                )
            else:
                return ServiceResponse(
                    success=False,
                    error="Cancellation failed",
                    data=CancellationResponse(
                        success=False,
                        policy_number=request.control_number,
                        cancellation_date=request.cancellation_date,
                        errors=["IMS cancellation failed"]
                    )
                )
                
        except Exception as e:
            return self._handle_error(e, "cancel_policy")
    
    async def create_endorsement(self, request: EndorsementRequest) -> ServiceResponse:
        """
        Create a policy endorsement
        
        Args:
            request: Endorsement request
            
        Returns:
            ServiceResponse with EndorsementResponse
        """
        self._log_operation("create_endorsement", {
            "control_number": request.control_number,
            "effective_date": request.endorsement_effective_date.isoformat()
        })
        
        try:
            # Build SOAP parameters
            params = {
                'ControlNumber': request.control_number,
                'EndorsementEffectiveDate': request.endorsement_effective_date.isoformat(),
                'EndorsementComment': request.endorsement_comment,
                'EndorsementReasonID': request.endorsement_reason_id,
                'CalculationType': request.calculation_type,
                'CopyExposures': 'true' if request.copy_exposures else 'false',
                'CopyPremiums': 'true' if request.copy_premiums else 'false'
            }
            
            if request.user_guid:
                params['UserGuid'] = request.user_guid
            
            # Call custom stored procedure
            from app.microservices.data_access import CommandRequest
            command = CommandRequest(
                command="CreateEndorsement_WS",
                parameters=params
            )
            
            result = await self.data_service.execute_command(command)
            
            if result.success and result.data.result:
                # Parse result
                ims_result = result.data.result
                
                response = EndorsementResponse(
                    success=True,
                    policy_number=request.control_number,
                    endorsement_number=self._extract_string(ims_result, 'EndorsementNumber'),
                    endorsement_quote_guid=self._extract_string(ims_result, 'EndorsementQuoteGuid'),
                    endorsement_effective_date=request.endorsement_effective_date,
                    premium_change=self._extract_decimal(ims_result, 'PremiumChange'),
                    new_total_premium=self._extract_decimal(ims_result, 'NewTotalPremium'),
                    ims_reference=self._extract_string(ims_result, 'Reference')
                )
                
                # Apply premium change if specified
                if request.premium_change and response.endorsement_quote_guid:
                    await self._apply_endorsement_premium(
                        response.endorsement_quote_guid,
                        request.premium_change
                    )
                
                return ServiceResponse(
                    success=True,
                    data=response,
                    metadata={"action": "endorsement_created"}
                )
            else:
                return ServiceResponse(
                    success=False,
                    error="Endorsement creation failed",
                    data=EndorsementResponse(
                        success=False,
                        policy_number=request.control_number,
                        endorsement_effective_date=request.endorsement_effective_date,
                        errors=["IMS endorsement creation failed"]
                    )
                )
                
        except Exception as e:
            return self._handle_error(e, "create_endorsement")
    
    async def reinstate_policy(self, request: ReinstatementRequest) -> ServiceResponse:
        """
        Reinstate a cancelled policy
        
        Args:
            request: Reinstatement request
            
        Returns:
            ServiceResponse with ReinstatementResponse
        """
        self._log_operation("reinstate_policy", {
            "control_number": request.control_number,
            "reinstatement_date": request.reinstatement_date.isoformat()
        })
        
        try:
            # Build SOAP parameters
            params = {
                'ControlNumber': request.control_number,
                'ReinstatementDate': request.reinstatement_date.isoformat(),
                'ReinstatementReasonID': request.reinstatement_reason_id,
                'Comments': request.comments,
                'GenerateInvoice': 'true' if request.generate_invoice else 'false'
            }
            
            if request.user_guid:
                params['UserGuid'] = request.user_guid
            
            if request.payment_received:
                params['PaymentReceived'] = str(request.payment_received)
            
            if request.check_number:
                params['CheckNumber'] = request.check_number
            
            # Call custom stored procedure
            from app.microservices.data_access import CommandRequest
            command = CommandRequest(
                command="ReinstatePolicy_WS",
                parameters=params
            )
            
            result = await self.data_service.execute_command(command)
            
            if result.success and result.data.result:
                # Parse result
                ims_result = result.data.result
                
                response = ReinstatementResponse(
                    success=True,
                    policy_number=request.control_number,
                    reinstatement_date=request.reinstatement_date,
                    reinstatement_amount=self._extract_decimal(ims_result, 'ReinstatementAmount'),
                    invoice_number=self._extract_string(ims_result, 'InvoiceNumber'),
                    invoice_amount=self._extract_decimal(ims_result, 'InvoiceAmount'),
                    ims_reference=self._extract_string(ims_result, 'Reference')
                )
                
                return ServiceResponse(
                    success=True,
                    data=response,
                    metadata={"action": "reinstated"}
                )
            else:
                return ServiceResponse(
                    success=False,
                    error="Reinstatement failed",
                    data=ReinstatementResponse(
                        success=False,
                        policy_number=request.control_number,
                        reinstatement_date=request.reinstatement_date,
                        errors=["IMS reinstatement failed"]
                    )
                )
                
        except Exception as e:
            return self._handle_error(e, "reinstate_policy")
    
    async def search_policies(self, criteria: PolicySearch) -> ServiceResponse:
        """
        Search for policies
        
        Args:
            criteria: Search criteria
            
        Returns:
            ServiceResponse with list of policies
        """
        self._log_operation("search_policies", criteria.dict(exclude_none=True))
        
        try:
            # Build query
            query = """
            SELECT 
                p.PolicyID,
                p.PolicyNumber,
                p.ControlNumber,
                q.QuoteGUID,
                q.QuoteNumber,
                i.InsuredGUID,
                i.CorporationName as InsuredName,
                p.EffectiveDate,
                p.ExpirationDate,
                p.Status,
                l.LineName as LineOfBusiness,
                p.State,
                p.TotalPremium,
                p.WrittenPremium,
                p.BoundDate,
                p.IssuedDate,
                p.CancelledDate,
                p.CreatedDate,
                p.ModifiedDate
            FROM Policies p
            INNER JOIN Quotes q ON p.QuoteID = q.QuoteID
            INNER JOIN Insureds i ON q.InsuredGUID = i.InsuredGUID
            INNER JOIN Lines l ON q.LineGUID = l.LineGUID
            WHERE 1=1
            """
            
            parameters = {}
            
            # Add search conditions
            if criteria.policy_number:
                query += " AND p.PolicyNumber = @PolicyNumber"
                parameters["PolicyNumber"] = criteria.policy_number
            
            if criteria.control_number:
                query += " AND p.ControlNumber = @ControlNumber"
                parameters["ControlNumber"] = criteria.control_number
            
            if criteria.insured_name:
                query += " AND i.CorporationName LIKE @InsuredName"
                parameters["InsuredName"] = f"%{criteria.insured_name}%"
            
            if criteria.insured_guid:
                query += " AND i.InsuredGUID = @InsuredGUID"
                parameters["InsuredGUID"] = criteria.insured_guid
            
            if criteria.status:
                query += " AND p.Status = @Status"
                parameters["Status"] = criteria.status.value
            
            if criteria.state:
                query += " AND p.State = @State"
                parameters["State"] = criteria.state
            
            if criteria.effective_date_from:
                query += " AND p.EffectiveDate >= @EffectiveDateFrom"
                parameters["EffectiveDateFrom"] = criteria.effective_date_from.isoformat()
            
            if criteria.effective_date_to:
                query += " AND p.EffectiveDate <= @EffectiveDateTo"
                parameters["EffectiveDateTo"] = criteria.effective_date_to.isoformat()
            
            # Add ordering and pagination
            query += " ORDER BY p.PolicyNumber DESC"
            query += f" OFFSET {criteria.offset} ROWS FETCH NEXT {criteria.limit} ROWS ONLY"
            
            # Execute query
            from app.microservices.data_access import QueryRequest
            query_request = QueryRequest(
                query=query,
                parameters=parameters
            )
            
            result = await self.data_service.execute_query(query_request)
            
            if result.success and result.data.tables:
                policies = []
                for row in result.data.tables[0]["rows"]:
                    policies.append(self._map_row_to_policy(row))
                
                return ServiceResponse(
                    success=True,
                    data=policies,
                    metadata={
                        "count": len(policies),
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
            return self._handle_error(e, "search_policies")
    
    async def _apply_endorsement_premium(self, quote_guid: str, premium_change: Decimal):
        """Apply premium change to endorsement"""
        try:
            quote_service = get_service('quote')
            
            # Add quote option
            option_response = await quote_service.add_quote_option(quote_guid)
            if option_response.success:
                option_id = option_response.data["quote_option_id"]
                
                # Add premium change
                from app.microservices.quote import PremiumCreate
                premium_data = PremiumCreate(
                    quote_guid=quote_guid,
                    quote_option_id=option_id,
                    amount=abs(premium_change),
                    description="Endorsement Premium Adjustment" if premium_change > 0 else "Endorsement Premium Credit"
                )
                
                await quote_service.add_premium(premium_data)
                
        except Exception as e:
            self.logger.warning(f"Failed to apply endorsement premium: {str(e)}")
    
    def _map_ims_to_policy(self, ims_policy: Any) -> Policy:
        """Map IMS policy object to our model"""
        return Policy(
            policy_id=getattr(ims_policy, 'PolicyID', None),
            policy_number=ims_policy.PolicyNumber,
            quote_guid=str(ims_policy.QuoteGUID),
            quote_number=getattr(ims_policy, 'QuoteNumber', None),
            insured_guid=str(ims_policy.InsuredGUID),
            insured_name=ims_policy.InsuredName,
            effective_date=ims_policy.EffectiveDate,
            expiration_date=ims_policy.ExpirationDate,
            status=PolicyStatus(ims_policy.Status),
            line_of_business=ims_policy.LineOfBusiness,
            state=ims_policy.State,
            total_premium=Decimal(str(ims_policy.TotalPremium)),
            written_premium=Decimal(str(getattr(ims_policy, 'WrittenPremium', 0))),
            bound_date=ims_policy.BoundDate,
            issued_date=getattr(ims_policy, 'IssuedDate', None),
            cancelled_date=getattr(ims_policy, 'CancelledDate', None),
            control_number=getattr(ims_policy, 'ControlNumber', None),
            created_date=getattr(ims_policy, 'CreatedDate', datetime.now())
        )
    
    def _map_row_to_policy(self, row: Dict[str, Any]) -> Policy:
        """Map database row to policy model"""
        return Policy(
            policy_id=row.get('PolicyID'),
            policy_number=row['PolicyNumber'],
            quote_guid=row['QuoteGUID'],
            quote_number=row.get('QuoteNumber'),
            insured_guid=row['InsuredGUID'],
            insured_name=row['InsuredName'],
            effective_date=row['EffectiveDate'],
            expiration_date=row['ExpirationDate'],
            status=PolicyStatus(row['Status']),
            line_of_business=row['LineOfBusiness'],
            state=row['State'],
            total_premium=Decimal(str(row['TotalPremium'])),
            written_premium=Decimal(str(row.get('WrittenPremium', 0))),
            bound_date=row['BoundDate'],
            issued_date=row.get('IssuedDate'),
            cancelled_date=row.get('CancelledDate'),
            control_number=row.get('ControlNumber'),
            created_date=row.get('CreatedDate', datetime.now())
        )
    
    def _extract_string(self, result: Any, field: str) -> Optional[str]:
        """Safely extract string from result"""
        if hasattr(result, field):
            value = getattr(result, field)
            return str(value) if value else None
        return None
    
    def _extract_decimal(self, result: Any, field: str) -> Optional[Decimal]:
        """Safely extract decimal from result"""
        if hasattr(result, field):
            value = getattr(result, field)
            if value:
                try:
                    return Decimal(str(value))
                except:
                    pass
        return None