"""
IMS Document Service

This service handles all document-related operations in IMS including:
- Creating policy documents
- Managing document templates
- Retrieving documents
- Managing rating sheets
"""

import logging
from typing import Dict, Any, Optional, List
import base64

from app.services.ims.base_service import BaseIMSService

logger = logging.getLogger(__name__)


class IMSDocumentService(BaseIMSService):
    """Service for managing documents in IMS"""
    
    def create_policy_document(self, policy_guid: str, document_type: str = "Policy") -> Dict[str, Any]:
        """
        Create a policy document
        
        Args:
            policy_guid: The policy's GUID
            document_type: The type of document to create
            
        Returns:
            Dictionary with document creation result
        """
        self._log_operation("create_policy_document", {
            "policy_guid": policy_guid,
            "document_type": document_type
        })
        
        body_content = f"""
        <CreatePolicyDocument xmlns="http://tempuri.org/IMSWebServices/DocumentFunctions">
            <policyGuid>{policy_guid}</policyGuid>
            <documentType>{document_type}</documentType>
        </CreatePolicyDocument>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.document_functions_url,
                "http://tempuri.org/IMSWebServices/DocumentFunctions/CreatePolicyDocument",
                body_content
            )
            
            if response and 'soap:Body' in response:
                create_response = response['soap:Body'].get('CreatePolicyDocumentResponse', {})
                result = create_response.get('CreatePolicyDocumentResult', {})
                
                if result:
                    logger.info(f"Created policy document for {policy_guid}")
                    return result
            
            return {"success": False, "error": "No result returned"}
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "create_policy_document")
                # Retry once
                return self.create_policy_document(policy_guid, document_type)
            raise
    
    def create_quote_document(self, quote_guid: str, quote_option_id: int, 
                            document_type: str = "Quote") -> Dict[str, Any]:
        """
        Create a quote document
        
        Args:
            quote_guid: The quote's GUID
            quote_option_id: The quote option ID
            document_type: The type of document to create
            
        Returns:
            Dictionary with document creation result
        """
        self._log_operation("create_quote_document", {
            "quote_guid": quote_guid,
            "quote_option_id": quote_option_id,
            "document_type": document_type
        })
        
        body_content = f"""
        <CreateQuoteDocument xmlns="http://tempuri.org/IMSWebServices/DocumentFunctions">
            <quoteGuid>{quote_guid}</quoteGuid>
            <quoteOptionId>{quote_option_id}</quoteOptionId>
            <documentType>{document_type}</documentType>
        </CreateQuoteDocument>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.document_functions_url,
                "http://tempuri.org/IMSWebServices/DocumentFunctions/CreateQuoteDocument",
                body_content
            )
            
            if response and 'soap:Body' in response:
                create_response = response['soap:Body'].get('CreateQuoteDocumentResponse', {})
                result = create_response.get('CreateQuoteDocumentResult', {})
                
                if result:
                    logger.info(f"Created quote document for {quote_guid}")
                    return result
            
            return {"success": False, "error": "No result returned"}
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "create_quote_document")
                # Retry once
                return self.create_quote_document(quote_guid, quote_option_id, document_type)
            raise
    
    def get_rating_sheet(self, quote_guid: str, quote_option_id: int) -> Dict[str, Any]:
        """
        Get the rating sheet for a quote
        
        Args:
            quote_guid: The quote's GUID
            quote_option_id: The quote option ID
            
        Returns:
            Dictionary containing rating sheet data
        """
        self._log_operation("get_rating_sheet", {
            "quote_guid": quote_guid,
            "quote_option_id": quote_option_id
        })
        
        body_content = f"""
        <GetRatingSheet xmlns="http://tempuri.org/IMSWebServices/DocumentFunctions">
            <quoteGuid>{quote_guid}</quoteGuid>
            <quoteOptionId>{quote_option_id}</quoteOptionId>
        </GetRatingSheet>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.document_functions_url,
                "http://tempuri.org/IMSWebServices/DocumentFunctions/GetRatingSheet",
                body_content
            )
            
            if response and 'soap:Body' in response:
                sheet_response = response['soap:Body'].get('GetRatingSheetResponse', {})
                rating_sheet = sheet_response.get('GetRatingSheetResult', {})
                
                if rating_sheet:
                    logger.info(f"Retrieved rating sheet for quote {quote_guid}")
                    return rating_sheet
            
            return {}
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "get_rating_sheet")
                # Retry once
                return self.get_rating_sheet(quote_guid, quote_option_id)
            raise
    
    def insert_associated_document(self, entity_guid: str, entity_type: str,
                                 file_data: bytes, file_name: str,
                                 description: str = "") -> bool:
        """
        Insert a document associated with an entity (policy, quote, etc.)
        
        Args:
            entity_guid: The entity's GUID
            entity_type: The type of entity (Policy, Quote, Insured, etc.)
            file_data: The file data as bytes
            file_name: The name of the file
            description: Optional description
            
        Returns:
            True if successful
        """
        self._log_operation("insert_associated_document", {
            "entity_guid": entity_guid,
            "entity_type": entity_type,
            "file_name": file_name
        })
        
        # Encode file data to base64
        file_bytes_b64 = base64.b64encode(file_data).decode("utf-8")
        
        body_content = f"""
        <InsertAssociatedDocument xmlns="http://tempuri.org/IMSWebServices/DocumentFunctions">
            <entityGuid>{entity_guid}</entityGuid>
            <entityType>{entity_type}</entityType>
            <fileBytes>{file_bytes_b64}</fileBytes>
            <fileName>{file_name}</fileName>
            <description>{description}</description>
        </InsertAssociatedDocument>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.document_functions_url,
                "http://tempuri.org/IMSWebServices/DocumentFunctions/InsertAssociatedDocument",
                body_content
            )
            
            if response and 'soap:Body' in response:
                insert_response = response['soap:Body'].get('InsertAssociatedDocumentResponse', {})
                result = insert_response.get('InsertAssociatedDocumentResult', False)
                
                if result:
                    logger.info(f"Inserted document {file_name} for {entity_type} {entity_guid}")
                else:
                    logger.error(f"Failed to insert document {file_name}")
                    
                return result
            
            return False
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "insert_associated_document")
                # Retry once
                return self.insert_associated_document(entity_guid, entity_type,
                                                      file_data, file_name, description)
            raise
    
    def get_policy_documents_list(self, policy_guid: str) -> List[Dict[str, Any]]:
        """
        Get list of documents associated with a policy
        
        Args:
            policy_guid: The policy's GUID
            
        Returns:
            List of document information dictionaries
        """
        self._log_operation("get_policy_documents_list", {"policy_guid": policy_guid})
        
        body_content = f"""
        <GetPolicyDocumentsList xmlns="http://tempuri.org/IMSWebServices/DocumentFunctions">
            <policyGuid>{policy_guid}</policyGuid>
        </GetPolicyDocumentsList>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.document_functions_url,
                "http://tempuri.org/IMSWebServices/DocumentFunctions/GetPolicyDocumentsList",
                body_content
            )
            
            if response and 'soap:Body' in response:
                list_response = response['soap:Body'].get('GetPolicyDocumentsListResponse', {})
                documents_result = list_response.get('GetPolicyDocumentsListResult', {})
                
                if documents_result:
                    documents = documents_result.get('Document', [])
                    
                    # Convert to list if single item
                    if not isinstance(documents, list):
                        documents = [documents]
                    
                    logger.info(f"Found {len(documents)} documents for policy {policy_guid}")
                    return documents
            
            return []
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "get_policy_documents_list")
                # Retry once
                return self.get_policy_documents_list(policy_guid)
            raise
    
    def get_document_from_store(self, document_guid: str) -> Optional[bytes]:
        """
        Retrieve a document from the document store
        
        Args:
            document_guid: The document's GUID
            
        Returns:
            The document data as bytes, or None if not found
        """
        self._log_operation("get_document_from_store", {"document_guid": document_guid})
        
        body_content = f"""
        <GetDocumentFromStore xmlns="http://tempuri.org/IMSWebServices/DocumentFunctions">
            <documentGuid>{document_guid}</documentGuid>
        </GetDocumentFromStore>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.document_functions_url,
                "http://tempuri.org/IMSWebServices/DocumentFunctions/GetDocumentFromStore",
                body_content
            )
            
            if response and 'soap:Body' in response:
                doc_response = response['soap:Body'].get('GetDocumentFromStoreResponse', {})
                doc_data_b64 = doc_response.get('GetDocumentFromStoreResult')
                
                if doc_data_b64:
                    # Decode from base64
                    doc_data = base64.b64decode(doc_data_b64)
                    logger.info(f"Retrieved document {document_guid}, size: {len(doc_data)} bytes")
                    return doc_data
            
            logger.warning(f"Document {document_guid} not found")
            return None
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "get_document_from_store")
                # Retry once
                return self.get_document_from_store(document_guid)
            raise