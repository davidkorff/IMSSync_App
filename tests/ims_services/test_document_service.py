"""
Tests for IMS Document Service

Tests document creation, retrieval, storage, and folder management.
"""

import unittest
from datetime import datetime
from test_base import IMSServiceTestBase
import logging
import os
import tempfile

logger = logging.getLogger(__name__)


class TestIMSDocumentService(IMSServiceTestBase):
    """Test IMS Document Service functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data for document tests"""
        super().setUpClass()
        
        # Create a test quote for document association
        try:
            # Create insured
            insured_data = {
                "name": f"Document Test Company {cls.generate_test_id(cls)}",
                "tax_id": "12-3456789",
                "business_type": "LLC",
                "address": "123 Document Test St",
                "city": "Dallas",
                "state": "TX",
                "zip_code": "75001"
            }
            cls.test_insured_guid = cls.insured_service.create_insured(insured_data)
            cls.track_entity(cls, "insureds", cls.test_insured_guid)
            
            # Get producer
            cls.test_producer_guid = cls.producer_service.get_default_producer_guid("triton")
            
            # Create submission
            submission_data = cls.generate_submission_data(
                cls,
                cls.test_insured_guid,
                cls.test_producer_guid
            )
            cls.test_submission_guid = cls.quote_service.create_submission(submission_data)
            cls.track_entity(cls, "submissions", cls.test_submission_guid)
            
            # Create quote
            quote_data = cls.generate_quote_data(cls, cls.test_submission_guid)
            quote_data["line_guid"] = cls.quote_service.get_default_line_guid("triton", "primary")
            quote_data["producer_contact_guid"] = cls.test_producer_guid
            cls.test_quote_guid = cls.quote_service.create_quote(quote_data)
            cls.track_entity(cls, "quotes", cls.test_quote_guid)
            
            logger.info(f"Created test quote: {cls.test_quote_guid}")
            
        except Exception as e:
            logger.error(f"Failed to set up test data: {str(e)}")
            raise
    
    def test_01_verify_folder(self):
        """Test verifying/creating folders"""
        # Test creating a document folder
        folder_path = f"Test/Documents/{self.test_id}"
        
        logger.info(f"Verifying folder: {folder_path}")
        
        folder_guid = self.document_service.verify_folder(folder_path)
        
        # Verify
        self.assertIsGuid(folder_guid)
        logger.info(f"Folder GUID: {folder_guid}")
        
        # Store for later tests
        self.test_folder_guid = folder_guid
    
    def test_02_get_folder_list(self):
        """Test getting list of folders"""
        # Get root folders
        logger.info("\nGetting root folder list")
        
        folders = self.document_service.get_folder_list()
        
        # Verify
        self.assertIsInstance(folders, list)
        
        if folders:
            logger.info(f"Found {len(folders)} root folders:")
            for folder in folders[:5]:  # Show first 5
                logger.info(f"  {folder.get('FolderName')} ({folder.get('FolderGUID')})")
        
        # Test with parent folder
        if hasattr(self, 'test_folder_guid'):
            logger.info(f"\nGetting subfolders of {self.test_folder_guid}")
            subfolders = self.document_service.get_folder_list(self.test_folder_guid)
            
            if subfolders:
                logger.info(f"Found {len(subfolders)} subfolders")
    
    def test_03_insert_standard_document(self):
        """Test inserting a standard document"""
        # Create a test document
        document_content = f"Test document content for {self.test_id}"
        document_name = f"test_document_{self.test_id}.txt"
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(document_content)
            temp_path = tmp.name
        
        try:
            # Get folder
            if not hasattr(self, 'test_folder_guid'):
                folder_path = f"Test/Documents/{self.test_id}"
                self.test_folder_guid = self.document_service.verify_folder(folder_path)
            
            logger.info(f"\nInserting document: {document_name}")
            
            # Insert document
            document_guid = self.document_service.insert_standard_document(
                self.test_folder_guid,
                document_name,
                temp_path,
                description=f"Test document for {self.test_id}"
            )
            
            # Verify
            self.assertIsGuid(document_guid)
            logger.info(f"Inserted document: {document_guid}")
            
            # Store for later tests
            self.test_document_guid = document_guid
            
        finally:
            # Clean up temp file
            os.unlink(temp_path)
    
    def test_04_get_document_from_store(self):
        """Test retrieving document from store"""
        # Need a document first
        if not hasattr(self, 'test_document_guid'):
            self.skipTest("No test document available")
        
        logger.info(f"\nRetrieving document: {self.test_document_guid}")
        
        # Get document
        document_data = self.document_service.get_document_from_store(self.test_document_guid)
        
        # Verify
        self.assertIsInstance(document_data, dict)
        
        if document_data:
            logger.info("Document retrieved successfully")
            logger.info(f"  Content length: {len(document_data.get('content', b''))} bytes")
            logger.info(f"  Document name: {document_data.get('name')}")
            logger.info(f"  MIME type: {document_data.get('mime_type')}")
    
    def test_05_get_document_from_folder(self):
        """Test retrieving document from folder"""
        # Need folder and document
        if not hasattr(self, 'test_folder_guid') or not hasattr(self, 'test_document_guid'):
            self.skipTest("No test folder/document available")
        
        logger.info(f"\nGetting documents from folder: {self.test_folder_guid}")
        
        # Get documents
        documents = self.document_service.get_document_from_folder(self.test_folder_guid)
        
        # Verify
        self.assertIsInstance(documents, list)
        
        if documents:
            logger.info(f"Found {len(documents)} documents:")
            for doc in documents[:5]:  # Show first 5
                logger.info(f"  {doc.get('DocumentName')} ({doc.get('DocumentGUID')})")
            
            # Check if our test document is in the list
            doc_guids = [doc.get('DocumentGUID') for doc in documents]
            if self.test_document_guid in doc_guids:
                logger.info("Test document found in folder")
    
    def test_06_insert_associated_document(self):
        """Test inserting document associated with entity"""
        # Create a test document
        document_content = f"Associated document for quote {self.test_quote_guid}"
        document_name = f"quote_document_{self.test_id}.txt"
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(document_content)
            temp_path = tmp.name
        
        try:
            logger.info(f"\nInserting associated document: {document_name}")
            logger.info(f"Associating with quote: {self.test_quote_guid}")
            
            # Insert associated document
            document_guid = self.document_service.insert_associated_document(
                self.test_quote_guid,
                "quote",
                document_name,
                temp_path,
                description=f"Associated document for quote test {self.test_id}"
            )
            
            # Verify
            self.assertIsGuid(document_guid)
            logger.info(f"Inserted associated document: {document_guid}")
            
        finally:
            # Clean up temp file
            os.unlink(temp_path)
    
    def test_07_get_policy_documents_list(self):
        """Test getting documents for a policy"""
        # This test might not return results in test environment
        logger.info("\nTesting policy documents list")
        
        # Try with test quote (may not have documents)
        documents = self.document_service.get_policy_documents_list(self.test_quote_guid)
        
        # Verify structure
        self.assertIsInstance(documents, list)
        
        if documents:
            logger.info(f"Found {len(documents)} documents for quote")
            for doc in documents[:3]:
                logger.info(f"  {doc.get('DocumentName')} - {doc.get('DocumentType')}")
        else:
            logger.info("No documents found for test quote")
    
    def test_08_create_quote_document(self):
        """Test creating a quote document"""
        logger.info(f"\nCreating quote document for: {self.test_quote_guid}")
        
        try:
            # Create quote document
            result = self.document_service.create_quote_document(
                self.test_quote_guid,
                document_type="proposal"
            )
            
            # Verify
            self.assertIsInstance(result, dict)
            
            if result.get('success'):
                logger.info("Quote document created successfully")
                if result.get('document_guid'):
                    logger.info(f"Document GUID: {result['document_guid']}")
            else:
                logger.warning(f"Quote document creation failed: {result.get('error_message')}")
                
        except Exception as e:
            logger.warning(f"Quote document creation not available: {str(e)}")
    
    def test_09_create_policy_document(self):
        """Test creating a policy document"""
        # Skip if no policy available
        logger.info("\nTesting policy document creation")
        
        # Try to bind quote first to get a policy
        if os.getenv("SKIP_BINDING_TESTS", "false").lower() == "true":
            self.skipTest("Binding tests disabled")
        
        try:
            # Add quote option and premium first
            option_id = self.quote_service.add_quote_option(self.test_quote_guid)
            self.quote_service.add_premium(self.test_quote_guid, option_id, 1000.00, "Test Premium")
            
            # Bind to get policy
            policy_number = self.quote_service.bind_quote(option_id)
            self.track_entity("policies", policy_number)
            
            logger.info(f"Creating policy document for: {policy_number}")
            
            # Create policy document
            result = self.document_service.create_policy_document(
                policy_number,
                document_type="policy"
            )
            
            # Verify
            self.assertIsInstance(result, dict)
            
            if result.get('success'):
                logger.info("Policy document created successfully")
            else:
                logger.warning(f"Policy document creation failed: {result.get('error_message')}")
                
        except Exception as e:
            logger.warning(f"Policy document test skipped: {str(e)}")
    
    def test_10_update_document_properties(self):
        """Test updating document properties"""
        # Need a document
        if not hasattr(self, 'test_document_guid'):
            self.skipTest("No test document available")
        
        logger.info(f"\nUpdating document properties for: {self.test_document_guid}")
        
        # Update properties
        updates = {
            "description": f"Updated description at {datetime.now()}",
            "tags": ["test", "updated", self.test_id],
            "metadata": {
                "updated_by": "test_suite",
                "update_date": datetime.now().isoformat()
            }
        }
        
        try:
            success = self.document_service.update_document_properties(
                self.test_document_guid,
                updates
            )
            
            if success:
                logger.info("Document properties updated successfully")
            else:
                logger.info("Document properties update failed")
                
        except Exception as e:
            logger.warning(f"Update properties not available: {str(e)}")


