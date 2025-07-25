import requests
import logging
import xml.etree.ElementTree as ET
import xmltodict
import os
import re
from app.core.config import settings

logger = logging.getLogger(__name__)

class IMSSoapClient:
    def __init__(self, config_file):
        self.config_file = config_file
        self._load_config()
        self.token = None
        self.namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsd': 'http://www.w3.org/2001/XMLSchema'
        }
        
    def _load_config(self):
        """Load IMS configuration from config file"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "IMS_Configs", self.config_file)
            tree = ET.parse(config_path)
            root = tree.getroot()
            
            # Extract URLs from app settings
            settings_dict = {}
            for setting in root.findall(".//add"):
                key = setting.get('key')
                value = setting.get('value')
                settings_dict[key] = value
            
            self.logon_url = settings_dict.get("WebServicesLogonUrl")
            self.document_functions_url = settings_dict.get("WebServicesDocumentsUrl")
            self.invoicing_url = settings_dict.get("WebServicesInvoicingUrl")
            
            # Construct other URLs based on pattern from known URLs
            base_path = re.match(r'(.*?)/(.*?)\.asmx', self.logon_url)
            if base_path:
                base_url = base_path.group(1)
                self.insured_functions_url = f"{base_url}/InsuredFunctions.asmx"
                self.quote_functions_url = f"{base_url}/QuoteFunctions.asmx"
                self.data_access_url = f"{base_url}/DataAccess.asmx"
                self.clearance_url = f"{base_url}/Clearance.asmx"
                self.producer_functions_url = f"{base_url}/ProducerFunctions.asmx"
            else:
                raise ValueError(f"Could not parse base URL from {self.logon_url}")
                
            logger.info(f"Loaded IMS configuration from {config_path}")
            logger.info(f"  Logon URL: {self.logon_url}")
            logger.info(f"  Quote Functions URL: {self.quote_functions_url}")
            logger.info(f"  Insured Functions URL: {self.insured_functions_url}")
            
        except Exception as e:
            logger.error(f"Error loading IMS configuration: {str(e)}")
            # Fallback to default URLs
            base_url = "http://10.64.32.234/ims_one"
            self.logon_url = f"{base_url}/logon.asmx"
            self.data_access_url = f"{base_url}/DataAccess.asmx"
            self.clearance_url = f"{base_url}/Clearance.asmx"
            self.insured_functions_url = f"{base_url}/InsuredFunctions.asmx"
            self.quote_functions_url = f"{base_url}/QuoteFunctions.asmx"
            self.document_functions_url = f"{base_url}/DocumentFunctions.asmx"
            self.producer_functions_url = f"{base_url}/ProducerFunctions.asmx"
            self.invoicing_url = f"{base_url}/InvoiceFactory.asmx"
        
    def _create_soap_envelope(self, body_content, include_token=False):
        """Create a SOAP envelope with the specified body content"""
        token_header = ""
        if include_token and self.token:
            # Extract namespace from body_content
            namespace_match = re.search(r'xmlns="(.*?)"', body_content)
            namespace = namespace_match.group(1) if namespace_match else "http://tempuri.org/"
            token_header = f"""
            <soap:Header>
                <TokenHeader xmlns="{namespace}">
                    <Token>{self.token}</Token>
                </TokenHeader>
            </soap:Header>
            """
            
        return f"""<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            {token_header}
            <soap:Body>
                {body_content}
            </soap:Body>
        </soap:Envelope>
        """
    
    def _make_soap_request(self, url, action, body_content, include_token=True):
        """Make a SOAP request to the specified URL"""
        envelope = self._create_soap_envelope(body_content, include_token)
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': action
        }
        
        # Always log SOAP requests in INFO level for debugging
        logger.info(f"Sending SOAP request to {url}")
        logger.info(f"SOAP Action: {action}")
        logger.info(f"SOAP Request Body:\n{envelope}")
        
        try:
            response = requests.post(url, data=envelope, headers=headers)
            response.raise_for_status()
            
            logger.debug(f"Received response: {response.status_code}")
            logger.debug(f"Response body: {response.text}")
            
            # Parse response XML
            root = ET.fromstring(response.text)
            
            # Return the body content
            body = root.find('.//soap:Body', namespaces=self.namespaces)
            if body is not None:
                # Convert to dict for easier handling
                body_dict = xmltodict.parse(ET.tostring(body, encoding='unicode'))
                return body_dict
            
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making SOAP request to {url}: {str(e)}")
            logger.error(f"SOAP Action: {action}")
            logger.error("Full SOAP Request:")
            logger.error(envelope)
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text[:1000]}")  # First 1000 chars
            raise
        except ET.ParseError as e:
            logger.error(f"Error parsing SOAP response: {str(e)}")
            logger.error(f"Response text: {response.text}")
            logger.error("Full SOAP Request that caused the error:")
            logger.error(envelope)
            # Check if it's a SOAP fault
            if 'soap:Fault' in response.text or 'faultstring' in response.text:
                logger.error("SOAP Fault detected in response")
            raise
    
    def login(self, username, password):
        """Login to IMS and get token"""
        logger.info(f"Logging in to IMS with username {username}")
        
        body_content = f"""
        <LoginIMSUser xmlns="http://tempuri.org/IMSWebServices/Logon">
            <userName>{username}</userName>
            <tripleDESEncryptedPassword>{password}</tripleDESEncryptedPassword>
        </LoginIMSUser>
        """
        
        try:
            response = self._make_soap_request(
                self.logon_url,
                "http://tempuri.org/IMSWebServices/Logon/LoginIMSUser",
                body_content,
                include_token=False
            )
            
            # Extract token from response
            if response and 'soap:Body' in response:
                login_response = response['soap:Body'].get('LoginIMSUserResponse', {})
                login_result = login_response.get('LoginIMSUserResult', {})
                
                token = login_result.get('Token')
                user_guid = login_result.get('UserGuid')
                
                if token:
                    self.token = token
                    logger.info(f"Successfully logged in, received token for user {user_guid}")
                    return token
                else:
                    error_message = login_result.get('ErrorMessage', 'Unknown error')
                    logger.error(f"Login failed: {error_message}")
                    raise ValueError(f"Login failed: {error_message}")
            
            logger.error("Login failed: Unexpected response format")
            raise ValueError("Login failed: Unexpected response format")
            
        except Exception as e:
            logger.error(f"Error logging in to IMS: {str(e)}")
            raise
    
    def find_insured_by_name(self, name, tax_id=None):
        """Find insured by name"""
        logger.info(f"Finding insured by name: {name}")
        
        body_content = f"""
        <FindInsuredByName xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
            <partialName>{name}</partialName>
        </FindInsuredByName>
        """
        
        try:
            response = self._make_soap_request(
                self.insured_functions_url,
                "http://tempuri.org/IMSWebServices/InsuredFunctions/FindInsuredByName",
                body_content
            )
            
            # Extract results from response
            if response and 'soap:Body' in response:
                find_response = response['soap:Body'].get('FindInsuredByNameResponse', {})
                find_result = find_response.get('FindInsuredByNameResult', {})
                
                if isinstance(find_result, dict) and 'Insureds' in find_result:
                    insureds = find_result['Insureds'].get('LookupInsured', [])
                    
                    # Convert to list if it's a single item
                    if not isinstance(insureds, list):
                        insureds = [insureds]
                    
                    # If tax_id is provided, filter by it
                    if tax_id:
                        for insured in insureds:
                            if insured.get('TaxID') == tax_id:
                                return insured.get('InsuredGUID')
                    
                    # Otherwise return the first match
                    if insureds:
                        return insureds[0].get('InsuredGUID')
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding insured by name: {str(e)}")
            raise
    
    def add_insured(self, insured_data):
        """Add a new insured"""
        logger.info(f"Adding insured: {insured_data.get('name')}")
        
        # Extract insured fields
        name = insured_data.get('name', '')
        tax_id = insured_data.get('tax_id', '')
        business_type_id = insured_data.get('business_type_id', 1)  # Default to 1 (Corporation)
        
        # Determine if this is an individual or corporation
        is_individual = business_type_id in [3, 4]  # Individual, Sole Proprietor
        
        # For individuals, split name into first/last
        first_name = last_name = ""
        corporation_name = ""
        
        if is_individual:
            name_parts = name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
        else:
            corporation_name = name
        
        # Get office GUID from insured_data or use default
        office_guid = insured_data.get('office_guid', '00000000-0000-0000-0000-000000000000')
        
        body_content = f"""
        <AddInsured xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
            <insured>
                <BusinessTypeID>{business_type_id}</BusinessTypeID>
                <FirstName>{first_name}</FirstName>
                <LastName>{last_name}</LastName>
                <CorporationName>{corporation_name}</CorporationName>
                <NameOnPolicy>{name}</NameOnPolicy>
                <FEIN>{tax_id if not is_individual else ""}</FEIN>
                <SSN>{tax_id if is_individual else ""}</SSN>
                <Office>{office_guid}</Office>
            </insured>
        </AddInsured>
        """
        
        try:
            response = self._make_soap_request(
                self.insured_functions_url,
                "http://tempuri.org/IMSWebServices/InsuredFunctions/AddInsured",
                body_content
            )
            
            # Extract insured GUID from response
            if response and 'soap:Body' in response:
                add_response = response['soap:Body'].get('AddInsuredResponse', {})
                insured_guid = add_response.get('AddInsuredResult')
                
                if insured_guid:
                    logger.info(f"Successfully added insured, received GUID: {insured_guid}")
                    return insured_guid
                else:
                    logger.error("Failed to add insured: No GUID returned")
                    raise ValueError("Failed to add insured: No GUID returned")
            
            logger.error("Failed to add insured: Unexpected response format")
            raise ValueError("Failed to add insured: Unexpected response format")
            
        except Exception as e:
            logger.error(f"Error adding insured: {str(e)}")
            raise
    
    def add_insured_location(self, insured_guid, location_data):
        """Add a location to an insured"""
        logger.info(f"Adding location for insured: {insured_guid}")
        
        # Extract location fields
        address = location_data.get('address', '')
        city = location_data.get('city', '')
        state = location_data.get('state', '')
        zip_code = location_data.get('zip_code', '')
        country = location_data.get('country', 'USA')
        description = location_data.get('description', '')
        
        body_content = f"""
        <AddInsuredLocation xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
            <insuredGuid>{insured_guid}</insuredGuid>
            <location>
                <Address1>{address}</Address1>
                <City>{city}</City>
                <State>{state}</State>
                <Zip>{zip_code}</Zip>
                <Country>{country}</Country>
                <Description>{description}</Description>
            </location>
        </AddInsuredLocation>
        """
        
        try:
            response = self._make_soap_request(
                self.insured_functions_url,
                "http://tempuri.org/IMSWebServices/InsuredFunctions/AddInsuredLocation",
                body_content
            )
            
            # Extract location ID from response
            if response and 'soap:Body' in response:
                add_response = response['soap:Body'].get('AddInsuredLocationResponse', {})
                location_id = add_response.get('AddInsuredLocationResult')
                
                if location_id:
                    logger.info(f"Successfully added location, received ID: {location_id}")
                    return location_id
                else:
                    logger.error("Failed to add location: No ID returned")
                    raise ValueError("Failed to add location: No ID returned")
            
            logger.error("Failed to add location: Unexpected response format")
            raise ValueError("Failed to add location: Unexpected response format")
            
        except Exception as e:
            logger.error(f"Error adding location: {str(e)}")
            raise
    
    def add_submission(self, submission_data):
        """Add a submission"""
        logger.info(f"Adding submission for insured: {submission_data.get('insured_guid')}")
        
        # Extract submission fields
        insured_guid = submission_data.get('insured_guid', '')
        producer_contact_guid = submission_data.get('producer_contact_guid', '')
        underwriter_guid = submission_data.get('underwriter_guid', '')
        submission_date = submission_data.get('submission_date', '')
        producer_location_guid = submission_data.get('producer_location_guid', '')
        
        # Format date as expected by IMS (YYYY-MM-DD)
        if hasattr(submission_date, 'isoformat'):
            submission_date = submission_date.isoformat()
        
        body_content = f"""
        <AddSubmission xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
            <submission>
                <Insured>{insured_guid}</Insured>
                <ProducerContact>{producer_contact_guid}</ProducerContact>
                <Underwriter>{underwriter_guid}</Underwriter>
                <SubmissionDate>{submission_date}</SubmissionDate>
                <ProducerLocation>{producer_location_guid}</ProducerLocation>
            </submission>
        </AddSubmission>
        """
        
        try:
            response = self._make_soap_request(
                self.quote_functions_url,
                "http://tempuri.org/IMSWebServices/QuoteFunctions/AddSubmission",
                body_content
            )
            
            # Extract submission GUID from response
            if response and 'soap:Body' in response:
                add_response = response['soap:Body'].get('AddSubmissionResponse', {})
                submission_guid = add_response.get('AddSubmissionResult')
                
                if submission_guid:
                    logger.info(f"Successfully added submission, received GUID: {submission_guid}")
                    return submission_guid
                else:
                    logger.error("Failed to add submission: No GUID returned")
                    raise ValueError("Failed to add submission: No GUID returned")
            
            logger.error("Failed to add submission: Unexpected response format")
            raise ValueError("Failed to add submission: Unexpected response format")
            
        except Exception as e:
            logger.error(f"Error adding submission: {str(e)}")
            raise
    
    def add_quote(self, quote_data):
        """Add a quote"""
        logger.info(f"Adding quote for submission: {quote_data.get('submission_guid')}")
        
        # Extract quote fields
        submission_guid = quote_data.get('submission_guid', '')
        quoting_location_guid = quote_data.get('quoting_location_guid', '')
        issuing_location_guid = quote_data.get('issuing_location_guid', '')
        company_location_guid = quote_data.get('company_location_guid', '')
        line_guid = quote_data.get('line_guid', '')
        state_id = quote_data.get('state', '')
        producer_contact_guid = quote_data.get('producer_contact_guid', '')
        quote_status_id = quote_data.get('status_id', 1)  # Default to 1 (New)
        
        # Extract dates and format as expected by IMS (YYYY-MM-DD)
        effective_date = quote_data.get('effective_date', '')
        if hasattr(effective_date, 'isoformat'):
            effective_date = effective_date.isoformat()
            
        expiration_date = quote_data.get('expiration_date', '')
        if hasattr(expiration_date, 'isoformat'):
            expiration_date = expiration_date.isoformat()
        
        billing_type_id = quote_data.get('billing_type_id', 1)  # Default to 1 (Agency Bill)
        
        # Extract QuoteDetail fields
        quote_detail = quote_data.get('quote_detail', {})
        company_commission = quote_detail.get('company_commission', 0)
        producer_commission = quote_detail.get('producer_commission', 0)
        terms_of_payment = quote_detail.get('terms_of_payment', 30)
        program_code = quote_detail.get('program_code', '')
        company_contact_guid = quote_detail.get('company_contact_guid', '')
        rater_id = quote_detail.get('rater_id', '')
        factor_set_guid = quote_detail.get('factor_set_guid', '')
        program_id = quote_detail.get('program_id', '')
        
        # Extract optional fields
        underwriter_guid = quote_data.get('underwriter_guid', '')
        policy_type_id = quote_data.get('policy_type_id', '')
        
        body_content = f"""
        <AddQuote xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
            <quote>
                <Submission>{submission_guid}</Submission>
                <QuotingLocation>{quoting_location_guid}</QuotingLocation>
                <IssuingLocation>{issuing_location_guid}</IssuingLocation>
                <CompanyLocation>{company_location_guid}</CompanyLocation>
                <Line>{line_guid}</Line>
                <StateID>{state_id}</StateID>
                <ProducerContact>{producer_contact_guid}</ProducerContact>
                <QuoteStatusID>{quote_status_id}</QuoteStatusID>
                <Effective>{effective_date}</Effective>
                <Expiration>{expiration_date}</Expiration>
                <BillingTypeID>{billing_type_id}</BillingTypeID>
                <QuoteDetail>
                    <CompanyCommission>{company_commission}</CompanyCommission>
                    <ProducerCommission>{producer_commission}</ProducerCommission>
                    <TermsOfPayment>{terms_of_payment}</TermsOfPayment>
                    <ProgramCode>{program_code}</ProgramCode>
                    <CompanyContactGuid>{company_contact_guid}</CompanyContactGuid>
                    <RaterID>{rater_id}</RaterID>
                    <FactorSetGuid>{factor_set_guid}</FactorSetGuid>
                    <ProgramID>{program_id}</ProgramID>
                    <LineGUID>{line_guid}</LineGUID>
                    <CompanyLocationGUID>{company_location_guid}</CompanyLocationGUID>
                </QuoteDetail>"""
        
        # Add optional fields if provided
        if underwriter_guid:
            body_content += f"\n                <Underwriter>{underwriter_guid}</Underwriter>"
        
        if policy_type_id:
            body_content += f"\n                <PolicyTypeID>{policy_type_id}</PolicyTypeID>"
        
        body_content += """
            </quote>
        </AddQuote>
        """
        
        try:
            response = self._make_soap_request(
                self.quote_functions_url,
                "http://tempuri.org/IMSWebServices/QuoteFunctions/AddQuote",
                body_content
            )
            
            # Extract quote GUID from response
            if response and 'soap:Body' in response:
                add_response = response['soap:Body'].get('AddQuoteResponse', {})
                quote_guid = add_response.get('AddQuoteResult')
                
                if quote_guid:
                    logger.info(f"Successfully added quote, received GUID: {quote_guid}")
                    return quote_guid
                else:
                    logger.error("Failed to add quote: No GUID returned")
                    raise ValueError("Failed to add quote: No GUID returned")
            
            logger.error("Failed to add quote: Unexpected response format")
            raise ValueError("Failed to add quote: Unexpected response format")
            
        except Exception as e:
            logger.error(f"Error adding quote: {str(e)}")
            raise
    
    def add_quote_option(self, quote_guid):
        """Add a quote option"""
        logger.info(f"Adding quote option for quote: {quote_guid}")
        
        body_content = f"""
        <AddQuoteOption xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
            <quoteGuid>{quote_guid}</quoteGuid>
        </AddQuoteOption>
        """
        
        try:
            response = self._make_soap_request(
                self.quote_functions_url,
                "http://tempuri.org/IMSWebServices/QuoteFunctions/AddQuoteOption",
                body_content
            )
            
            # Extract quote option ID from response
            if response and 'soap:Body' in response:
                add_response = response['soap:Body'].get('AddQuoteOptionResponse', {})
                option_id = add_response.get('AddQuoteOptionResult')
                
                if option_id:
                    logger.info(f"Successfully added quote option, received ID: {option_id}")
                    return option_id
                else:
                    logger.error("Failed to add quote option: No ID returned")
                    raise ValueError("Failed to add quote option: No ID returned")
            
            logger.error("Failed to add quote option: Unexpected response format")
            raise ValueError("Failed to add quote option: Unexpected response format")
            
        except Exception as e:
            logger.error(f"Error adding quote option: {str(e)}")
            raise
    
    def add_premium(self, quote_guid, option_id, premium_amount, description="Premium"):
        """Add premium to a quote option"""
        logger.info(f"Adding premium for quote: {quote_guid}, option: {option_id}")
        
        body_content = f"""
        <AddPremium xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
            <quoteGuid>{quote_guid}</quoteGuid>
            <quoteOptionID>{option_id}</quoteOptionID>
            <premium>
                <Amount>{premium_amount}</Amount>
                <Description>{description}</Description>
            </premium>
        </AddPremium>
        """
        
        try:
            response = self._make_soap_request(
                self.quote_functions_url,
                "http://tempuri.org/IMSWebServices/QuoteFunctions/AddPremium",
                body_content
            )
            
            # Check if the operation was successful
            if response and 'soap:Body' in response:
                add_response = response['soap:Body'].get('AddPremiumResponse', {})
                result = add_response.get('AddPremiumResult')
                
                if result:
                    logger.info(f"Successfully added premium: {premium_amount}")
                    return True
                else:
                    logger.error("Failed to add premium")
                    return False
            
            logger.error("Failed to add premium: Unexpected response format")
            return False
            
        except Exception as e:
            logger.error(f"Error adding premium: {str(e)}")
            raise
    
    def import_excel_rater(self, quote_guid, file_bytes, file_name, rater_id, factor_set_guid, apply_fees=True):
        """Import Excel rater for a quote"""
        logger.info(f"Importing Excel rater for quote: {quote_guid}")
        
        body_content = f"""
        <ImportExcelRater xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
            <QuoteGuid>{quote_guid}</QuoteGuid>
            <FileBytes>{file_bytes}</FileBytes>
            <FileName>{file_name}</FileName>
            <RaterID>{rater_id}</RaterID>
            <FactorSetGuid>{factor_set_guid}</FactorSetGuid>
            <ApplyFees>{"true" if apply_fees else "false"}</ApplyFees>
        </ImportExcelRater>
        """
        
        try:
            response = self._make_soap_request(
                self.quote_functions_url,
                "http://tempuri.org/IMSWebServices/QuoteFunctions/ImportExcelRater",
                body_content
            )
            
            # Extract result from response
            if response and 'soap:Body' in response:
                import_response = response['soap:Body'].get('ImportExcelRaterResponse', {})
                import_result = import_response.get('ImportExcelRaterResult', {})
                
                if import_result:
                    success = import_result.get('Success', False)
                    error_message = import_result.get('ErrorMessage', '')
                    
                    if success:
                        premiums = import_result.get('Premiums', {}).get('OptionResult', [])
                        
                        # Convert to list if it's a single item
                        if not isinstance(premiums, list):
                            premiums = [premiums]
                        
                        result = {
                            'success': True,
                            'premiums': []
                        }
                        
                        for premium in premiums:
                            result['premiums'].append({
                                'quote_option_id': premium.get('QuoteOptionGuid'),
                                'premium_total': premium.get('PremiumTotal'),
                                'fee_total': premium.get('FeeTotal')
                            })
                        
                        logger.info(f"Successfully imported Excel rater: {len(result['premiums'])} premium options")
                        return result
                    else:
                        logger.error(f"Failed to import Excel rater: {error_message}")
                        return {
                            'success': False,
                            'error_message': error_message
                        }
                        
            logger.error("Failed to import Excel rater: Unexpected response format")
            return {
                'success': False,
                'error_message': 'Unexpected response format'
            }
            
        except Exception as e:
            logger.error(f"Error importing Excel rater: {str(e)}")
            raise
    
    def bind(self, quote_option_id):
        """Bind a quote"""
        logger.info(f"Binding quote option: {quote_option_id}")
        
        body_content = f"""
        <Bind xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
            <quoteOptionID>{quote_option_id}</quoteOptionID>
        </Bind>
        """
        
        try:
            response = self._make_soap_request(
                self.quote_functions_url,
                "http://tempuri.org/IMSWebServices/QuoteFunctions/Bind",
                body_content
            )
            
            # Extract policy number from response
            if response and 'soap:Body' in response:
                bind_response = response['soap:Body'].get('BindResponse', {})
                policy_number = bind_response.get('BindResult')
                
                if policy_number:
                    logger.info(f"Successfully bound quote, received policy number: {policy_number}")
                    return policy_number
                else:
                    logger.error("Failed to bind quote: No policy number returned")
                    raise ValueError("Failed to bind quote: No policy number returned")
            
            logger.error("Failed to bind quote: Unexpected response format")
            raise ValueError("Failed to bind quote: Unexpected response format")
            
        except Exception as e:
            logger.error(f"Error binding quote: {str(e)}")
            raise
    
    def issue_policy(self, policy_number):
        """Issue a policy"""
        logger.info(f"Issuing policy: {policy_number}")
        
        body_content = f"""
        <IssuePolicy xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
            <policyNumber>{policy_number}</policyNumber>
        </IssuePolicy>
        """
        
        try:
            response = self._make_soap_request(
                self.quote_functions_url,
                "http://tempuri.org/IMSWebServices/QuoteFunctions/IssuePolicy",
                body_content
            )
            
            # Check if the operation was successful
            if response and 'soap:Body' in response:
                issue_response = response['soap:Body'].get('IssuePolicyResponse', {})
                result = issue_response.get('IssuePolicyResult')
                
                if result:
                    logger.info(f"Successfully issued policy: {policy_number}")
                    return True
                else:
                    logger.error(f"Failed to issue policy: {policy_number}")
                    return False
            
            logger.error("Failed to issue policy: Unexpected response format")
            return False
            
        except Exception as e:
            logger.error(f"Error issuing policy: {str(e)}")
            raise
    
    def execute_data_set(self, query, parameters=None):
        """Execute a query via DataAccess.asmx"""
        logger.info(f"Executing query: {query}")
        
        params_xml = ""
        if parameters:
            for key, value in parameters.items():
                params_xml += f"""
                <Parameter>
                    <Name>{key}</Name>
                    <Value>{value}</Value>
                </Parameter>
                """
        
        body_content = f"""
        <ExecuteDataSet xmlns="http://tempuri.org/IMSWebServices/DataAccess">
            <query>{query}</query>
            <parameters>
                {params_xml}
            </parameters>
        </ExecuteDataSet>
        """
        
        try:
            response = self._make_soap_request(
                self.data_access_url,
                "http://tempuri.org/IMSWebServices/DataAccess/ExecuteDataSet",
                body_content
            )
            
            # Extract dataset from response
            if response and 'soap:Body' in response:
                execute_response = response['soap:Body'].get('ExecuteDataSetResponse', {})
                result = execute_response.get('ExecuteDataSetResult', {})
                
                if result:
                    logger.info(f"Successfully executed query")
                    return result
                else:
                    logger.error("Failed to execute query: No result returned")
                    return None
            
            logger.error("Failed to execute query: Unexpected response format")
            return None
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
    
    def execute_command(self, command, parameters=None):
        """Execute a command via DataAccess.asmx"""
        logger.info(f"Executing command: {command}")
        
        params_xml = ""
        if parameters:
            for key, value in parameters.items():
                params_xml += f"""
                <Parameter>
                    <Name>{key}</Name>
                    <Value>{value}</Value>
                </Parameter>
                """
        
        body_content = f"""
        <ExecuteCommand xmlns="http://tempuri.org/IMSWebServices/DataAccess">
            <command>{command}</command>
            <parameters>
                {params_xml}
            </parameters>
        </ExecuteCommand>
        """
        
        try:
            response = self._make_soap_request(
                self.data_access_url,
                "http://tempuri.org/IMSWebServices/DataAccess/ExecuteCommand",
                body_content
            )
            
            # Check if the operation was successful
            if response and 'soap:Body' in response:
                execute_response = response['soap:Body'].get('ExecuteCommandResponse', {})
                result = execute_response.get('ExecuteCommandResult')
                
                logger.info(f"Command execution result: {result}")
                return result
            
            logger.error("Failed to execute command: Unexpected response format")
            return None
            
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            raise