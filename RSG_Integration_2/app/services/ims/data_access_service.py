import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from .base_service import BaseIMSService
from .auth_service import AuthService
from zeep import Plugin
from lxml import etree

logger = logging.getLogger(__name__)

class LoggingPlugin(Plugin):
    """Plugin to log raw SOAP XML requests and responses"""
    
    def ingress(self, envelope, http_headers, operation):
        # Log incoming response
        logger.info("=== SOAP RESPONSE XML ===")
        logger.info(etree.tostring(envelope, pretty_print=True, encoding='unicode'))
        return envelope, http_headers
    
    def egress(self, envelope, http_headers, operation, binding_options):
        # Log outgoing request
        logger.info("=== SOAP REQUEST XML ===")
        logger.info(etree.tostring(envelope, pretty_print=True, encoding='unicode'))
        logger.info("=== END SOAP REQUEST ===")
        return envelope, http_headers

class DataAccessService(BaseIMSService):
    """Service for IMS DataAccess operations (stored procedures)"""
    
    def __init__(self, auth_service: AuthService):
        super().__init__("data_access")
        self.auth_service = auth_service
        # Add the logging plugin to capture SOAP XML
        self.client.plugins.append(LoggingPlugin())
        
        # Log available types in the WSDL for debugging
        try:
            logger.info("Available types in DataAccess WSDL:")
            for service in self.client.wsdl.services.values():
                for port in service.ports.values():
                    for operation in port.binding._operations.values():
                        logger.info(f"Operation: {operation.name}")
                        if operation.name == 'ExecuteDataSet':
                            logger.info(f"  Input: {operation.input}")
                            logger.info(f"  Output: {operation.output}")
        except Exception as e:
            logger.debug(f"Could not inspect WSDL types: {e}")
    
    def execute_command(self, procedure_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a stored procedure that returns a single result
        
        Note: _WS suffix is automatically appended by the service
        """
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
            logger.info(f"Calling ExecuteCommand with procedure: {procedure_name}")
            logger.info(f"Parameters array: {params}")
            
            if len(params) == 0:
                logger.info("No parameters, passing None")
                response = self.client.service.ExecuteCommand(
                    procedureName=procedure_name,
                    parameters=None,
                    _soapheaders=self.get_header(token)
                )
            else:
                # Use ArrayOfString type from WSDL (same fix as ExecuteDataSet)
                try:
                    logger.info("Using ArrayOfString type from WSDL")
                    array_type = self.client.get_type('{http://tempuri.org/IMSWebServices/DataAccess}ArrayOfString')
                    params_array = array_type(params)
                    logger.info(f"Created ArrayOfString with: {params_array}")
                    
                    response = self.client.service.ExecuteCommand(
                        procedureName=procedure_name,
                        parameters=params_array,
                        _soapheaders=self.get_header(token)
                    )
                except Exception as e:
                    logger.warning(f"ArrayOfString approach failed: {e}")
                    # Fallback to raw array
                    response = self.client.service.ExecuteCommand(
                        procedureName=procedure_name,
                        parameters=params,
                        _soapheaders=self.get_header(token)
                    )
            
            logger.info(f"Executed stored procedure: {procedure_name}")
            logger.info(f"Response: {response}")
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
            
            # Log the exact XML that will be sent for Postman
            logger.info("\n" + "="*50)
            logger.info("COPY THIS XML TO POSTMAN:")
            logger.info("="*50)
            logger.info("URL: https://webservices.mgasystems.com/ims_demo/Dataaccess.asmx")
            logger.info("Method: POST")
            logger.info("Headers:")
            logger.info("  Content-Type: text/xml; charset=utf-8")
            logger.info("  SOAPAction: \"http://tempuri.org/IMSWebServices/DataAccess/ExecuteDataSet\"")
            logger.info("\nBody:")
            
            # Build the XML manually for logging
            param_xml = ""
            if params:
                for param in params:
                    param_xml += f"        <string>{param}</string>\n"
            
            soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <Token>{token}</Token>
      <Context>RSG</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <ExecuteDataSet xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <procedureName>{procedure_name}</procedureName>
      <parameters>
{param_xml.rstrip()}
      </parameters>
    </ExecuteDataSet>
  </soap:Body>
</soap:Envelope>"""
            
            logger.info(soap_body)
            logger.info("=" * 50 + "\n")
            
            # Try different approaches to fix the array serialization issue
            # Zeep is only sending the first element of our array
            
            if len(params) == 0:
                logger.info("No parameters, passing None")
                response = self.client.service.ExecuteDataSet(
                    procedureName=procedure_name,
                    parameters=None,
                    _soapheaders=self.get_header(token)
                )
            else:
                # Try to get the ArrayOfString type from the WSDL
                try:
                    logger.info("Attempting to use ArrayOfString type from WSDL")
                    # First, let's see what types are available
                    array_type = self.client.get_type('{http://tempuri.org/IMSWebServices/DataAccess}ArrayOfString')
                    params_array = array_type(params)
                    logger.info(f"Created ArrayOfString with: {params_array}")
                    
                    response = self.client.service.ExecuteDataSet(
                        procedureName=procedure_name,
                        parameters=params_array,
                        _soapheaders=self.get_header(token)
                    )
                except Exception as e:
                    logger.warning(f"ArrayOfString approach failed: {e}")
                    
                    # Fallback: Try passing as dict
                    logger.info("Trying dict approach with 'string' key")
                    params_dict = {'string': params}
                    
                    response = self.client.service.ExecuteDataSet(
                        procedureName=procedure_name,
                        parameters=params_dict,
                        _soapheaders=self.get_header(token)
                    )
            
            logger.info(f"Executed dataset procedure: {procedure_name}")
            logger.info(f"Raw response type: {type(response)}")
            logger.info(f"Raw response: {response}")
            
            # Parse the dataset response
            results = []
            
            # The response might be a string containing escaped XML
            if isinstance(response, str):
                logger.info("Response is a string, parsing embedded XML")
                try:
                    # Parse the embedded XML
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response)
                    
                    # Look for Table elements
                    for table in root.findall('.//Table'):
                        result_dict = {}
                        for child in table:
                            result_dict[child.tag] = child.text
                        results.append(result_dict)
                    
                    logger.info(f"Parsed {len(results)} results from embedded XML")
                except Exception as xml_e:
                    logger.error(f"Failed to parse embedded XML: {xml_e}")
                    logger.debug(f"Response content: {response[:500]}")
            
            # Handle structured response (if Zeep parses it for us)
            elif hasattr(response, 'Tables') and response.Tables:
                logger.info("Response has Tables attribute")
                table = response.Tables.DataTable[0]
                if hasattr(table, 'Rows') and table.Rows:
                    for row in table.Rows.DataRow:
                        result_dict = {}
                        for i, value in enumerate(row):
                            if hasattr(table, 'Columns') and i < len(table.Columns.DataColumn):
                                column_name = table.Columns.DataColumn[i].ColumnName
                                result_dict[column_name] = value
                        results.append(result_dict)
            
            logger.info(f"Returning {len(results)} results")
            if results:
                logger.info(f"First result: {results[0]}")
            
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
        """Get the integer quote option ID from a Quote Option GUID using spGetQuoteOptionIDFromGuid_WS"""
        try:
            logger.info(f"Getting quote option ID for option GUID {quote_option_guid}")
            
            # Use the dedicated stored procedure for getting ID from GUID
            return self.get_quote_option_id_by_guid(quote_option_guid)
                
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
        """Get the integer quote option ID for a given QUOTE OPTION GUID using spGetQuoteOptionIDFromGuid_WS"""
        try:
            logger.info(f"Getting quote option ID for quote option GUID {quote_option_guid} using spGetQuoteOptionIDFromGuid")
            
            # spGetQuoteOptionIDFromGuid_WS expects QuoteOptionGuid parameter
            params = {
                "QuoteOptionGuid": str(quote_option_guid)
            }
            
            results = self.execute_dataset("spGetQuoteOptionIDFromGuid", params)
            
            if results and len(results) > 0:
                # The stored procedure returns QuoteOptionID
                option_id = results[0].get('QuoteOptionID') or results[0].get('quoteoptionid')
                if option_id:
                    logger.info(f"SUCCESS: Found quote option ID: {option_id}")
                    return int(option_id)
                else:
                    logger.warning(f"No QuoteOptionID field in results: {results[0].keys()}")
                    return None
            else:
                logger.warning("No results returned from spGetQuoteOptionIDFromGuid_WS")
                return None
                
        except Exception as e:
            logger.error(f"Error getting quote option ID by quote option GUID: {e}")
            # Return None instead of raising to allow fallback to other methods
            return None