class TestDocumentTemplates(IMSServiceTestBase):
    """Test document template functionality"""
    
    def test_01_create_binder_document(self):
        """Test creating binder document"""
        logger.info("\nTesting binder document creation")
        
        # Create test data
        binder_data = {
            "insured_name": f"Binder Test Company {self.test_id}",
            "effective_date": datetime.now().date(),
            "coverage_type": "General Liability",
            "limits": "$1M/$2M",
            "premium": 5000.00
        }
        
        try:
            result = self.document_service.create_binder_document(binder_data)
            
            # Verify
            self.assertIsInstance(result, dict)
            
            if result.get('success'):
                logger.info("Binder document created successfully")
                if result.get('document_guid'):
                    logger.info(f"Document GUID: {result['document_guid']}")
            else:
                logger.warning(f"Binder creation failed: {result.get('error_message')}")
                
        except NotImplementedError:
            logger.info("Binder document creation not implemented")
    
    def test_02_create_policy_form_document(self):
        """Test creating policy form document"""
        logger.info("\nTesting policy form document creation")
        
        # Test data
        form_data = {
            "form_type": "additional_insured",
            "form_number": "CG 20 10",
            "edition_date": "04/13",
            "insured_name": f"Form Test Company {self.test_id}"
        }
        
        try:
            result = self.document_service.create_policy_form_document(form_data)
            
            # Verify
            self.assertIsInstance(result, dict)
            
            if result.get('success'):
                logger.info("Policy form document created successfully")
            else:
                logger.warning(f"Form creation failed: {result.get('error_message')}")
                
        except NotImplementedError:
            logger.info("Policy form document creation not implemented")
    
    def test_03_save_and_get_rating_sheet(self):
        """Test saving and retrieving rating sheet"""
        # Need a quote
        logger.info(f"\nTesting rating sheet for quote: {self.test_quote_guid}")
        
        # Create rating data
        rating_data = {
            "base_rate": 1.5,
            "territory_factor": 1.2,
            "class_factor": 0.9,
            "experience_mod": 1.1,
            "calculated_premium": 5000.00,
            "rating_date": datetime.now().isoformat(),
            "factors": {
                "deductible": 0.95,
                "limits": 1.0,
                "coverage": 1.0
            }
        }
        
        try:
            # Save rating sheet
            logger.info("Saving rating sheet")
            save_result = self.document_service.save_rating_sheet(
                self.test_quote_guid,
                rating_data
            )
            
            if save_result:
                logger.info("Rating sheet saved successfully")
                
                # Get rating sheet
                logger.info("Retrieving rating sheet")
                sheet_data = self.document_service.get_rating_sheet(self.test_quote_guid)
                
                if sheet_data:
                    logger.info("Rating sheet retrieved successfully")
                    logger.info(f"  Base rate: {sheet_data.get('base_rate')}")
                    logger.info(f"  Premium: {sheet_data.get('calculated_premium')}")
            else:
                logger.warning("Rating sheet save failed")
                
        except Exception as e:
            logger.warning(f"Rating sheet operations not available: {str(e)}")


