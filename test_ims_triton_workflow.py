#!/usr/bin/env python3
"""
Test script for IMS workflow with Triton payload

This script tests the complete IMS integration workflow with a sample
Triton payload containing all expected fields.
"""

import os
import sys
import json
from datetime import datetime, date
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ims.workflow_orchestrator import IMSWorkflowOrchestrator
from app.services.ims.field_mappings import triton_mapper
from app.models.transaction_models import Transaction, TransactionType, IMSProcessing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_triton_payload():
    """Create a sample Triton payload with all expected fields"""
    return {
        # Transaction fields
        "transaction_id": "TRITON-TEST-20240123-001",
        "transaction_date": datetime.now().isoformat(),
        "transaction_type": "NEW_BUSINESS",
        "source_system": "triton",
        
        # Policy fields
        "umr": "UMR123456",
        "agreement_number": "AGR-2024-001",
        "section_number": "SECT-001",
        "class_of_business": "Commercial Auto",
        "program_name": "AHC Primary",
        "policy_number": "TEST-POL-2024-001",
        
        # Insured fields
        "insured_name": "ABC Transport Company LLC",
        "insured_state": "TX",
        "insured_zip": "75001",
        "business_type": "LLC",
        
        # Producer/Underwriter
        "producer_name": "Test Producer Agency",
        "underwriter_name": "John Smith",
        
        # Dates
        "invoice_date": date.today().isoformat(),
        "effective_date": date.today().isoformat(),
        "expiration_date": date.today().replace(year=date.today().year + 1).isoformat(),
        "bound_date": date.today().isoformat(),
        "status": "BOUND",
        
        # Coverage details
        "limit_amount": "1000000",
        "limit_prior": "500000",
        "deductible_amount": "5000",
        
        # Premium and fees
        "gross_premium": "15000.00",
        "base_premium": "12000.00",
        "net_premium": "13500.00",
        "policy_fee": "250.00",
        "surplus_lines_tax": "600.00",
        "stamping_fee": "50.00",
        "other_fee": "100.00",
        
        # Commission
        "commission_rate": "10",
        "commission_percent": "10.00",
        "commission_amount": "1500.00",
        
        # Opportunities (if applicable)
        "opportunities": {
            "id": "OPP-12345"
        },
        
        # Additional insured
        "additional_insured": {
            "name": "XYZ Logistics Corp",
            "address": "456 Commerce St, Dallas, TX 75201"
        }
    }


def test_field_mapping(payload):
    """Test field mapping configuration"""
    print("\n=== Testing Field Mapping ===")
    
    # Get IMS fields
    ims_fields = triton_mapper.get_ims_fields(payload)
    print("\nIMS Standard Fields:")
    for field, value in ims_fields.items():
        print(f"  {field}: {value}")
    
    # Get Excel fields
    excel_fields = triton_mapper.get_excel_fields(payload)
    print("\nExcel Rater Fields:")
    for field, value in excel_fields.items():
        print(f"  {field}: {value}")
    
    # Get custom fields
    custom_fields = triton_mapper.get_custom_fields(payload)
    print("\nCustom Table Fields:")
    for field, value in custom_fields.items():
        print(f"  {field}: {value}")
    
    # Validate required fields
    missing_fields = triton_mapper.validate_required_fields(payload)
    if missing_fields:
        print(f"\n⚠️  Missing required fields: {missing_fields}")
    else:
        print("\n✅ All required fields present")


def test_workflow_orchestration(payload):
    """Test the complete workflow orchestration"""
    print("\n\n=== Testing Workflow Orchestration ===")
    
    # Create transaction
    transaction = Transaction(
        transaction_id=payload["transaction_id"],
        transaction_type=TransactionType.POLICY_BINDING,
        source_system="triton",
        external_id=payload["transaction_id"],
        created_at=datetime.now()
    )
    
    # Add IMS processing
    transaction.ims_processing = IMSProcessing()
    
    # Set parsed data
    transaction.parsed_data = payload
    
    # Initialize orchestrator
    orchestrator = IMSWorkflowOrchestrator(environment="ims_one")
    
    print(f"\nProcessing transaction: {transaction.transaction_id}")
    print(f"Insured: {payload['insured_name']}")
    print(f"Producer: {payload['producer_name']}")
    print(f"Premium: ${payload['gross_premium']}")
    
    try:
        # Process transaction
        result = orchestrator.process_transaction(transaction)
        
        print(f"\n✅ Workflow completed successfully!")
        print(f"Status: {result.ims_processing.status.value}")
        
        if result.ims_processing.insured:
            print(f"Insured GUID: {result.ims_processing.insured.guid}")
            
        if result.ims_processing.quote:
            print(f"Quote GUID: {result.ims_processing.quote.guid}")
            print(f"Premium: ${result.ims_processing.quote.premium}")
            
        if result.ims_processing.policy:
            print(f"Policy Number: {result.ims_processing.policy.policy_number}")
        
        # Print processing logs
        print("\nProcessing Logs:")
        for log in result.ims_processing.logs[-10:]:  # Last 10 logs
            print(f"  {log}")
            
    except Exception as e:
        print(f"\n❌ Workflow failed: {str(e)}")
        logger.error("Workflow error", exc_info=True)
        
        # Print any logs that were captured
        if transaction.ims_processing and transaction.ims_processing.logs:
            print("\nProcessing Logs:")
            for log in transaction.ims_processing.logs:
                print(f"  {log}")


def test_midterm_endorsement():
    """Test midterm endorsement processing"""
    print("\n\n=== Testing Midterm Endorsement ===")
    
    payload = create_sample_triton_payload()
    
    # Modify for endorsement
    payload["transaction_type"] = "ENDORSEMENT"
    payload["transaction_id"] = "TRITON-TEST-20240123-002"
    
    # Add endorsement details
    payload["opportunities_midterm_endorsements"] = {
        "endorsement_id": "END-001",
        "description": "Add vehicle to policy",
        "premium": "500.00",
        "effective_date": date.today().isoformat(),
        "endorsement_number": "1"
    }
    
    print("Endorsement payload created")
    print(f"  Endorsement ID: {payload['opportunities_midterm_endorsements']['endorsement_id']}")
    print(f"  Description: {payload['opportunities_midterm_endorsements']['description']}")
    print(f"  Premium: ${payload['opportunities_midterm_endorsements']['premium']}")


def main():
    """Run all tests"""
    print("IMS Integration Test Suite")
    print("=" * 60)
    
    # Create sample payload
    payload = create_sample_triton_payload()
    
    print("\nSample Triton Payload:")
    print(json.dumps(payload, indent=2))
    
    # Test field mapping
    test_field_mapping(payload)
    
    # Test workflow orchestration
    test_workflow_orchestration(payload)
    
    # Test endorsement
    test_midterm_endorsement()
    
    print("\n" + "=" * 60)
    print("Test suite completed!")


if __name__ == "__main__":
    main()