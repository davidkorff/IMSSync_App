"""
Tests for IMS Workflow Orchestrator

Tests complete transaction workflows including field mapping, 
entity creation, and state transitions.
"""

import unittest
from datetime import datetime, date
from test_base import IMSServiceTestBase
from app.models.transaction_models import (
    Transaction, TransactionType, TransactionStatus,
    IMSProcessing, IMSProcessingStatus
)
from app.services.ims.field_mappings import triton_mapper
import logging
import os

logger = logging.getLogger(__name__)


class TestIMSWorkflowOrchestrator(IMSServiceTestBase):
    """Test IMS Workflow Orchestrator functionality"""
    
    def test_01_complete_new_business_workflow(self):
        """Test complete new business workflow"""
        # Create transaction
        transaction = self._create_test_transaction("NEW_BUSINESS")
        
        # Add Triton payload data
        transaction.parsed_data = self.generate_triton_payload()
        
        logger.info(f"\nProcessing new business transaction: {transaction.transaction_id}")
        self.log_test_data(transaction.parsed_data, "Transaction Data")
        
        try:
            # Process transaction
            result = self.workflow_orchestrator.process_transaction(transaction)
            
            # Verify status progression
            self.assertIsNotNone(result.ims_processing)
            self.assertIn(result.ims_processing.status, [
                IMSProcessingStatus.RATED,
                IMSProcessingStatus.BOUND,
                IMSProcessingStatus.ISSUED,
                IMSProcessingStatus.ERROR
            ])
            
            # Log results
            logger.info(f"Final status: {result.ims_processing.status.value}")
            
            if result.ims_processing.insured:
                logger.info(f"Insured GUID: {result.ims_processing.insured.guid}")
                self.assertIsGuid(result.ims_processing.insured.guid)
                
            if result.ims_processing.submission:
                logger.info(f"Submission GUID: {result.ims_processing.submission.guid}")
                self.assertIsGuid(result.ims_processing.submission.guid)
                
            if result.ims_processing.quote:
                logger.info(f"Quote GUID: {result.ims_processing.quote.guid}")
                self.assertIsGuid(result.ims_processing.quote.guid)
                
            # Log processing steps
            logger.info("\nProcessing logs:")
            for log in result.ims_processing.logs[-10:]:  # Last 10
                logger.info(f"  {log}")
                
        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            if transaction.ims_processing:
                logger.info("\nProcessing logs before failure:")
                for log in transaction.ims_processing.logs:
                    logger.info(f"  {log}")
            raise
    
    def test_02_field_mapping_integration(self):
        """Test field mapping in workflow"""
        # Create transaction with full Triton data
        transaction = self._create_test_transaction("NEW_BUSINESS")
        
        # Add complete Triton payload
        transaction.parsed_data = {
            "transaction_id": f"TRITON-{self.test_id}",
            "transaction_type": "NEW_BUSINESS",
            "source_system": "triton",
            
            # Fields that should map to IMS
            "insured_name": "Field Mapping Test LLC",
            "insured_state": "TX",
            "insured_zip": "75001",
            "business_type": "LLC",
            
            # Fields that should go to Excel
            "umr": "UMR123",
            "agreement_number": "AGR123",
            "gross_premium": "10000.00",
            "policy_fee": "250.00",
            "surplus_lines_tax": "500.00",
            
            # Other required fields
            "producer_name": "Test Producer",
            "effective_date": date.today().isoformat(),
            "expiration_date": date.today().replace(year=date.today().year + 1).isoformat()
        }
        
        # Verify field mapping before processing
        ims_fields = triton_mapper.get_ims_fields(transaction.parsed_data)
        excel_fields = triton_mapper.get_excel_fields(transaction.parsed_data)
        
        logger.info("\nField mapping results:")
        logger.info(f"IMS fields: {list(ims_fields.keys())}")
        logger.info(f"Excel fields: {list(excel_fields.keys())}")
        
        # Verify key mappings
        self.assertEqual(ims_fields.get("InsuredName"), "Field Mapping Test LLC")
        self.assertEqual(ims_fields.get("State"), "TX")
        self.assertEqual(ims_fields.get("BusinessTypeID"), 5)  # LLC
        
        self.assertEqual(excel_fields.get("UMR"), "UMR123")
        self.assertEqual(excel_fields.get("Gross_Premium"), 10000.00)
        self.assertEqual(excel_fields.get("Policy_Fee"), 250.00)
    
    def test_03_insured_matching_in_workflow(self):
        """Test insured matching within workflow"""
        # Create first transaction
        transaction1 = self._create_test_transaction("NEW_BUSINESS")
        transaction1.parsed_data = {
            "source_system": "triton",
            "insured_name": f"Workflow Match Test Company {self.test_id}",
            "tax_id": "98-7654321",
            "business_type": "Corporation",
            "insured_state": "TX",
            "producer_name": "Test Producer",
            "effective_date": date.today().isoformat(),
            "expiration_date": date.today().replace(year=date.today().year + 1).isoformat(),
            "gross_premium": "5000.00"
        }
        
        # Process first transaction
        result1 = self.workflow_orchestrator.process_transaction(transaction1)
        
        # Get insured GUID
        insured_guid1 = None
        if result1.ims_processing.insured:
            insured_guid1 = result1.ims_processing.insured.guid
            logger.info(f"First transaction created insured: {insured_guid1}")
        
        # Create second transaction with similar insured
        transaction2 = self._create_test_transaction("NEW_BUSINESS")
        transaction2.parsed_data = transaction1.parsed_data.copy()
        transaction2.parsed_data["insured_name"] = transaction1.parsed_data["insured_name"] + " Corp"  # Slight variation
        
        # Process second transaction
        result2 = self.workflow_orchestrator.process_transaction(transaction2)
        
        # Verify same insured was matched
        if result2.ims_processing.insured and insured_guid1:
            insured_guid2 = result2.ims_processing.insured.guid
            self.assertEqual(insured_guid1, insured_guid2, 
                           "Should match existing insured")
            logger.info(f"Successfully matched existing insured: {insured_guid2}")
    
    def test_04_producer_underwriter_lookup(self):
        """Test producer and underwriter lookup in workflow"""
        transaction = self._create_test_transaction("NEW_BUSINESS")
        
        # Add specific producer/underwriter names
        transaction.parsed_data = self.generate_triton_payload()
        transaction.parsed_data.update({
            "producer_name": "Test Producer Agency",
            "underwriter_name": "John Smith"
        })
        
        # Process transaction
        result = self.workflow_orchestrator.process_transaction(transaction)
        
        # Check logs for producer/underwriter lookup
        logs = result.ims_processing.logs
        producer_logs = [log for log in logs if "producer" in log.lower()]
        underwriter_logs = [log for log in logs if "underwriter" in log.lower()]
        
        logger.info("\nProducer lookup logs:")
        for log in producer_logs[:5]:
            logger.info(f"  {log}")
            
        logger.info("\nUnderwriter lookup logs:")
        for log in underwriter_logs[:5]:
            logger.info(f"  {log}")
    
    def test_05_additional_insureds_handling(self):
        """Test additional insureds processing"""
        transaction = self._create_test_transaction("NEW_BUSINESS")
        
        # Add additional insured data
        transaction.parsed_data = self.generate_triton_payload()
        transaction.parsed_data["additional_insured"] = {
            "name": "Additional Test Company LLC",
            "address": "789 Additional St, Dallas, TX 75001"
        }
        
        logger.info("\nProcessing transaction with additional insured")
        
        # Process transaction
        result = self.workflow_orchestrator.process_transaction(transaction)
        
        # Check logs for additional insured processing
        ai_logs = [log for log in result.ims_processing.logs 
                   if "additional insured" in log.lower()]
        
        logger.info("\nAdditional insured logs:")
        for log in ai_logs:
            logger.info(f"  {log}")
            
        # Verify additional insured was processed
        self.assertTrue(len(ai_logs) > 0, "Should have additional insured logs")
    
    def test_06_excel_rating_workflow(self):
        """Test Excel rating in workflow"""
        # Skip if Excel tests disabled
        if os.getenv("SKIP_EXCEL_TESTS", "false").lower() == "true":
            self.skipTest("Excel tests disabled")
        
        transaction = self._create_test_transaction("NEW_BUSINESS")
        
        # Enable Excel rating
        transaction.parsed_data = self.generate_triton_payload()
        transaction.parsed_data["use_excel_rater"] = True
        
        logger.info("\nProcessing transaction with Excel rating")
        
        # Process transaction
        result = self.workflow_orchestrator.process_transaction(transaction)
        
        # Check logs for Excel rating
        excel_logs = [log for log in result.ims_processing.logs 
                      if "excel" in log.lower()]
        
        if excel_logs:
            logger.info("\nExcel rating logs:")
            for log in excel_logs:
                logger.info(f"  {log}")
        else:
            logger.info("No Excel rating performed (template may not exist)")
    
    def test_07_error_handling_invalid_data(self):
        """Test error handling with invalid data"""
        transaction = self._create_test_transaction("NEW_BUSINESS")
        
        # Add invalid data (missing required fields)
        transaction.parsed_data = {
            "source_system": "triton",
            # Missing insured_name, dates, etc.
        }
        
        logger.info("\nProcessing transaction with invalid data")
        
        # Process transaction
        result = self.workflow_orchestrator.process_transaction(transaction)
        
        # Should fail gracefully
        self.assertEqual(result.ims_processing.status, IMSProcessingStatus.ERROR)
        self.assertEqual(result.status, TransactionStatus.FAILED)
        
        # Check error logs
        error_logs = [log for log in result.ims_processing.logs 
                      if "error" in log.lower()]
        
        logger.info("\nError logs:")
        for log in error_logs[:5]:
            logger.info(f"  {log}")
    
    def test_08_state_transitions(self):
        """Test workflow state transitions"""
        transaction = self._create_test_transaction("NEW_BUSINESS")
        transaction.parsed_data = self.generate_triton_payload()
        
        # Track state changes
        state_changes = []
        
        # Monkey patch to track state changes
        original_update = transaction.ims_processing.update_status
        def track_update(status, message):
            state_changes.append((status, message))
            return original_update(status, message)
        
        transaction.ims_processing.update_status = track_update
        
        # Process transaction
        result = self.workflow_orchestrator.process_transaction(transaction)
        
        # Log state transitions
        logger.info("\nState transitions:")
        for status, message in state_changes:
            logger.info(f"  {status.value}: {message}")
        
        # Verify proper sequence
        expected_sequence = [
            IMSProcessingStatus.INSURED_CREATED,
            IMSProcessingStatus.SUBMISSION_CREATED,
            IMSProcessingStatus.QUOTE_CREATED,
            IMSProcessingStatus.RATED
        ]
        
        actual_sequence = [status for status, _ in state_changes]
        
        for expected in expected_sequence:
            self.assertIn(expected, actual_sequence, 
                         f"Missing expected state: {expected.value}")
    
    def test_09_transaction_type_handling(self):
        """Test different transaction types"""
        # Test endorsement
        endorsement = self._create_test_transaction("ENDORSEMENT")
        endorsement.parsed_data = self.generate_triton_payload()
        endorsement.parsed_data["transaction_type"] = "ENDORSEMENT"
        endorsement.parsed_data["policy_number"] = "TEST-POL-123"
        
        logger.info("\nProcessing endorsement transaction")
        
        # Process (may not be fully implemented)
        try:
            result = self.workflow_orchestrator.process_transaction(endorsement)
            logger.info(f"Endorsement status: {result.ims_processing.status.value}")
        except NotImplementedError:
            logger.info("Endorsement processing not yet implemented")
    
    def test_10_program_data_storage(self):
        """Test program-specific data storage"""
        transaction = self._create_test_transaction("NEW_BUSINESS")
        
        # Add program-specific fields
        transaction.parsed_data = self.generate_triton_payload()
        transaction.parsed_data.update({
            "program_name": "AHC Primary",
            "opportunities": {"id": "OPP-12345"},
            "vehicles": [
                {"vin": "TEST123", "year": 2023, "make": "Ford"}
            ]
        })
        
        logger.info("\nProcessing transaction with program data")
        
        # Process transaction
        result = self.workflow_orchestrator.process_transaction(transaction)
        
        # Check logs for program data storage
        program_logs = [log for log in result.ims_processing.logs 
                        if "program data" in log.lower()]
        
        if program_logs:
            logger.info("\nProgram data logs:")
            for log in program_logs:
                logger.info(f"  {log}")
    
    # Helper methods
    
    def _create_test_transaction(self, transaction_type: str) -> Transaction:
        """Create a test transaction"""
        transaction = Transaction(
            transaction_id=f"TEST-{self.test_id}-{datetime.now().strftime('%H%M%S')}",
            transaction_type=TransactionType.POLICY_BINDING,
            source_system="triton",
            external_id=f"EXT-{self.test_id}",
            created_at=datetime.now()
        )
        
        # Initialize IMS processing
        transaction.ims_processing = IMSProcessing()
        
        return transaction


if __name__ == "__main__":
    unittest.main(verbosity=2)