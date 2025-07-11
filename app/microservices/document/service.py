"""
Document Microservice Implementation
"""

import os
import base64
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.microservices.core import (
    BaseMicroservice, 
    ServiceConfig, 
    ServiceResponse,
    ServiceError
)
from app.microservices.core.exceptions import ValidationError
from .models import (
    Document,
    DocumentCreate,
    DocumentType,
    DocumentStatus,
    DocumentSearch,
    GenerateDocumentRequest,
    GenerateDocumentResponse,
    UploadDocumentRequest,
    UploadDocumentResponse
)


class DocumentService(BaseMicroservice):
    """
    Microservice for managing documents in IMS
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        if not config:
            config = ServiceConfig(
                name="document",
                version="1.0.0"
            )
        super().__init__(config)
    
    def _on_initialize(self):
        """Service-specific initialization"""
        self.logger.info("Document service specific initialization")
    
    def _on_shutdown(self):
        """Service-specific shutdown"""
        self.logger.info("Document service specific shutdown")
    
    async def generate_document(self, request: GenerateDocumentRequest) -> ServiceResponse:
        """
        Generate a document based on type and data
        
        Args:
            request: Document generation request
            
        Returns:
            ServiceResponse with GenerateDocumentResponse
        """
        self._log_operation("generate_document", {
            "document_type": request.document_type.value,
            "format": request.format
        })
        
        try:
            # Route based on document type
            if request.document_type == DocumentType.QUOTE:
                return await self._generate_quote_document(request)
            elif request.document_type == DocumentType.BINDER:
                return await self._generate_binder_document(request)
            elif request.document_type == DocumentType.POLICY:
                return await self._generate_policy_document(request)
            elif request.document_type == DocumentType.CERTIFICATE:
                return await self._generate_certificate(request)
            else:
                return ServiceResponse(
                    success=False,
                    error=f"Document type {request.document_type} generation not implemented"
                )
                
        except Exception as e:
            return self._handle_error(e, "generate_document")
    
    async def _generate_quote_document(self, request: GenerateDocumentRequest) -> ServiceResponse:
        """Generate quote document"""
        try:
            if not request.quote_guid:
                raise ValidationError("Quote GUID is required for quote documents")
            
            # Call IMS to generate quote document
            if request.format.upper() == "PDF":
                result = self.soap_client.service.CreateQuoteDocument(
                    QuoteGuid=request.quote_guid,
                    TemplateName=request.template_name or "DefaultQuoteTemplate"
                )
            else:
                # Other formats not implemented in this example
                raise ServiceError(f"Format {request.format} not supported for quotes")
            
            if not result:
                raise ServiceError("Failed to generate quote document")
            
            response = GenerateDocumentResponse(
                success=True,
                document_guid=str(result.get("DocumentGUID", "")),
                document_path=result.get("FilePath", ""),
                document_url=result.get("DocumentURL", "")
            )
            
            # Handle email sending if requested
            if request.send_to_insured or request.send_to_agent:
                # This would integrate with email service
                response.warnings.append("Email sending not implemented")
            
            return ServiceResponse(
                success=True,
                data=response
            )
            
        except Exception as e:
            return self._handle_error(e, "_generate_quote_document")
    
    async def _generate_binder_document(self, request: GenerateDocumentRequest) -> ServiceResponse:
        """Generate binder document"""
        try:
            if not request.policy_number:
                raise ValidationError("Policy number is required for binder documents")
            
            # Call IMS to generate binder
            result = self.soap_client.service.CreateBinderDocument(
                PolicyNumber=request.policy_number,
                IncludeForms=request.include_forms
            )
            
            if not result:
                raise ServiceError("Failed to generate binder document")
            
            response = GenerateDocumentResponse(
                success=True,
                document_guid=str(result.get("DocumentGUID", "")),
                document_path=result.get("FilePath", "")
            )
            
            return ServiceResponse(
                success=True,
                data=response
            )
            
        except Exception as e:
            return self._handle_error(e, "_generate_binder_document")
    
    async def _generate_policy_document(self, request: GenerateDocumentRequest) -> ServiceResponse:
        """Generate policy document"""
        try:
            if not request.policy_number:
                raise ValidationError("Policy number is required for policy documents")
            
            # Call IMS to generate policy document
            result = self.soap_client.service.CreatePolicyDocument(
                PolicyNumber=request.policy_number,
                IncludeForms=request.include_forms,
                TemplateName=request.template_name or "DefaultPolicyTemplate"
            )
            
            if not result:
                raise ServiceError("Failed to generate policy document")
            
            response = GenerateDocumentResponse(
                success=True,
                document_guid=str(result.get("DocumentGUID", "")),
                document_path=result.get("FilePath", "")
            )
            
            return ServiceResponse(
                success=True,
                data=response
            )
            
        except Exception as e:
            return self._handle_error(e, "_generate_policy_document")
    
    async def _generate_certificate(self, request: GenerateDocumentRequest) -> ServiceResponse:
        """Generate certificate of insurance"""
        try:
            if not request.policy_number:
                raise ValidationError("Policy number is required for certificates")
            
            # Certificates often require custom data
            cert_data = request.custom_data or {}
            
            # This would call a certificate-specific service
            # For now, return not implemented
            return ServiceResponse(
                success=False,
                error="Certificate generation not yet implemented"
            )
            
        except Exception as e:
            return self._handle_error(e, "_generate_certificate")
    
    async def upload_document(self, request: UploadDocumentRequest) -> ServiceResponse:
        """
        Upload a document to IMS
        
        Args:
            request: Document upload request
            
        Returns:
            ServiceResponse with UploadDocumentResponse
        """
        self._log_operation("upload_document", {
            "document_name": request.document_name,
            "document_type": request.document_type.value
        })
        
        try:
            # Validate that at least one entity is provided
            if not any([request.policy_number, request.quote_guid, request.insured_guid]):
                raise ValidationError("At least one entity (policy, quote, or insured) must be specified")
            
            # Prepare document data
            doc_data = {
                "DocumentName": request.document_name,
                "DocumentType": request.document_type.value,
                "FileName": request.file_name,
                "FileContent": base64.b64encode(request.file_content).decode('utf-8'),
                "MimeType": request.mime_type,
                "Description": request.description or "",
                "Tags": ",".join(request.tags) if request.tags else ""
            }
            
            # Call appropriate IMS method based on entity type
            if request.policy_number:
                result = self.soap_client.service.InsertTypedDocumentAssociatedToPolicy(
                    PolicyNumber=request.policy_number,
                    **doc_data
                )
            elif request.quote_guid:
                result = self.soap_client.service.InsertAssociatedDocument(
                    QuoteGuid=request.quote_guid,
                    **doc_data
                )
            else:
                # For insured-only documents
                result = self.soap_client.service.InsertStandardDocument(
                    InsuredGuid=request.insured_guid,
                    **doc_data
                )
            
            if not result:
                raise ServiceError("Failed to upload document")
            
            response = UploadDocumentResponse(
                success=True,
                document_guid=str(result.get("DocumentGUID", "")),
                file_path=result.get("FilePath", "")
            )
            
            # Handle notifications if requested
            if request.notify:
                # This would integrate with notification service
                response.notifications_sent = 0
            
            return ServiceResponse(
                success=True,
                data=response,
                metadata={"action": "uploaded"}
            )
            
        except Exception as e:
            return self._handle_error(e, "upload_document")
    
    async def get_document(self, document_guid: str) -> ServiceResponse:
        """
        Get document by GUID
        
        Args:
            document_guid: Document GUID
            
        Returns:
            ServiceResponse with Document
        """
        self._log_operation("get_document", {"document_guid": document_guid})
        
        try:
            # Get document from IMS
            result = self.soap_client.service.GetDocumentFromStore(
                DocumentGUID=document_guid
            )
            
            if not result:
                return ServiceResponse(
                    success=False,
                    error=f"Document not found: {document_guid}"
                )
            
            document = self._map_ims_to_document(result)
            
            return ServiceResponse(
                success=True,
                data=document
            )
            
        except Exception as e:
            return self._handle_error(e, "get_document")
    
    async def get_policy_documents(self, policy_number: str) -> ServiceResponse:
        """
        Get all documents for a policy
        
        Args:
            policy_number: Policy number
            
        Returns:
            ServiceResponse with list of documents
        """
        self._log_operation("get_policy_documents", {"policy_number": policy_number})
        
        try:
            # Get document list from IMS
            result = self.soap_client.service.GetPolicyDocumentsList(
                PolicyNumber=policy_number
            )
            
            documents = []
            if result and hasattr(result, 'Documents'):
                for doc in result.Documents:
                    documents.append(self._map_ims_to_document(doc))
            
            return ServiceResponse(
                success=True,
                data=documents,
                metadata={"count": len(documents)}
            )
            
        except Exception as e:
            return self._handle_error(e, "get_policy_documents")
    
    async def apply_policy_forms(self, policy_number: str, state: Optional[str] = None) -> ServiceResponse:
        """
        Apply standard policy forms to a policy
        
        Args:
            policy_number: Policy number
            state: State code (optional, uses policy state if not provided)
            
        Returns:
            ServiceResponse indicating success
        """
        self._log_operation("apply_policy_forms", {
            "policy_number": policy_number,
            "state": state
        })
        
        try:
            # Apply policy forms
            if state:
                result = self.soap_client.service.ApplyPolicyForms(
                    PolicyNumber=policy_number,
                    State=state
                )
            else:
                # Use policy's state
                result = self.soap_client.service.ApplyPolicyForms(
                    PolicyNumber=policy_number
                )
            
            if result:
                return ServiceResponse(
                    success=True,
                    data={"forms_applied": True},
                    metadata={
                        "policy_number": policy_number,
                        "forms_count": result.get("FormsCount", 0)
                    }
                )
            else:
                return ServiceResponse(
                    success=False,
                    error="Failed to apply policy forms"
                )
                
        except Exception as e:
            return self._handle_error(e, "apply_policy_forms")
    
    def _map_ims_to_document(self, ims_doc: Any) -> Document:
        """Map IMS document object to our model"""
        return Document(
            document_guid=str(ims_doc.DocumentGUID),
            document_id=getattr(ims_doc, 'DocumentID', None),
            document_name=ims_doc.DocumentName,
            document_type=DocumentType(ims_doc.DocumentType),
            status=DocumentStatus(getattr(ims_doc, 'Status', 'Approved')),
            policy_number=getattr(ims_doc, 'PolicyNumber', None),
            quote_guid=str(getattr(ims_doc, 'QuoteGUID', '')) or None,
            insured_guid=str(getattr(ims_doc, 'InsuredGUID', '')) or None,
            file_path=getattr(ims_doc, 'FilePath', None),
            file_size=getattr(ims_doc, 'FileSize', None),
            mime_type=getattr(ims_doc, 'MimeType', None),
            description=getattr(ims_doc, 'Description', None),
            version=getattr(ims_doc, 'Version', 1),
            created_date=getattr(ims_doc, 'CreatedDate', datetime.now()),
            created_by=getattr(ims_doc, 'CreatedBy', None)
        )