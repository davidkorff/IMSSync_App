"""
Data Access Microservice Implementation
"""

import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from cachetools import TTLCache

from app.microservices.core import (
    BaseMicroservice, 
    ServiceConfig, 
    ServiceResponse,
    ServiceError
)
from .models import (
    QueryRequest,
    QueryResponse,
    CommandRequest,
    CommandResponse,
    ProgramData,
    LookupData,
    LookupType
)


class DataAccessService(BaseMicroservice):
    """
    Microservice for data access operations in IMS
    Provides query execution, stored procedures, and data caching
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        if not config:
            config = ServiceConfig(
                name="data_access",
                version="1.0.0",
                enable_caching=True,
                cache_ttl=300  # 5 minutes
            )
        super().__init__(config)
        
        # Initialize cache for lookup data
        self._lookup_cache = TTLCache(maxsize=100, ttl=config.cache_ttl)
    
    def _on_initialize(self):
        """Service-specific initialization"""
        self.logger.info("Data Access service specific initialization")
        # Preload common lookup data if needed
    
    def _on_shutdown(self):
        """Service-specific shutdown"""
        self.logger.info("Data Access service specific shutdown")
        self._lookup_cache.clear()
    
    async def execute_query(self, request: QueryRequest) -> ServiceResponse:
        """
        Execute a SQL query and return results
        
        Args:
            request: Query request with SQL and parameters
            
        Returns:
            ServiceResponse with QueryResponse data
        """
        self._log_operation("execute_query", {
            "query_preview": request.query[:100],
            "param_count": len(request.parameters)
        })
        
        start_time = time.time()
        
        try:
            # Execute query through SOAP client
            result = self.soap_client.service.ExecuteDataSet(
                Query=request.query,
                Parameters=self._prepare_parameters(request.parameters)
            )
            
            # Parse results
            tables = []
            row_count = 0
            
            if result and hasattr(result, 'Tables'):
                for table in result.Tables:
                    table_data = {
                        "name": getattr(table, 'TableName', 'Table'),
                        "columns": [],
                        "rows": []
                    }
                    
                    # Get columns
                    if hasattr(table, 'Columns'):
                        table_data["columns"] = [col.ColumnName for col in table.Columns]
                    
                    # Get rows
                    if hasattr(table, 'Rows'):
                        for row in table.Rows:
                            row_data = {}
                            for i, col in enumerate(table_data["columns"]):
                                row_data[col] = getattr(row, f'Column{i}', None)
                            table_data["rows"].append(row_data)
                        
                        row_count += len(table_data["rows"])
                    
                    tables.append(table_data)
            
            execution_time = (time.time() - start_time) * 1000
            
            response = QueryResponse(
                success=True,
                tables=tables,
                row_count=row_count,
                execution_time_ms=execution_time
            )
            
            return ServiceResponse(
                success=True,
                data=response
            )
            
        except Exception as e:
            return self._handle_error(e, "execute_query")
    
    async def execute_command(self, request: CommandRequest) -> ServiceResponse:
        """
        Execute a stored procedure and return results
        
        Args:
            request: Command request with procedure name and parameters
            
        Returns:
            ServiceResponse with CommandResponse data
        """
        self._log_operation("execute_command", {
            "command": request.command,
            "param_count": len(request.parameters)
        })
        
        start_time = time.time()
        
        try:
            # Execute command through SOAP client
            result = self.soap_client.service.ExecuteCommand(
                CommandText=request.command,
                Parameters=self._prepare_parameters(request.parameters)
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            response = CommandResponse(
                success=True,
                result=result,
                execution_time_ms=execution_time
            )
            
            return ServiceResponse(
                success=True,
                data=response
            )
            
        except Exception as e:
            return self._handle_error(e, "execute_command")
    
    async def store_program_data(self, data: ProgramData) -> ServiceResponse:
        """
        Store program-specific data using custom stored procedures
        
        Args:
            data: Program data to store
            
        Returns:
            ServiceResponse indicating success
        """
        self._log_operation("store_program_data", {
            "program": data.program,
            "quote_guid": data.quote_guid,
            "external_id": data.external_id
        })
        
        try:
            # Map program to stored procedure
            sp_mapping = {
                "triton": "StoreRSGTritonData_WS",
                "xuber": "StoreRSGXuberData_WS",
                "default": "StoreRSGProgramData_WS"
            }
            
            stored_proc = sp_mapping.get(data.program.lower(), sp_mapping["default"])
            
            # Prepare parameters
            parameters = {
                "QuoteGUID": data.quote_guid,
                "ExternalID": data.external_id,
                "ProgramData": json.dumps(data.data),
                "CreatedDate": (data.created_date or datetime.now()).isoformat(),
                "ModifiedDate": (data.modified_date or datetime.now()).isoformat()
            }
            
            # Add program-specific parameters
            if data.program.lower() == "triton":
                parameters.update(self._extract_triton_params(data.data))
            elif data.program.lower() == "xuber":
                parameters.update(self._extract_xuber_params(data.data))
            
            # Execute stored procedure
            request = CommandRequest(
                command=stored_proc,
                parameters=parameters
            )
            
            result = await self.execute_command(request)
            
            if result.success:
                return ServiceResponse(
                    success=True,
                    data={"stored": True},
                    metadata={
                        "program": data.program,
                        "quote_guid": data.quote_guid
                    }
                )
            else:
                return result
                
        except Exception as e:
            return self._handle_error(e, "store_program_data")
    
    async def get_lookup_data(self, lookup_type: LookupType) -> ServiceResponse:
        """
        Get lookup data from IMS (cached)
        
        Args:
            lookup_type: Type of lookup data to retrieve
            
        Returns:
            ServiceResponse with LookupData
        """
        self._log_operation("get_lookup_data", {"lookup_type": lookup_type.value})
        
        # Check cache first
        if self.config.enable_caching and lookup_type in self._lookup_cache:
            cached_data = self._lookup_cache[lookup_type]
            return ServiceResponse(
                success=True,
                data=cached_data,
                metadata={"cached": True}
            )
        
        try:
            # Map lookup types to queries
            query_mapping = {
                LookupType.BUSINESS_TYPES: 
                    "SELECT BusinessTypeID, Description FROM BusinessTypes WHERE Active = 1 ORDER BY Description",
                LookupType.STATES: 
                    "SELECT StateID, StateName, StateAbbrev FROM States WHERE Active = 1 ORDER BY StateName",
                LookupType.LINES: 
                    "SELECT LineGUID, LineName, LineCode FROM Lines WHERE Active = 1 ORDER BY LineName",
                LookupType.COMPANIES: 
                    "SELECT CompanyGUID, CompanyName FROM Companies WHERE Active = 1 ORDER BY CompanyName",
                LookupType.LOCATIONS: 
                    "SELECT LocationGUID, LocationName, LocationCode FROM Locations WHERE Active = 1 ORDER BY LocationName",
                LookupType.CANCELLATION_REASONS:
                    "SELECT ReasonID, ReasonDescription FROM CancellationReasons WHERE Active = 1 ORDER BY ReasonDescription",
                LookupType.ENDORSEMENT_REASONS:
                    "SELECT ReasonID, ReasonDescription FROM EndorsementReasons WHERE Active = 1 ORDER BY ReasonDescription",
                LookupType.REINSTATEMENT_REASONS:
                    "SELECT ReasonID, ReasonDescription FROM ReinstatementReasons WHERE Active = 1 ORDER BY ReasonDescription",
                LookupType.PAYMENT_TERMS:
                    "SELECT PaymentTermsID, Description FROM PaymentTerms WHERE Active = 1 ORDER BY Description",
                LookupType.BILLING_TYPES:
                    "SELECT BillingTypeID, Description FROM BillingTypes WHERE Active = 1 ORDER BY Description"
            }
            
            query = query_mapping.get(lookup_type)
            if not query:
                return ServiceResponse(
                    success=False,
                    error=f"Unknown lookup type: {lookup_type}"
                )
            
            # Execute query
            query_request = QueryRequest(query=query)
            result = await self.execute_query(query_request)
            
            if result.success and result.data.tables:
                items = result.data.tables[0].get("rows", [])
                
                lookup_data = LookupData(
                    lookup_type=lookup_type,
                    items=items,
                    count=len(items),
                    cached=False,
                    cache_expires=datetime.now() + timedelta(seconds=self.config.cache_ttl)
                )
                
                # Cache the result
                if self.config.enable_caching:
                    self._lookup_cache[lookup_type] = lookup_data
                
                return ServiceResponse(
                    success=True,
                    data=lookup_data
                )
            else:
                return result
                
        except Exception as e:
            return self._handle_error(e, "get_lookup_data")
    
    async def find_entity_by_external_id(
        self, 
        external_id: str, 
        external_system: str
    ) -> ServiceResponse:
        """
        Find an IMS entity by its external system ID
        
        Args:
            external_id: External system's ID
            external_system: Name of the external system
            
        Returns:
            ServiceResponse with entity information
        """
        self._log_operation("find_entity_by_external_id", {
            "external_id": external_id,
            "external_system": external_system
        })
        
        query = """
        SELECT q.QuoteGUID, q.QuoteNumber, q.PolicyNumber, 
               q.InsuredGUID, q.SubmissionGUID, q.QuoteStatusID,
               i.CorporationName as InsuredName
        FROM Quotes q
        LEFT JOIN Insureds i ON q.InsuredGUID = i.InsuredGUID
        WHERE q.ExternalQuoteID = @ExternalID 
          AND q.ExternalSystemID = @ExternalSystem
        """
        
        request = QueryRequest(
            query=query,
            parameters={
                "ExternalID": external_id,
                "ExternalSystem": external_system
            }
        )
        
        result = await self.execute_query(request)
        
        if result.success and result.data.row_count > 0:
            entity = result.data.tables[0]["rows"][0]
            return ServiceResponse(
                success=True,
                data=entity,
                metadata={"found": True}
            )
        else:
            return ServiceResponse(
                success=True,
                data=None,
                metadata={"found": False}
            )
    
    def _prepare_parameters(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert parameters to SOAP format"""
        soap_params = []
        
        for key, value in params.items():
            param = {
                "Name": key,
                "Value": str(value) if value is not None else "",
                "DataType": self._get_data_type(value)
            }
            soap_params.append(param)
        
        return soap_params
    
    def _get_data_type(self, value: Any) -> str:
        """Determine SQL data type from Python value"""
        if isinstance(value, bool):
            return "bit"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "decimal"
        elif isinstance(value, datetime):
            return "datetime"
        else:
            return "nvarchar"
    
    def _extract_triton_params(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Triton-specific parameters"""
        params = {}
        
        # Vehicle information
        if "vehicles" in data and isinstance(data["vehicles"], list):
            params["VehicleCount"] = len(data["vehicles"])
            params["VehicleData"] = json.dumps(data["vehicles"])
        
        # Coverage information
        if "coverages" in data:
            params["CoverageData"] = json.dumps(data["coverages"])
        
        # Premium information
        params["TotalPremium"] = str(data.get("premium", 0.0))
        
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
        
        return params
    
    async def _get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        return {
            "cache_size": len(self._lookup_cache),
            "cache_ttl": self.config.cache_ttl
        }