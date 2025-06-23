"""
Field mapping configurations for different source systems

This module defines how fields from external systems map to IMS fields
and which fields go to Excel rater vs standard IMS fields.
"""

from typing import Dict, Any, List, Optional
from enum import Enum


class FieldDestination(Enum):
    """Where a field should be stored in IMS"""
    IMS_STANDARD = "ims_standard"  # Standard IMS field
    EXCEL_RATER = "excel_rater"    # Excel rater field
    CUSTOM_TABLE = "custom_table"  # Custom database table
    BOTH = "both"                  # Both IMS and Excel rater


class FieldMapping:
    """Defines how a source field maps to IMS"""
    def __init__(self, 
                 source_field: str,
                 ims_field: Optional[str] = None,
                 excel_field: Optional[str] = None,
                 destination: FieldDestination = FieldDestination.IMS_STANDARD,
                 transform_func: Optional[callable] = None,
                 required: bool = False):
        self.source_field = source_field
        self.ims_field = ims_field
        self.excel_field = excel_field
        self.destination = destination
        self.transform_func = transform_func
        self.required = required


# Triton field mappings
TRITON_FIELD_MAPPINGS = {
    # Insured fields
    "insured_name": FieldMapping(
        source_field="insured_name",
        ims_field="InsuredName",
        destination=FieldDestination.IMS_STANDARD,
        required=True
    ),
    "insured_state": FieldMapping(
        source_field="insured_state",
        ims_field="State",
        excel_field="State",
        destination=FieldDestination.BOTH,
        required=True
    ),
    "insured_zip": FieldMapping(
        source_field="insured_zip",
        ims_field="ZipCode",
        destination=FieldDestination.IMS_STANDARD
    ),
    "business_type": FieldMapping(
        source_field="business_type",
        ims_field="BusinessTypeID",
        destination=FieldDestination.IMS_STANDARD,
        transform_func=lambda x: {
            "LLC": 5,
            "CORP": 1,
            "CORPORATION": 1,
            "PARTNERSHIP": 2,
            "INDIVIDUAL": 3,
            "SOLE PROP": 4
        }.get(x.upper() if x else "", 1)  # Default to Corporation (1)
    ),
    
    # Policy fields
    "policy_number": FieldMapping(
        source_field="policy_number",
        ims_field="PolicyNumber",
        excel_field="Policy_Number",
        destination=FieldDestination.BOTH
    ),
    "effective_date": FieldMapping(
        source_field="effective_date",
        ims_field="EffectiveDate",
        excel_field="Effective_Date",
        destination=FieldDestination.BOTH,
        required=True
    ),
    "expiration_date": FieldMapping(
        source_field="expiration_date",
        ims_field="ExpirationDate",
        excel_field="Expiration_Date",
        destination=FieldDestination.BOTH,
        required=True
    ),
    "bound_date": FieldMapping(
        source_field="bound_date",
        ims_field="BoundDate",
        destination=FieldDestination.IMS_STANDARD
    ),
    
    # Coverage fields
    "limit_amount": FieldMapping(
        source_field="limit_amount",
        excel_field="Limit",
        destination=FieldDestination.EXCEL_RATER,
        transform_func=lambda x: float(str(x).replace(",", "").replace("$", "")) if x else 0
    ),
    "deductible_amount": FieldMapping(
        source_field="deductible_amount",
        excel_field="Deductible",
        destination=FieldDestination.EXCEL_RATER,
        transform_func=lambda x: float(str(x).replace(",", "").replace("$", "")) if x else 0
    ),
    
    # Premium fields
    "gross_premium": FieldMapping(
        source_field="gross_premium",
        excel_field="Gross_Premium",
        destination=FieldDestination.EXCEL_RATER,
        transform_func=lambda x: float(str(x).replace(",", "").replace("$", "")) if x else 0
    ),
    "base_premium": FieldMapping(
        source_field="base_premium",
        excel_field="Base_Premium",
        destination=FieldDestination.EXCEL_RATER,
        transform_func=lambda x: float(str(x).replace(",", "").replace("$", "")) if x else 0
    ),
    "net_premium": FieldMapping(
        source_field="net_premium",
        destination=FieldDestination.CUSTOM_TABLE,
        transform_func=lambda x: float(str(x).replace(",", "").replace("$", "")) if x else 0
    ),
    
    # Commission fields
    "commission_rate": FieldMapping(
        source_field="commission_rate",
        excel_field="Commission_Rate",
        destination=FieldDestination.EXCEL_RATER
    ),
    "commission_percent": FieldMapping(
        source_field="commission_percent",
        excel_field="Commission_Percent",
        destination=FieldDestination.EXCEL_RATER
    ),
    "commission_amount": FieldMapping(
        source_field="commission_amount",
        destination=FieldDestination.CUSTOM_TABLE,
        transform_func=lambda x: float(str(x).replace(",", "").replace("$", "")) if x else 0
    ),
    
    # Fee fields
    "policy_fee": FieldMapping(
        source_field="policy_fee",
        excel_field="Policy_Fee",
        destination=FieldDestination.EXCEL_RATER,
        transform_func=lambda x: float(str(x).replace(",", "").replace("$", "")) if x else 0
    ),
    "surplus_lines_tax": FieldMapping(
        source_field="surplus_lines_tax",
        excel_field="Surplus_Lines_Tax",
        destination=FieldDestination.EXCEL_RATER,
        transform_func=lambda x: float(str(x).replace(",", "").replace("$", "")) if x else 0
    ),
    "stamping_fee": FieldMapping(
        source_field="stamping_fee",
        excel_field="Stamping_Fee",
        destination=FieldDestination.EXCEL_RATER,
        transform_func=lambda x: float(str(x).replace(",", "").replace("$", "")) if x else 0
    ),
    "other_fee": FieldMapping(
        source_field="other_fee",
        excel_field="Other_Fee",
        destination=FieldDestination.EXCEL_RATER,
        transform_func=lambda x: float(str(x).replace(",", "").replace("$", "")) if x else 0
    ),
    
    # Reference fields
    "producer_name": FieldMapping(
        source_field="producer_name",
        ims_field="ProducerName",
        destination=FieldDestination.IMS_STANDARD,
        required=True
    ),
    "underwriter_name": FieldMapping(
        source_field="underwriter_name",
        ims_field="UnderwriterName",
        destination=FieldDestination.IMS_STANDARD
    ),
    
    # Program fields
    "program_name": FieldMapping(
        source_field="program_name",
        excel_field="Program",
        destination=FieldDestination.EXCEL_RATER
    ),
    "class_of_business": FieldMapping(
        source_field="class_of_business",
        excel_field="Class_of_Business",
        destination=FieldDestination.EXCEL_RATER
    ),
    "umr": FieldMapping(
        source_field="umr",
        excel_field="UMR",
        destination=FieldDestination.EXCEL_RATER
    ),
    "agreement_number": FieldMapping(
        source_field="agreement_number",
        excel_field="Agreement_Number",
        destination=FieldDestination.EXCEL_RATER
    ),
    "section_number": FieldMapping(
        source_field="section_number",
        excel_field="Section_Number",
        destination=FieldDestination.EXCEL_RATER
    ),
    
    # Transaction fields
    "transaction_id": FieldMapping(
        source_field="transaction_id",
        destination=FieldDestination.CUSTOM_TABLE,
        required=True
    ),
    "transaction_date": FieldMapping(
        source_field="transaction_date",
        destination=FieldDestination.CUSTOM_TABLE,
        required=True
    ),
    "transaction_type": FieldMapping(
        source_field="transaction_type",
        destination=FieldDestination.CUSTOM_TABLE,
        required=True
    ),
    "source_system": FieldMapping(
        source_field="source_system",
        destination=FieldDestination.CUSTOM_TABLE,
        required=True
    ),
    
    # Additional fields
    "invoice_date": FieldMapping(
        source_field="invoice_date",
        excel_field="Invoice_Date",
        destination=FieldDestination.EXCEL_RATER
    ),
    "status": FieldMapping(
        source_field="status",
        destination=FieldDestination.CUSTOM_TABLE
    ),
    "limit_prior": FieldMapping(
        source_field="limit_prior",
        destination=FieldDestination.CUSTOM_TABLE
    ),
    
    # Opportunity fields
    "opportunities.id": FieldMapping(
        source_field="opportunities.id",
        destination=FieldDestination.CUSTOM_TABLE
    )
}