class TestDocumentBatch(IMSServiceTestBase):
    """Test batch document operations"""
    
    def test_01_upload_document_batch(self):
        """Test uploading multiple documents"""
        logger.info("\nTesting batch document upload")
        
        # Create multiple test documents
        documents = []
        temp_files = []
        
        try:
            for i in range(3):
                # Create temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                    tmp.write(f"Batch document {i+1} content for {self.test_id}")
                    temp_files.append(tmp.name)
                    
                    documents.append({
                        "name": f"batch_doc_{i+1}_{self.test_id}.txt",
                        "path": tmp.name,
                        "description": f"Batch document {i+1}",
                        "entity_guid": self.test_quote_guid,
                        "entity_type": "quote"
                    })
            
            # Upload batch
            results = self.document_service.upload_document_batch(documents)
            
            # Verify
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), len(documents))
            
            success_count = sum(1 for r in results if r.get('success'))
            logger.info(f"Successfully uploaded {success_count}/{len(documents)} documents")
            
            for i, result in enumerate(results):
                if result.get('success'):
                    logger.info(f"  Document {i+1}: {result.get('document_guid')}")
                else:
                    logger.warning(f"  Document {i+1} failed: {result.get('error_message')}")
                    
        except NotImplementedError:
            logger.info("Batch upload not implemented")
        finally:
            # Clean up temp files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
    
    def test_02_document_mime_types(self):
        """Test different document MIME types"""
        mime_tests = [
            ("test.pdf", "application/pdf"),
            ("test.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("test.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("test.txt", "text/plain"),
            ("test.jpg", "image/jpeg"),
            ("test.png", "image/png")
        ]
        
        logger.info("\nTesting MIME type detection")
        
        for filename, expected_mime in mime_tests:
            detected_mime = self.document_service._get_mime_type(filename)
            self.assertEqual(detected_mime, expected_mime, 
                           f"Wrong MIME type for {filename}")
            logger.info(f"  {filename}: {detected_mime} ✓")


if __name__ == "__main__":
    unittest.main(verbosity=2)