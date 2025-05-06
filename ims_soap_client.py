"""
IMS SOAP Client - Handles XML request/response processing for IMS web services
"""
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging

class IMSSoapClient:
    def __init__(self, ims_integration):
        """Initialize the SOAP client with a reference to the IMS integration"""
        self.ims = ims_integration
        self.logger = self.ims.logger
        self.token = None
        self.user_guid = None
        
    def login(self):
        """Login to IMS and get an authentication token"""
        self.logger.info(f"Logging in to IMS as {self.ims.username}")
        
        # Prepare SOAP request
        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <LoginIMSUser xmlns="http://tempuri.org/IMSWebServices/Logon">
      <userName>{self.ims.username}</userName>
      <tripleDESEncryptedPassword>{self.ims.password}</tripleDESEncryptedPassword>
    </LoginIMSUser>
  </soap:Body>
</soap:Envelope>"""
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'http://tempuri.org/IMSWebServices/Logon/LoginIMSUser'
        }
        
        try:
            response = requests.post(self.ims.urls.get('logon'), data=soap_envelope, headers=headers)
            
            if response.status_code == 200:
                # Parse the response XML to extract token and user GUID
                root = ET.fromstring(response.content)
                
                # Define namespaces for XPath queries
                namespaces = {
                    'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                    'ims': 'http://tempuri.org/IMSWebServices/Logon'
                }
                
                # Extract token and user GUID
                result_node = root.find('.//ims:LoginIMSUserResult', namespaces)
                if result_node is not None:
                    token_node = result_node.find('ims:Token', namespaces)
                    user_guid_node = result_node.find('ims:UserGuid', namespaces)
                    
                    if token_node is not None and user_guid_node is not None:
                        self.token = token_node.text
                        self.user_guid = user_guid_node.text
                        self.logger.info("Login successful")
                        return True
                
                self.logger.error("Failed to extract token from login response")
                return False
            else:
                self.logger.error(f"Login failed with status code {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during login: {e}")
            return False
    
    def add_quote_with_submission(self, submission_data):
        """
        Call the AddQuoteWithSubmission API to create a submission and quote in IMS
        
        Args:
            submission_data: Dictionary containing submission and quote data
            
        Returns:
            String: GUID of the created quote, or None if the operation failed
        """
        if not self.token:
            self.logger.error("Not authenticated. Call login() first.")
            return None
            
        self.logger.info("Adding quote with submission")
        
        # Build the SOAP envelope
        soap_envelope = self._build_add_quote_with_submission_envelope(submission_data)
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'http://tempuri.org/IMSWebServices/QuoteFunctions/AddQuoteWithSubmission'
        }
        
        try:
            # The correct URL needs to be determined based on the IMS configuration
            quote_functions_url = self.ims.urls.get('logon').replace('logon.asmx', 'quotefunctions.asmx')
            
            response = requests.post(quote_functions_url, data=soap_envelope, headers=headers)
            
            if response.status_code == 200:
                # Parse the response XML to extract the quote GUID
                root = ET.fromstring(response.content)
                
                # Define namespaces for XPath queries
                namespaces = {
                    'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                    'ims': 'http://tempuri.org/IMSWebServices/QuoteFunctions'
                }
                
                # Extract the quote GUID
                result_node = root.find('.//ims:AddQuoteWithSubmissionResult', namespaces)
                if result_node is not None:
                    quote_guid = result_node.text
                    self.logger.info(f"Created quote with GUID: {quote_guid}")
                    return quote_guid
                
                self.logger.error("Failed to extract quote GUID from response")
                return None
            else:
                self.logger.error(f"Add quote with submission failed with status code {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error during add quote with submission: {e}")
            return None
    
    def _build_add_quote_with_submission_envelope(self, data):
        """
        Build the SOAP envelope for the AddQuoteWithSubmission API call
        
        Args:
            data: Dictionary containing submission and quote data
            
        Returns:
            String: SOAP envelope XML
        """
        # Create the root elements
        envelope = ET.Element('soap:Envelope')
        envelope.set('xmlns:soap', 'http://schemas.xmlsoap.org/soap/envelope/')
        envelope.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        envelope.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
        
        header = ET.SubElement(envelope, 'soap:Header')
        token_header = ET.SubElement(header, 'TokenHeader')
        token_header.set('xmlns', 'http://tempuri.org/IMSWebServices/QuoteFunctions')
        
        token_element = ET.SubElement(token_header, 'Token')
        token_element.text = self.token
        
        context_element = ET.SubElement(token_header, 'Context')
        context_element.text = ''
        
        body = ET.SubElement(envelope, 'soap:Body')
        add_quote = ET.SubElement(body, 'AddQuoteWithSubmission')
        add_quote.set('xmlns', 'http://tempuri.org/IMSWebServices/QuoteFunctions')
        
        # Add submission element
        submission_element = ET.SubElement(add_quote, 'submission')
        self._add_submission_elements(submission_element, data['submission'])
        
        # Add quote element
        quote_element = ET.SubElement(add_quote, 'quote')
        self._add_quote_elements(quote_element, data['quote'])
        
        # Convert to string with pretty formatting
        xml_str = ET.tostring(envelope, encoding='utf-8')
        dom = minidom.parseString(xml_str)
        pretty_xml_str = dom.toprettyxml(indent="  ")
        
        # Remove the XML declaration that minidom adds, as we'll add our own
        if pretty_xml_str.startswith('<?xml'):
            pretty_xml_str = pretty_xml_str.split('\n', 1)[1]
        
        # Add our XML declaration
        return f'<?xml version="1.0" encoding="utf-8"?>\n{pretty_xml_str}'
    
    def _add_submission_elements(self, parent, submission_data):
        """Add submission child elements to the parent element"""
        for key, value in submission_data.items():
            element = ET.SubElement(parent, key)
            if value is not None:
                element.text = str(value)
    
    def _add_quote_elements(self, parent, quote_data):
        """Add quote child elements to the parent element"""
        for key, value in quote_data.items():
            if key == 'QuoteDetail':
                # QuoteDetail is a sub-object
                quote_detail = ET.SubElement(parent, key)
                for detail_key, detail_value in value.items():
                    detail_element = ET.SubElement(quote_detail, detail_key)
                    if detail_value is not None:
                        detail_element.text = str(detail_value)
            elif key == 'RiskInformation':
                # RiskInformation is a sub-object
                risk_info = ET.SubElement(parent, key)
                for risk_key, risk_value in value.items():
                    risk_element = ET.SubElement(risk_info, risk_key)
                    if risk_value is not None:
                        risk_element.text = str(risk_value)
            else:
                # Regular element
                element = ET.SubElement(parent, key)
                if value is not None:
                    element.text = str(value) 