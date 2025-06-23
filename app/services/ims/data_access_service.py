"""
IMS Data Access Service

This service handles all data access operations in IMS including:
- Executing queries
- Executing commands (stored procedures)
- Managing custom data
"""

import logging
from typing import Dict, Any, Optional, List
import json

from app.services.ims.base_service import BaseIMSService

logger = logging.getLogger(__name__)


class IMSDataAccessService(BaseIMSService):
    """Service for data access operations in IMS"""
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a query and return the results
        
        Args:
            query: The SQL query to execute
            parameters: Optional dictionary of parameters
            
        Returns:
            Dictionary containing the query results
        """
        self._log_operation("execute_query", {"query": query[:100]})  # Log first 100 chars
        
        try:
            result = self.soap_client.execute_data_set(query, parameters)
            
            if result:
                logger.info(f"Query executed successfully")
                return result
            else:
                logger.warning(f"Query returned no results")
                return {}
                
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "execute_query")
                # Retry once
                return self.soap_client.execute_data_set(query, parameters)
            raise
    
    def execute_command(self, command: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a command (stored procedure) and return the result
        
        Args:
            command: The stored procedure name
            parameters: Optional dictionary of parameters
            
        Returns:
            The command execution result
        """
        self._log_operation("execute_command", {
            "command": command,
            "params": list(parameters.keys()) if parameters else []
        })
        
        try:
            result = self.soap_client.execute_command(command, parameters)
            
            logger.info(f"Command {command} executed successfully")
            return result
                
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "execute_command")
                # Retry once
                return self.soap_client.execute_command(command, parameters)
            raise
    
    def store_program_data(self, program: str, quote_guid: str, 
                          external_id: str, data: Dict[str, Any]) -> bool:
        """
        Store program-specific data using custom stored procedures
        
        Args:
            program: The program name (e.g., 'triton', 'xuber')
            quote_guid: The IMS quote GUID
            external_id: The external system ID
            data: The data to store
            
        Returns:
            True if successful
        """
        self._log_operation("store_program_data", {
            "program": program,
            "quote_guid": quote_guid,
            "external_id": external_id
        })
        
        try:
            # Map program to stored procedure
            sp_mapping = {
                "triton": "StoreRSGTritonData_WS",
                "xuber": "StoreRSGXuberData_WS",
                "default": "StoreRSGProgramData_WS"
            }
            
            stored_proc = sp_mapping.get(program.lower(), sp_mapping["default"])
            
            # Prepare parameters
            parameters = {
                "QuoteGUID": str(quote_guid),
                "ExternalID": external_id,
                "ProgramData": json.dumps(data),
                "CreatedDate": data.get("created_date", ""),
                "ModifiedDate": data.get("modified_date", "")
            }
            
            # Add program-specific parameters
            if program.lower() == "triton":
                parameters.update(self._extract_triton_params(data))
            elif program.lower() == "xuber":
                parameters.update(self._extract_xuber_params(data))
            
            # Execute the stored procedure
            result = self.execute_command(stored_proc, parameters)
            
            if result:
                logger.info(f"Successfully stored {program} data for quote {quote_guid}")
                return True
            else:
                logger.error(f"Failed to store {program} data for quote {quote_guid}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing program data: {str(e)}")
            # Don't raise - this is supplementary data storage
            return False
    
    def get_lookup_data(self, lookup_type: str) -> List[Dict[str, Any]]:
        """
        Get lookup data from IMS (e.g., business types, states, etc.)
        
        Args:
            lookup_type: The type of lookup data to retrieve
            
        Returns:
            List of lookup items
        """
        self._log_operation("get_lookup_data", {"lookup_type": lookup_type})
        
        # Map lookup types to queries
        query_mapping = {
            "business_types": "SELECT BusinessTypeID, Description FROM BusinessTypes WHERE Active = 1",
            "states": "SELECT StateID, StateName, StateAbbrev FROM States WHERE Active = 1",
            "lines": "SELECT LineGUID, LineName, LineCode FROM Lines WHERE Active = 1",
            "companies": "SELECT CompanyGUID, CompanyName FROM Companies WHERE Active = 1",
            "locations": "SELECT LocationGUID, LocationName, LocationCode FROM Locations WHERE Active = 1"
        }
        
        query = query_mapping.get(lookup_type.lower())
        if not query:
            logger.warning(f"Unknown lookup type: {lookup_type}")
            return []
        
        try:
            result = self.execute_query(query)
            
            if result and 'Tables' in result:
                # Extract rows from the first table
                tables = result.get('Tables', {})
                if tables and len(tables) > 0:
                    first_table = tables[0]
                    rows = first_table.get('Rows', [])
                    
                    logger.info(f"Retrieved {len(rows)} {lookup_type}")
                    return rows
            
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving lookup data: {str(e)}")
            return []
    
    def find_entity_by_external_id(self, external_id: str, 
                                  external_system: str) -> Optional[Dict[str, Any]]:
        """
        Find an IMS entity by its external system ID
        
        Args:
            external_id: The external system's ID
            external_system: The name of the external system
            
        Returns:
            Dictionary with entity information if found
        """
        self._log_operation("find_entity_by_external_id", {
            "external_id": external_id,
            "external_system": external_system
        })
        
        query = """
        SELECT q.QuoteGUID, q.QuoteNumber, q.PolicyNumber, 
               q.InsuredGUID, q.SubmissionGUID, q.QuoteStatusID
        FROM Quotes q
        WHERE q.ExternalQuoteID = @ExternalID 
          AND q.ExternalSystemID = @ExternalSystem
        """
        
        parameters = {
            "ExternalID": external_id,
            "ExternalSystem": external_system
        }
        
        try:
            result = self.execute_query(query, parameters)
            
            if result and 'Tables' in result:
                tables = result.get('Tables', {})
                if tables and len(tables) > 0:
                    rows = tables[0].get('Rows', [])
                    if rows and len(rows) > 0:
                        logger.info(f"Found entity for {external_system}/{external_id}")
                        return rows[0]
            
            logger.info(f"No entity found for {external_system}/{external_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding entity by external ID: {str(e)}")
            return None
    
    def _extract_triton_params(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Triton-specific parameters"""
        params = {}
        
        # Vehicle information
        if "vehicles" in data and isinstance(data["vehicles"], list):
            params["VehicleCount"] = len(data["vehicles"])
            params["VehicleData"] = json.dumps(data["vehicles"])
        
        # Location information
        if "locations" in data and isinstance(data["locations"], list):
            params["LocationCount"] = len(data["locations"])
            params["LocationData"] = json.dumps(data["locations"])
        
        # Coverage information
        if "coverages" in data:
            params["CoverageData"] = json.dumps(data["coverages"])
        
        # Premium information
        params["TotalPremium"] = str(data.get("premium", 0.0))
        params["OriginalPremium"] = str(data.get("original_premium", data.get("premium", 0.0)))
        
        return params
    
    def _extract_xuber_params(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Xuber-specific parameters"""
        params = {}
        
        # Driver information
        if "drivers" in data and isinstance(data["drivers"], list):
            params["DriverCount"] = len(data["drivers"])
            params["DriverData"] = json.dumps(data["drivers"])
        
        # Vehicle information
        if "vehicles" in data and isinstance(data["vehicles"], list):
            params["VehicleCount"] = len(data["vehicles"])
            params["VehicleData"] = json.dumps(data["vehicles"])
        
        # Coverage limits
        if "coverage_limits" in data:
            params["CoverageLimits"] = json.dumps(data["coverage_limits"])
        
        # Premium breakdown
        params["BasePremium"] = str(data.get("base_premium", 0.0))
        params["TotalPremium"] = str(data.get("total_premium", 0.0))
        params["Fees"] = str(data.get("fees", 0.0))
        
        return params