class FieldMapper:
    """Utility class for mapping fields between systems"""
    
    def __init__(self, mappings: Dict[str, FieldMapping]):
        self.mappings = mappings
    
    def get_ims_fields(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract fields that should go to standard IMS fields"""
        ims_data = {}
        
        for field_name, mapping in self.mappings.items():
            if mapping.destination in [FieldDestination.IMS_STANDARD, FieldDestination.BOTH]:
                source_value = self._get_nested_value(source_data, mapping.source_field)
                
                if source_value is not None and mapping.ims_field:
                    # Apply transformation if defined
                    if mapping.transform_func:
                        source_value = mapping.transform_func(source_value)
                    
                    ims_data[mapping.ims_field] = source_value
        
        return ims_data
    
    def get_excel_fields(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract fields that should go to Excel rater"""
        excel_data = {}
        
        for field_name, mapping in self.mappings.items():
            if mapping.destination in [FieldDestination.EXCEL_RATER, FieldDestination.BOTH]:
                source_value = self._get_nested_value(source_data, mapping.source_field)
                
                if source_value is not None and mapping.excel_field:
                    # Apply transformation if defined
                    if mapping.transform_func:
                        source_value = mapping.transform_func(source_value)
                    
                    excel_data[mapping.excel_field] = source_value
        
        return excel_data
    
    def get_custom_fields(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract fields that should go to custom tables"""
        custom_data = {}
        
        for field_name, mapping in self.mappings.items():
            if mapping.destination == FieldDestination.CUSTOM_TABLE:
                source_value = self._get_nested_value(source_data, mapping.source_field)
                
                if source_value is not None:
                    # Apply transformation if defined
                    if mapping.transform_func:
                        source_value = mapping.transform_func(source_value)
                    
                    custom_data[mapping.source_field] = source_value
        
        return custom_data
    
    def validate_required_fields(self, source_data: Dict[str, Any]) -> List[str]:
        """Validate that all required fields are present"""
        missing_fields = []
        
        for field_name, mapping in self.mappings.items():
            if mapping.required:
                value = self._get_nested_value(source_data, mapping.source_field)
                if value is None or value == "":
                    missing_fields.append(mapping.source_field)
        
        return missing_fields
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value


# Create mapper instances
triton_mapper = FieldMapper(TRITON_FIELD_MAPPINGS)


def get_mapper(source_system: str) -> FieldMapper:
    """Get the appropriate field mapper for a source system"""
    mappers = {
        "triton": triton_mapper,
        # Add other source system mappers here
    }
    
    return mappers.get(source_system.lower(), triton_mapper)