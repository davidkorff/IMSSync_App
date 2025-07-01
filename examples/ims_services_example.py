#!/usr/bin/env python3
"""
Example script demonstrating the use of modular IMS services

This script shows how to:
1. Use individual IMS services for specific operations
2. Use the workflow orchestrator for complete workflows
3. Handle errors and check results
"""

import os
import sys
from datetime import datetime, date

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ims import (
    IMSInsuredService,
    IMSProducerService,
    IMSQuoteService,
    IMSDocumentService,
    IMSDataAccessService
)
from app.services.ims.workflow_orchestrator import IMSWorkflowOrchestrator
from app.models.transaction_models import Transaction, TransactionType, IMSProcessing
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_individual_services():
    """Example of using individual IMS services"""
    print("\n=== Example: Using Individual IMS Services ===\n")
    
    # Initialize services
    environment = "ims_one"  # or "iscmga_test"
    insured_service = IMSInsuredService(environment)
    producer_service = IMSProducerService(environment)
    quote_service = IMSQuoteService(environment)
    
    try:
        # 1. Find or create an insured
        print("1. Finding/Creating Insured...")
        insured_data = {
            "name": "Test Corporation ABC",
            "tax_id": "12-3456789",
            "business_type": "corporation",
            "address": "123 Test Street",
            "city": "Dallas",
            "state": "TX",
            "zip_code": "75001"
        }
        
        insured_guid = insured_service.find_or_create_insured(insured_data)
        print(f"   Insured GUID: {insured_guid}")
        
        # 2. Add a location to the insured
        print("\n2. Adding Location...")
        location_data = {
            "address": "456 Branch Ave",
            "city": "Houston",
            "state": "TX",
            "zip_code": "77001",
            "description": "Houston Branch Office"
        }
        
        location_id = insured_service.add_insured_location(insured_guid, location_data)
        print(f"   Location ID: {location_id}")
        
        # 3. Search for a producer
        print("\n3. Searching for Producer...")
        producers = producer_service.search_producer("Test Producer")
        if producers:
            producer_guid = producers[0].get('ProducerLocationGuid')
            print(f"   Found Producer: {producers[0].get('ProducerName')}")
            print(f"   Producer GUID: {producer_guid}")
        else:
            # Use default producer
            producer_guid = producer_service.get_default_producer_guid("triton")
            print(f"   Using default producer: {producer_guid}")
        
        # 4. Create a submission
        print("\n4. Creating Submission...")
        submission_data = {
            "insured_guid": insured_guid,
            "producer_contact_guid": producer_guid,
            "producer_location_guid": producer_guid,
            "submission_date": date.today(),
            "underwriter_guid": "00000000-0000-0000-0000-000000000000"
        }
        
        submission_guid = quote_service.create_submission(submission_data)
        print(f"   Submission GUID: {submission_guid}")
        
        # 5. Create a quote
        print("\n5. Creating Quote...")
        quote_data = {
            "submission_guid": submission_guid,
            "effective_date": date.today(),
            "expiration_date": date.today().replace(year=date.today().year + 1),
            "state": "TX",
            "line_guid": quote_service.get_default_line_guid("triton", "primary"),
            "quoting_location_guid": "00000000-0000-0000-0000-000000000000",
            "issuing_location_guid": "00000000-0000-0000-0000-000000000000",
            "company_location_guid": "00000000-0000-0000-0000-000000000000",
            "producer_contact_guid": producer_guid
        }
        
        quote_guid = quote_service.create_quote(quote_data)
        print(f"   Quote GUID: {quote_guid}")
        
        # 6. Add a quote option and premium
        print("\n6. Adding Quote Option and Premium...")
        option_id = quote_service.add_quote_option(quote_guid)
        print(f"   Quote Option ID: {option_id}")
        
        # Add premium
        premium_added = quote_service.add_premium(
            quote_guid,
            option_id,
            1500.00,
            "Annual Premium"
        )
        print(f"   Premium Added: {premium_added}")
        
        print("\n✅ Individual services example completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error in individual services example: {str(e)}")
        logger.error(f"Error details: {str(e)}", exc_info=True)


def example_workflow_orchestrator():
    """Example of using the workflow orchestrator"""
    print("\n\n=== Example: Using Workflow Orchestrator ===\n")
    
    # Initialize orchestrator
    orchestrator = IMSWorkflowOrchestrator(environment="ims_one")
    
    try:
        # Create a sample transaction
        transaction = Transaction(
            transaction_id="TEST-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
            transaction_type=TransactionType.POLICY_BINDING,
            source_system="triton",
            external_id="TRITON-12345",
            created_at=datetime.now()
        )
        
        # Add IMS processing tracking
        transaction.ims_processing = IMSProcessing()
        
        # Set parsed data (normally this would come from the source system)
        transaction.parsed_data = {
            "source_system": "triton",
            "external_id": "TRITON-12345",
            "insured_name": "Workflow Test Company",
            "tax_id": "98-7654321",
            "business_type": "corporation",
            "address": "789 Workflow St",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "effective_date": date.today().strftime("%Y-%m-%d"),
            "expiration_date": date.today().replace(year=date.today().year + 1).strftime("%Y-%m-%d"),
            "premium": 2500.00,
            "line_of_business": "General Liability",
            "bound_date": date.today().strftime("%Y-%m-%d"),
            "producer": {
                "name": "Test Producer Agency"
            }
        }
        
        print("Processing transaction through workflow orchestrator...")
        print(f"Transaction ID: {transaction.transaction_id}")
        
        # Process the transaction
        result = orchestrator.process_transaction(transaction)
        
        # Check results
        print(f"\nWorkflow Status: {result.ims_processing.status.value}")
        
        if result.ims_processing.insured:
            print(f"Insured GUID: {result.ims_processing.insured.guid}")
            
        if result.ims_processing.submission:
            print(f"Submission GUID: {result.ims_processing.submission.guid}")
            
        if result.ims_processing.quote:
            print(f"Quote GUID: {result.ims_processing.quote.guid}")
            print(f"Premium: ${result.ims_processing.quote.premium}")
            
        if result.ims_processing.policy:
            print(f"Policy Number: {result.ims_processing.policy.policy_number}")
        
        print("\n✅ Workflow orchestrator example completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error in workflow orchestrator example: {str(e)}")
        logger.error(f"Error details: {str(e)}", exc_info=True)


def example_data_access():
    """Example of using the data access service"""
    print("\n\n=== Example: Using Data Access Service ===\n")
    
    # Initialize service
    data_service = IMSDataAccessService(environment="ims_one")
    
    try:
        # 1. Get lookup data
        print("1. Getting Business Types...")
        business_types = data_service.get_lookup_data("business_types")
        print(f"   Found {len(business_types)} business types")
        
        # 2. Execute a query
        print("\n2. Executing Custom Query...")
        query = "SELECT TOP 5 InsuredGUID, InsuredName FROM Insureds WHERE Active = 1"
        results = data_service.execute_query(query)
        
        if results and 'Tables' in results:
            print(f"   Query returned results")
        
        # 3. Find entity by external ID
        print("\n3. Searching for Entity by External ID...")
        entity = data_service.find_entity_by_external_id("TRITON-12345", "triton")
        if entity:
            print(f"   Found entity: {entity}")
        else:
            print("   No entity found")
        
        print("\n✅ Data access example completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error in data access example: {str(e)}")
        logger.error(f"Error details: {str(e)}", exc_info=True)


def main():
    """Run all examples"""
    print("IMS Services Examples")
    print("=" * 50)
    
    # Run examples
    example_individual_services()
    example_workflow_orchestrator()
    example_data_access()
    
    print("\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    main()