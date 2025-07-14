"""
IMS Policy Lifecycle Service

This service handles policy lifecycle operations including:
- Policy cancellation
- Policy endorsement
- Policy reinstatement
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, date
import json

from app.services.ims.base_service import BaseIMSService
from app.services.ims.data_access_service import IMSDataAccessService
from app.services.ims.quote_service import IMSQuoteService

logger = logging.getLogger(__name__)


class IMSPolicyLifecycleService(BaseIMSService):
    """Service for policy lifecycle operations in IMS"""
    
    def __init__(self, environment: Optional[str] = None):
        """Initialize the service"""
        super().__init__(environment)
        self.data_access_service = IMSDataAccessService(environment)
        self.quote_service = IMSQuoteService(environment)
        
    def cancel_policy(
        self, 
        control_number: int,
        cancellation_date: datetime,
        cancellation_reason_id: int,
        comments: Optional[str] = None,
        user_guid: Optional[str] = None,
        return_premium: bool = True,
        flat_cancel: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel a policy in IMS
        
        Args:
            control_number: The policy control number
            cancellation_date: Effective date of cancellation
            cancellation_reason_id: Reason code for cancellation
            comments: Optional comments
            user_guid: User performing the cancellation
            return_premium: Whether to calculate return premium
            flat_cancel: If True, no return premium calculated
            
        Returns:
            Dictionary with cancellation results
        """
        self._log_operation("cancel_policy", {
            "control_number": control_number,
            "cancellation_date": cancellation_date.isoformat() if isinstance(cancellation_date, (date, datetime)) else cancellation_date,
            "reason_id": cancellation_reason_id,
            "flat_cancel": flat_cancel
        })
        
        try:
            # Prepare parameters for stored procedure
            # Note: We pass "CancelPolicy" without "_WS" as IMS adds it
            parameters = {
                "ControlNumber": control_number,
                "CancellationDate": self._format_date(cancellation_date),
                "CancellationReasonID": cancellation_reason_id,
                "Comments": comments or "",
                "UserGuid": user_guid or "00000000-0000-0000-0000-000000000000",
                "ReturnPremium": 1 if return_premium else 0,
                "FlatCancel": 1 if flat_cancel else 0
            }
            
            # Execute the cancellation stored procedure
            result = self.data_access_service.execute_command("CancelPolicy", parameters)
            
            logger.info(f"Policy {control_number} cancelled successfully")
            
            # Parse the result
            if result and isinstance(result, dict):
                return {
                    "success": True,
                    "control_number": control_number,
                    "cancellation_date": cancellation_date,
                    "transaction_number": result.get("TransactionNumber"),
                    "status": "cancelled",
                    "message": result.get("Message", "Policy cancelled successfully")
                }
            else:
                return {
                    "success": True,
                    "control_number": control_number,
                    "cancellation_date": cancellation_date,
                    "status": "cancelled",
                    "message": "Policy cancelled successfully"
                }
                
        except Exception as e:
            logger.error(f"Error cancelling policy {control_number}: {str(e)}")
            return {
                "success": False,
                "control_number": control_number,
                "error": str(e),
                "message": f"Failed to cancel policy: {str(e)}"
            }
    
    def create_endorsement(
        self,
        control_number: int,
        endorsement_effective_date: datetime,
        endorsement_comment: str,
        endorsement_reason_id: int,
        user_guid: str,
        calculation_type: str = "P",  # P=Pro-rata, S=Short-rate, F=Flat
        copy_exposures: bool = True,
        copy_premiums: bool = False
    ) -> Dict[str, Any]:
        """
        Create a policy endorsement in IMS
        
        Args:
            control_number: The policy control number
            endorsement_effective_date: Effective date of endorsement
            endorsement_comment: Description of changes
            endorsement_reason_id: Reason code for endorsement
            user_guid: User creating the endorsement
            calculation_type: Premium calculation type
            copy_exposures: Copy exposure data to endorsement
            copy_premiums: Copy premium data to endorsement
            
        Returns:
            Dictionary with endorsement results
        """
        self._log_operation("create_endorsement", {
            "control_number": control_number,
            "effective_date": endorsement_effective_date.isoformat() if isinstance(endorsement_effective_date, (date, datetime)) else endorsement_effective_date,
            "reason_id": endorsement_reason_id,
            "calculation_type": calculation_type
        })
        
        try:
            # Prepare parameters for stored procedure
            parameters = {
                "ControlNumber": control_number,
                "EndorsementEffectiveDate": self._format_date(endorsement_effective_date),
                "EndorsementComment": endorsement_comment,
                "EndorsementReasonID": endorsement_reason_id,
                "UserGuid": user_guid,
                "CalculationType": calculation_type,
                "CopyExposures": 1 if copy_exposures else 0,
                "CopyPremiums": 1 if copy_premiums else 0
            }
            
            # Execute the endorsement stored procedure
            result = self.data_access_service.execute_command("CreateEndorsement", parameters)
            
            logger.info(f"Endorsement created for policy {control_number}")
            
            # Parse the result
            if result and isinstance(result, dict):
                return {
                    "success": True,
                    "control_number": control_number,
                    "endorsement_quote_id": result.get("EndorsementQuoteID"),
                    "endorsement_quote_guid": result.get("EndorsementQuoteGuid"),
                    "endorsement_number": result.get("EndorsementNumber"),
                    "pro_rata_factor": result.get("ProRataFactor"),
                    "status": "endorsed",
                    "message": result.get("Message", "Endorsement created successfully")
                }
            else:
                return {
                    "success": True,
                    "control_number": control_number,
                    "status": "endorsed",
                    "message": "Endorsement created successfully"
                }
                
        except Exception as e:
            logger.error(f"Error creating endorsement for policy {control_number}: {str(e)}")
            return {
                "success": False,
                "control_number": control_number,
                "error": str(e),
                "message": f"Failed to create endorsement: {str(e)}"
            }
    
    def reinstate_policy(
        self,
        control_number: int,
        reinstatement_date: datetime,
        reinstatement_reason_id: Optional[int] = None,
        comments: Optional[str] = None,
        user_guid: Optional[str] = None,
        generate_invoice: bool = True,
        payment_received: Optional[float] = None,
        check_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reinstate a cancelled policy in IMS
        
        Args:
            control_number: The policy control number
            reinstatement_date: Effective date of reinstatement
            reinstatement_reason_id: Reason code (optional)
            comments: Optional comments
            user_guid: User performing the reinstatement
            generate_invoice: Whether to generate reinstatement invoice
            payment_received: Payment amount if received
            check_number: Check number if payment received
            
        Returns:
            Dictionary with reinstatement results
        """
        self._log_operation("reinstate_policy", {
            "control_number": control_number,
            "reinstatement_date": reinstatement_date.isoformat() if isinstance(reinstatement_date, (date, datetime)) else reinstatement_date,
            "generate_invoice": generate_invoice,
            "payment_received": payment_received
        })
        
        try:
            # Prepare parameters for stored procedure
            parameters = {
                "ControlNumber": control_number,
                "ReinstatementDate": self._format_date(reinstatement_date),
                "ReinstatementReasonID": reinstatement_reason_id or 0,
                "Comments": comments or "",
                "UserGuid": user_guid or "00000000-0000-0000-0000-000000000000",
                "GenerateInvoice": 1 if generate_invoice else 0,
                "PaymentReceived": payment_received or 0,
                "CheckNumber": check_number or ""
            }
            
            # Execute the reinstatement stored procedure
            result = self.data_access_service.execute_command("ReinstatePolicy", parameters)
            
            logger.info(f"Policy {control_number} reinstated successfully")
            
            # Parse the result
            if result and isinstance(result, dict):
                return {
                    "success": True,
                    "control_number": control_number,
                    "reinstatement_date": reinstatement_date,
                    "reinstatement_amount": result.get("ReinstatementAmount"),
                    "invoice_number": result.get("InvoiceNumber"),
                    "status": "reinstated",
                    "message": result.get("Message", "Policy reinstated successfully")
                }
            else:
                return {
                    "success": True,
                    "control_number": control_number,
                    "reinstatement_date": reinstatement_date,
                    "status": "reinstated",
                    "message": "Policy reinstated successfully"
                }
                
        except Exception as e:
            logger.error(f"Error reinstating policy {control_number}: {str(e)}")
            return {
                "success": False,
                "control_number": control_number,
                "error": str(e),
                "message": f"Failed to reinstate policy: {str(e)}"
            }
    
    def get_cancellation_reasons(self) -> List[Dict[str, Any]]:
        """
        Get available cancellation reasons from IMS
        
        Returns:
            List of cancellation reasons
        """
        try:
            query = """
                SELECT ID, Description, ReasonCode, AutomationID
                FROM lstQuoteStatusReasons
                WHERE QuoteStatusID = (SELECT QuoteStatusID FROM lstQuoteStatus WHERE Description = 'Cancelled')
                AND Active = 1
                ORDER BY Description
            """
            
            result = self.data_access_service.execute_query(query)
            
            if result and 'Tables' in result and len(result['Tables']) > 0:
                rows = result['Tables'][0].get('Rows', [])
                return [
                    {
                        "id": row.get("ID"),
                        "description": row.get("Description"),
                        "code": row.get("ReasonCode"),
                        "automation_id": row.get("AutomationID")
                    }
                    for row in rows
                ]
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching cancellation reasons: {str(e)}")
            return []
    
    def get_endorsement_reasons(self) -> List[Dict[str, Any]]:
        """
        Get available endorsement reasons from IMS
        
        Returns:
            List of endorsement reasons
        """
        try:
            query = """
                SELECT ID, Description, ReasonCode, AutomationID
                FROM lstQuoteStatusReasons
                WHERE Active = 1
                AND (Description LIKE '%endorse%' OR Description LIKE '%change%' OR Description LIKE '%modify%')
                ORDER BY Description
            """
            
            result = self.data_access_service.execute_query(query)
            
            if result and 'Tables' in result and len(result['Tables']) > 0:
                rows = result['Tables'][0].get('Rows', [])
                return [
                    {
                        "id": row.get("ID"),
                        "description": row.get("Description"),
                        "code": row.get("ReasonCode"),
                        "automation_id": row.get("AutomationID")
                    }
                    for row in rows
                ]
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching endorsement reasons: {str(e)}")
            return []
    
    def get_policy_by_control_number(self, control_number: int) -> Optional[Dict[str, Any]]:
        """
        Get policy information by control number
        
        Args:
            control_number: The policy control number
            
        Returns:
            Policy information if found
        """
        try:
            query = """
                SELECT TOP 1 
                    q.QuoteID, q.QuoteGuid, q.PolicyNumber,
                    q.Effective, q.Expiration, q.QuoteStatusID,
                    qs.Description as StatusDescription,
                    q.CancellationDate, q.EndorsementNumber,
                    q.ControlNum
                FROM tblQuotes q
                JOIN lstQuoteStatus qs ON qs.QuoteStatusID = q.QuoteStatusID
                WHERE q.ControlNum = @ControlNumber
                ORDER BY q.QuoteID DESC
            """
            
            result = self.data_access_service.execute_query(query, {"ControlNumber": control_number})
            
            if result and 'Tables' in result and len(result['Tables']) > 0:
                rows = result['Tables'][0].get('Rows', [])
                if rows:
                    row = rows[0]
                    return {
                        "quote_id": row.get("QuoteID"),
                        "quote_guid": row.get("QuoteGuid"),
                        "policy_number": row.get("PolicyNumber"),
                        "effective_date": row.get("Effective"),
                        "expiration_date": row.get("Expiration"),
                        "status_id": row.get("QuoteStatusID"),
                        "status": row.get("StatusDescription"),
                        "cancellation_date": row.get("CancellationDate"),
                        "endorsement_number": row.get("EndorsementNumber"),
                        "control_number": row.get("ControlNum")
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching policy by control number {control_number}: {str(e)}")
            return None
    
    def _format_date(self, date_value: Any) -> str:
        """Format date for IMS stored procedures"""
        if isinstance(date_value, str):
            return date_value
        elif isinstance(date_value, (date, datetime)):
            return date_value.strftime("%Y-%m-%d")
        else:
            return str(date_value)