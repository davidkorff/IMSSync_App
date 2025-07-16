import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from .base_service import BaseIMSService
from .auth_service import AuthService

logger = logging.getLogger(__name__)

class DataAccessService(BaseIMSService):
    """Service for IMS DataAccess operations (stored procedures)"""
    
    def __init__(self, auth_service: AuthService):
        super().__init__("dataaccess")
        self.auth_service = auth_service
    
    def execute_command(self, procedure_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a stored procedure that returns a single result
        
        Note: _WS suffix is automatically appended by the service
        """
        try:
            token = self.auth_service.get_token()
            
            # Convert parameters to the format IMS expects
            named_params = []
            for key, value in parameters.items():
                named_params.append({"Name": key, "Value": str(value) if value is not None else ""})
            
            response = self.client.service.ExecuteCommand(
                procedureName=procedure_name,
                namedParameters=named_params,
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Executed stored procedure: {procedure_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error executing stored procedure {procedure_name}: {e}")
            raise
    
    def execute_dataset(self, procedure_name: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a stored procedure that returns multiple rows"""
        try:
            token = self.auth_service.get_token()
            
            # Convert parameters to the format IMS expects
            named_params = []
            for key, value in parameters.items():
                named_params.append({"Name": key, "Value": str(value) if value is not None else ""})
            
            response = self.client.service.ExecuteDataSet(
                procedureName=procedure_name,
                namedParameters=named_params,
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Executed dataset procedure: {procedure_name}")
            
            # Parse the dataset response into a list of dictionaries
            results = []
            if hasattr(response, 'Tables') and response.Tables:
                table = response.Tables.DataTable[0]
                if hasattr(table, 'Rows') and table.Rows:
                    for row in table.Rows.DataRow:
                        result_dict = {}
                        for i, value in enumerate(row):
                            if hasattr(table, 'Columns') and i < len(table.Columns.DataColumn):
                                column_name = table.Columns.DataColumn[i].ColumnName
                                result_dict[column_name] = value
                        results.append(result_dict)
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing dataset procedure {procedure_name}: {e}")
            raise
    
    def store_triton_data(self, quote_guid: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        """Store Triton data using the custom stored procedure"""
        try:
            params = {
                "QuoteGuid": str(quote_guid),
                "TransactionID": data.get("transaction_id"),
                "PriorTransactionID": data.get("prior_transaction_id"),
                "OpportunityID": data.get("opportunity_id"),
                "OpportunityType": data.get("opportunity_type"),
                "PolicyFee": data.get("policy_fee"),
                "SurplusLinesTax": data.get("surplus_lines_tax"),
                "StampingFee": data.get("stamping_fee"),
                "OtherFee": data.get("other_fee"),
                "CommissionPercent": data.get("commission_percent"),
                "CommissionAmount": data.get("commission_amount"),
                "NetPremium": data.get("net_premium"),
                "BasePremium": data.get("base_premium"),
                "Status": data.get("status"),
                "LimitPrior": data.get("limit_prior"),
                "InvoiceDate": data.get("invoice_date")
            }
            
            # Note: _WS suffix is added automatically
            response = self.execute_command("spAddTritonQuoteData", params)
            
            logger.info(f"Stored Triton data for quote {quote_guid}")
            return {"success": True, "response": response}
            
        except Exception as e:
            logger.error(f"Error storing Triton data: {e}")
            raise
    
    def get_triton_data(self, quote_guid: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve Triton data for a quote"""
        try:
            params = {"QuoteGuid": str(quote_guid)}
            
            # Note: _WS suffix is added automatically
            results = self.execute_dataset("spGetTritonQuoteData", params)
            
            if results:
                logger.info(f"Retrieved Triton data for quote {quote_guid}")
                return results[0]  # Return first row
            else:
                logger.info(f"No Triton data found for quote {quote_guid}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving Triton data: {e}")
            raise
    
    def get_quote_option_details(self, quote_guid: UUID) -> List[Dict[str, Any]]:
        """Get quote options with their IDs for a quote"""
        try:
            # This would need a stored procedure like:
            # CREATE PROCEDURE spGetQuoteOptions_WS
            #     @QuoteGuid UNIQUEIDENTIFIER
            # AS
            # BEGIN
            #     SELECT QuoteOptionID, QuoteOptionGuid, LineGuid, PremiumTotal
            #     FROM tblQuoteOptions
            #     WHERE QuoteGuid = @QuoteGuid
            # END
            
            params = {"QuoteGuid": str(quote_guid)}
            results = self.execute_dataset("spGetQuoteOptions", params)
            
            logger.info(f"Retrieved {len(results)} quote options for quote {quote_guid}")
            return results
            
        except Exception as e:
            logger.error(f"Error getting quote options: {e}")
            raise