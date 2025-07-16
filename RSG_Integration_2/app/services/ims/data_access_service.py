import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from .base_service import BaseIMSService
from .auth_service import AuthService

logger = logging.getLogger(__name__)

class DataAccessService(BaseIMSService):
    """Service for IMS DataAccess operations (stored procedures)"""
    
    def __init__(self, auth_service: AuthService):
        super().__init__("data_access")
        self.auth_service = auth_service
    
    def execute_command(self, procedure_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a stored procedure that returns a single result
        
        Note: _WS suffix is automatically appended by the service
        """
        try:
            token = self.auth_service.get_token()
            
            # Convert parameters to array of strings format
            # Format: ['@ParamName1', 'Value1', '@ParamName2', 'Value2', ...]
            params = []
            
            # Only add parameters if dictionary is not empty
            if parameters:
                for key, value in parameters.items():
                    # Do NOT add @ symbol - just use the parameter name as is
                    param_name = key.lstrip('@')  # Remove @ if present
                    params.append(param_name)
                    params.append(str(value) if value is not None else "")
            
            response = self.client.service.ExecuteCommand(
                procedureName=procedure_name,
                parameters=params,  # Changed from namedParameters
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
            
            # Convert parameters to array of strings format
            # Format: ['ParamName1', 'Value1', 'ParamName2', 'Value2', ...]
            params = []
            
            # Only add parameters if dictionary is not empty
            if parameters:
                for key, value in parameters.items():
                    # Do NOT add @ symbol - just use the parameter name as is
                    param_name = key.lstrip('@')  # Remove @ if present
                    params.append(param_name)
                    params.append(str(value) if value is not None else "")
            
            # Log the parameters being sent
            logger.info(f"Calling ExecuteDataSet with procedure: {procedure_name}")
            logger.info(f"Parameters array: {params}")
            logger.info(f"Parameters array length: {len(params)}")
            
            # Log the exact SOAP request that will be sent
            logger.info("=== SOAP REQUEST DEBUG ===")
            logger.info(f"Procedure name that will be sent: {procedure_name}")
            logger.info(f"Procedure name with _WS suffix: {procedure_name}_WS")
            logger.info("Parameter array that will be sent:")
            for i in range(0, len(params), 2):
                if i + 1 < len(params):
                    logger.info(f"  Param[{i}]: '{params[i]}' (name)")
                    logger.info(f"  Param[{i+1}]: '{params[i+1]}' (value)")
            logger.info("=== END SOAP DEBUG ===")
            
            # If no parameters, try passing None instead of empty array
            if len(params) == 0:
                logger.info("No parameters, passing None")
                response = self.client.service.ExecuteDataSet(
                    procedureName=procedure_name,
                    parameters=None,
                    _soapheaders=self.get_header(token)
                )
            else:
                response = self.client.service.ExecuteDataSet(
                    procedureName=procedure_name,
                    parameters=params,
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
    
    def get_quote_option_details(self, quote_option_guid: UUID) -> List[Dict[str, Any]]:
        """Get quote option details including the integer ID from a Quote Option GUID"""
        try:
            # spGetQuoteOptions_WS expects @QuoteOptionGuid parameter
            logger.info(f"Attempting to get quote option details for option GUID {quote_option_guid}")
            
            # Send the correct parameter name that the stored procedure expects
            params = {"QuoteOptionGuid": str(quote_option_guid)}
            
            results = self.execute_dataset("spGetQuoteOptions", params)
            
            logger.info(f"Retrieved {len(results)} quote option details for option {quote_option_guid}")
            return results
            
        except Exception as e:
            logger.error(f"Error getting quote options: {e}")
            raise
    
    def get_quote_option_id_from_option_guid(self, quote_option_guid: UUID) -> Optional[int]:
        """Get the integer quote option ID from a Quote Option GUID using spGetQuoteOptions_WS"""
        try:
            logger.info(f"Getting quote option ID for option GUID {quote_option_guid}")
            
            # Call get_quote_option_details which will use spGetQuoteOptions_WS
            results = self.get_quote_option_details(quote_option_guid)
            
            if results and len(results) > 0:
                # The stored procedure should return QuoteOptionID
                option_id = results[0].get('QuoteOptionID') or results[0].get('quoteoptionid')
                if option_id:
                    logger.info(f"Found quote option ID: {option_id}")
                    return int(option_id)
                else:
                    logger.warning(f"No QuoteOptionID field in results: {results[0].keys()}")
                    return None
            else:
                logger.warning("No results returned from spGetQuoteOptions_WS")
                return None
                
        except Exception as e:
            logger.error(f"Error getting quote option ID from option GUID: {e}")
            return None
    
    def get_quote_option_id(self, quote_guid: UUID) -> Optional[int]:
        """Get the integer quote option ID for a given quote GUID using simplified stored procedure"""
        try:
            logger.info(f"Getting quote option ID for {quote_guid} using spGetQuoteOptionID")
            
            # Try the simplified stored procedure that just returns the ID
            params = {
                "QuoteGuid": str(quote_guid)
            }
            
            results = self.execute_dataset("spGetQuoteOptionID", params)
            
            if results and len(results) > 0:
                option_id = results[0].get('QuoteOptionID')
                logger.info(f"Found quote option ID: {option_id}")
                return int(option_id) if option_id is not None else None
            else:
                logger.warning("No quote option ID found")
                return None
                
        except Exception as e:
            logger.error(f"Error getting quote option ID: {e}")
            # Return None instead of raising to allow fallback to other methods
            return None
    
    def get_quote_option_id_by_guid(self, quote_option_guid: UUID) -> Optional[int]:
        """Get the integer quote option ID for a given QUOTE OPTION GUID using spGetTritonQuoteData_WS"""
        try:
            logger.info(f"Getting quote option ID for quote option GUID {quote_option_guid} using spGetTritonQuoteData")
            
            # spGetTritonQuoteData_WS expects QuoteOptionGuid parameter
            params = {
                "QuoteOptionGuid": str(quote_option_guid)
            }
            
            results = self.execute_dataset("spGetTritonQuoteData", params)
            
            if results and len(results) > 0:
                option_id = results[0].get('quoteoptionid')  # Note: lowercase in response
                logger.info(f"SUCCESS: Found quote option ID: {option_id}")
                return int(option_id) if option_id is not None else None
            else:
                logger.warning("No quote option ID found")
                return None
                
        except Exception as e:
            logger.error(f"Error getting quote option ID by quote GUID: {e}")
            # Return None instead of raising to allow fallback to other methods
            return None