"""
Simplified IMS Client
Provides direct, simple methods for IMS operations
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import date, datetime
import base64
from zeep import Client
from zeep.transports import Transport
from requests import Session

logger = logging.getLogger(__name__)


class IMSClient:
    """
    Simple, direct client for IMS SOAP operations
    Each method does one thing and returns clear results
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.token = None
        self.clients = {}
        self._setup_clients()
    
    def _setup_clients(self):
        """Setup SOAP clients for each service"""
        session = Session()
        session.verify = False  # IMS uses internal IPs, may not have valid SSL
        transport = Transport(session=session)
        
        # Use the actual IMS endpoints from config
        base_url = "http://10.64.32.234/ims_one"  # From IMS_ONE.config
        
        # Initialize clients for each service
        services = {
            'Logon': f"{base_url}/logon.asmx?WSDL",
            'InsuredFunctions': f"{base_url}/InsuredFunctions.asmx?WSDL",
            'ProducerFunctions': f"{base_url}/ProducerFunctions.asmx?WSDL",
            'QuoteFunctions': f"{base_url}/QuoteFunctions.asmx?WSDL",
            'DocumentFunctions': f"{base_url}/DocumentFunctions.asmx?WSDL",
            'DataAccess': f"{base_url}/DataAccess.asmx?WSDL",
            'InvoiceFactory': f"{base_url}/InvoiceFactory.asmx?WSDL"
        }
        
        for service_name, wsdl_url in services.items():
            try:
                self.clients[service_name] = Client(wsdl_url, transport=transport)
                logger.info(f"Initialized {service_name} client")
            except Exception as e:
                logger.error(f"Failed to initialize {service_name}: {str(e)}")
    
    def login(self):
        """Login to IMS and get authentication token"""
        try:
            # Get credentials from config - these come from .env file
            username = self.config.get('ims_username')
            password = self.config.get('ims_password')
            
            if not username or not password:
                raise ValueError("IMS credentials not configured. Check IMS_USERNAME and IMS_PASSWORD in .env")
            
            logger.info(f"Attempting IMS login for user: {username}")
            
            service = self.clients['Logon'].service
            response = service.LoginIMSUser(username, password)
            
            if response and hasattr(response, 'Token') and response.Token:
                self.token = response.Token
                logger.info(f"Successfully logged into IMS as {username}")
                return True
            else:
                logger.error("Failed to login to IMS - no token received")
                return False
                
        except Exception as e:
            logger.error(f"IMS login error: {str(e)}")
            raise
    
    def _get_header(self):
        """Get authentication header for SOAP calls"""
        if not self.token:
            self.login()
        
        return {
            'TokenHeader': {
                'Token': self.token,
                'Context': 'Integration'
            }
        }
    
    # Insured Operations
    
    def find_or_create_insured(self, insured_data: Dict[str, Any]) -> str:
        """
        Find existing insured or create new one
        Returns insured GUID
        """
        # First try to find by name
        service = self.clients['InsuredFunctions'].service
        
        try:
            # Search by name with location if available
            insured_guid = service.FindInsuredByName(
                insuredName=insured_data['name'],
                city=insured_data.get('city', ''),
                state=insured_data.get('state', ''),
                zip=insured_data.get('zip', ''),
                zipPlus='',
                _soapheaders=self._get_header()
            )
            
            if insured_guid and str(insured_guid) != '00000000-0000-0000-0000-000000000000':
                # Found existing insured
                logger.info(f"Found existing insured: {insured_guid}")
                return str(insured_guid)
            
            # Not found, create new
            logger.info(f"Creating new insured: {insured_data['name']}")
            
            # Get valid office GUID from config
            office_guid = insured_data.get('office_guid')
            if not office_guid:
                # Use null GUID as default
                office_guid = '00000000-0000-0000-0000-000000000000'
            
            # Create insured object with required fields
            insured = {
                'CorporationName': insured_data['name'],
                'BusinessTypeID': insured_data.get('business_type_id', 5),  # Default to 5 for LLC
                'NameOnPolicy': insured_data['name'],
                'Office': office_guid
            }
            
            # Add optional fields if available
            if 'tax_id' in insured_data and insured_data['tax_id']:
                insured['FEIN'] = insured_data['tax_id']
            if 'dba' in insured_data and insured_data['dba']:
                insured['DBA'] = insured_data['dba']
            
            # Log exactly what we're sending
            logger.info(f"Sending to IMS AddInsured: {insured}")
            
            result = service.AddInsured(
                insured=insured,
                _soapheaders=self._get_header()
            )
            
            # Log the raw result
            logger.info(f"IMS AddInsured raw result: {result}")
            logger.info(f"Result type: {type(result)}")
            if hasattr(result, '__dict__'):
                logger.info(f"Result attributes: {result.__dict__}")
            
            # Try different ways to get the GUID
            insured_guid = None
            
            # Method 1: Direct string result
            if isinstance(result, str) and result != '00000000-0000-0000-0000-000000000000':
                insured_guid = result
            # Method 2: InsuredGUID attribute
            elif hasattr(result, 'InsuredGUID'):
                insured_guid = str(result.InsuredGUID)
            # Method 3: InsuredGuid attribute (different case)
            elif hasattr(result, 'InsuredGuid'):
                insured_guid = str(result.InsuredGuid)
            # Method 4: GUID attribute
            elif hasattr(result, 'GUID'):
                insured_guid = str(result.GUID)
            # Method 5: Guid attribute
            elif hasattr(result, 'Guid'):
                insured_guid = str(result.Guid)
            # Method 6: If result is the GUID itself
            elif result and str(result) != '00000000-0000-0000-0000-000000000000':
                insured_guid = str(result)
            
            if insured_guid and insured_guid != '00000000-0000-0000-0000-000000000000':
                logger.info(f"Created insured with GUID: {insured_guid}")
                
                # Add location if provided
                if all(key in insured_data for key in ['address', 'city', 'state', 'zip']):
                    try:
                        self._add_insured_location(insured_guid, insured_data)
                    except Exception as loc_err:
                        logger.warning(f"Failed to add location: {str(loc_err)}")
                
                return insured_guid
            else:
                logger.error(f"No valid GUID returned. Result was: {result}")
                raise Exception(f"Failed to create insured - no valid GUID returned. Result: {result}")
                
        except Exception as e:
            logger.error(f"Error in find_or_create_insured: {str(e)}")
            raise
    
    def _add_insured_location(self, insured_guid: str, location_data: Dict[str, Any]):
        """Add location to insured"""
        try:
            service = self.clients['InsuredFunctions'].service
            
            # Create location object
            location = {
                'InsuredGuid': insured_guid,
                'Address1': location_data.get('address', ''),
                'Address2': location_data.get('address2', ''),
                'City': location_data.get('city', ''),
                'State': location_data.get('state', ''),
                'Zip': location_data.get('zip', ''),
                'ISOCountryCode': 'USA',
                'LocationTypeID': 1  # Primary location
            }
            
            result = service.AddInsuredLocation(
                location=location,
                _soapheaders=self._get_header()
            )
            logger.info(f"Added location to insured {insured_guid}")
        except Exception as e:
            logger.warning(f"Could not add location: {str(e)}")
    
    # Submission Operations
    
    def create_submission(self, submission_data: Dict[str, Any]) -> str:
        """Create submission and return GUID"""
        try:
            service = self.clients['QuoteFunctions'].service
            
            # Log the submission data we're about to send
            logger.info(f"Creating submission with data: {submission_data}")
            
            # Create submission object
            submission = {
                'InsuredGUID': submission_data['insured_guid'],
                'SubmissionDate': submission_data['submission_date'],
                'ProducerContactGUID': submission_data['producer_guid'],
                'UnderwriterGUID': submission_data['underwriter_guid'],
                'ProducerLocationGUID': submission_data['producer_guid']  # producer location
            }
            
            # Log the submission object
            logger.info(f"Submission object to send: {submission}")
            
            # The AddSubmission method expects individual parameters, not an object
            result = service.AddSubmission(
                submission['InsuredGUID'],
                submission['SubmissionDate'],
                submission['ProducerContactGUID'],
                submission['UnderwriterGUID'],
                submission['ProducerLocationGUID'],
                _soapheaders=self._get_header()
            )
            
            # Log the raw result
            logger.info(f"AddSubmission raw result: {result}")
            logger.info(f"Result type: {type(result)}")
            if hasattr(result, '__dict__'):
                logger.info(f"Result attributes: {result.__dict__}")
            
            # Try different ways to get the GUID
            submission_guid = None
            
            # Method 1: Direct string result
            if isinstance(result, str) and result != '00000000-0000-0000-0000-000000000000':
                submission_guid = result
            # Method 2: SubmissionGUID attribute
            elif hasattr(result, 'SubmissionGUID'):
                submission_guid = str(result.SubmissionGUID)
            # Method 3: SubmissionGuid attribute (different case)
            elif hasattr(result, 'SubmissionGuid'):
                submission_guid = str(result.SubmissionGuid)
            # Method 4: GUID attribute
            elif hasattr(result, 'GUID'):
                submission_guid = str(result.GUID)
            # Method 5: Guid attribute
            elif hasattr(result, 'Guid'):
                submission_guid = str(result.Guid)
            # Method 6: If result is the GUID itself
            elif result and str(result) != '00000000-0000-0000-0000-000000000000':
                submission_guid = str(result)
            
            if submission_guid and submission_guid != '00000000-0000-0000-0000-000000000000':
                logger.info(f"Created submission: {submission_guid}")
                return submission_guid
            else:
                logger.error(f"No valid GUID returned. Result was: {result}")
                raise Exception(f"Failed to create submission - no valid GUID returned. Result: {result}")
                
        except Exception as e:
            logger.error(f"Error creating submission: {str(e)}")
            raise
    
    # Quote Operations
    
    def create_quote(self, quote_data: Dict[str, Any]) -> str:
        """Create quote and return GUID"""
        try:
            service = self.clients['QuoteFunctions'].service
            
            result = service.AddQuote(
                quote_data['submission_guid'],
                quote_data['effective_date'],
                quote_data['expiration_date'],
                quote_data['state'],
                quote_data['line_guid'],
                1,  # status (new)
                1,  # billing type (agency bill)
                quote_data['producer_guid'],
                quote_data['location_guids']['issuing'],
                quote_data['location_guids']['company'],
                quote_data['location_guids']['quoting'],
                _soapheaders=self._get_header()
            )
            
            if result and hasattr(result, 'QuoteGUID'):
                quote_guid = str(result.QuoteGUID)
                logger.info(f"Created quote: {quote_guid}")
                return quote_guid
            else:
                raise Exception("Failed to create quote - no GUID returned")
                
        except Exception as e:
            logger.error(f"Error creating quote: {str(e)}")
            raise
    
    def add_quote_option(self, quote_guid: str) -> int:
        """Add quote option and return option ID"""
        try:
            service = self.clients['QuoteFunctions'].service
            
            result = service.AddQuoteOption(
                quote_guid,
                _soapheaders=self._get_header()
            )
            
            if result and hasattr(result, 'QuoteOptionID'):
                option_id = int(result.QuoteOptionID)
                logger.info(f"Created quote option: {option_id}")
                return option_id
            else:
                raise Exception("Failed to create quote option")
                
        except Exception as e:
            logger.error(f"Error adding quote option: {str(e)}")
            raise
    
    def add_premium(self, quote_guid: str, option_id: int, premium: float):
        """Add premium to quote option"""
        try:
            service = self.clients['QuoteFunctions'].service
            
            result = service.AddPremium(
                quote_guid,
                option_id,
                premium,
                'Premium from Triton',
                _soapheaders=self._get_header()
            )
            
            logger.info(f"Added premium {premium} to quote {quote_guid}")
            
        except Exception as e:
            logger.error(f"Error adding premium: {str(e)}")
            raise
    
    def bind_quote(self, option_id: int) -> str:
        """Bind quote option and return policy number"""
        try:
            service = self.clients['QuoteFunctions'].service
            
            result = service.Bind(
                option_id,
                _soapheaders=self._get_header()
            )
            
            if result:
                policy_number = str(result)
                logger.info(f"Bound policy: {policy_number}")
                return policy_number
            else:
                raise Exception("Failed to bind quote - no policy number returned")
                
        except Exception as e:
            logger.error(f"Error binding quote: {str(e)}")
            raise
    
    # Excel Rating Operations
    
    def import_excel_rater(self, quote_guid: str, file_bytes: bytes, file_name: str,
                          rater_id: int, factor_set_guid: Optional[str] = None,
                          apply_fees: bool = True) -> Dict[str, Any]:
        """Import Excel file for rating"""
        try:
            service = self.clients['QuoteFunctions'].service
            
            # Convert bytes to base64 for SOAP
            file_base64 = base64.b64encode(file_bytes).decode('utf-8')
            
            result = service.ImportExcelRater(
                quote_guid,
                file_base64,
                file_name,
                rater_id,
                factor_set_guid or '00000000-0000-0000-0000-000000000000',
                apply_fees,
                _soapheaders=self._get_header()
            )
            
            if result and hasattr(result, 'Success') and result.Success:
                premiums = []
                if hasattr(result, 'Premiums') and result.Premiums:
                    for option in result.Premiums.OptionResult:
                        premiums.append({
                            'quote_option_guid': str(option.QuoteOptionGuid),
                            'premium_total': float(option.PremiumTotal),
                            'fee_total': float(option.FeeTotal) if hasattr(option, 'FeeTotal') else 0
                        })
                
                logger.info(f"Excel rating successful for quote {quote_guid}")
                return {
                    'success': True,
                    'premiums': premiums
                }
            else:
                error_msg = result.ErrorMessage if hasattr(result, 'ErrorMessage') else 'Unknown error'
                logger.error(f"Excel rating failed: {error_msg}")
                return {
                    'success': False,
                    'error_message': error_msg
                }
                
        except Exception as e:
            logger.error(f"Error in Excel rating: {str(e)}")
            return {
                'success': False,
                'error_message': str(e)
            }
    
    def save_rating_sheet(self, quote_guid: str, rater_id: int, file_bytes: bytes, file_name: str):
        """Save rating sheet for reference"""
        try:
            service = self.clients['DocumentFunctions'].service
            
            # Convert to base64
            file_base64 = base64.b64encode(file_bytes).decode('utf-8')
            
            service.SaveRatingSheet(
                quote_guid,
                rater_id,
                file_base64,
                file_name,
                _soapheaders=self._get_header()
            )
            
            logger.info(f"Saved rating sheet for quote {quote_guid}")
            
        except Exception as e:
            logger.warning(f"Could not save rating sheet: {str(e)}")
    
    # Policy Operations
    
    def get_control_number(self, policy_number: str) -> int:
        """Get control number from policy number"""
        try:
            service = self.clients['QuoteFunctions'].service
            
            result = service.GetControlNumber(
                policy_number,
                _soapheaders=self._get_header()
            )
            
            if result:
                control_number = int(result)
                logger.info(f"Got control number {control_number} for policy {policy_number}")
                return control_number
            else:
                raise Exception(f"Control number not found for policy {policy_number}")
                
        except Exception as e:
            logger.error(f"Error getting control number: {str(e)}")
            raise
    
    def cancel_policy(self, cancellation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel policy using stored procedure"""
        try:
            result = self.execute_command(
                'CancelPolicy',
                [
                    'ControlNumber', str(cancellation_data['control_number']),
                    'CancellationDate', cancellation_data['cancellation_date'].strftime('%Y-%m-%d'),
                    'CancellationReasonID', str(cancellation_data['cancellation_reason_id']),
                    'Comments', cancellation_data.get('comments', ''),
                    'UserGuid', cancellation_data['user_guid'],
                    'FlatCancel', '1' if cancellation_data.get('flat_cancel') else '0'
                ]
            )
            
            logger.info(f"Policy cancelled: {result}")
            return {
                'success': True,
                'message': 'Policy cancelled successfully',
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error cancelling policy: {str(e)}")
            raise
    
    def create_endorsement(self, endorsement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create endorsement using stored procedure"""
        try:
            result = self.execute_command(
                'CreateEndorsement',
                [
                    'ControlNumber', str(endorsement_data['control_number']),
                    'EffectiveDate', endorsement_data['effective_date'].strftime('%Y-%m-%d'),
                    'Comments', endorsement_data.get('description', ''),
                    'ReasonID', str(endorsement_data['reason_id']),
                    'UserGuid', endorsement_data['user_guid']
                ]
            )
            
            # Parse result to get endorsement GUID if available
            endorsement_guid = None
            if result and 'EndorsementQuoteGUID' in result:
                endorsement_guid = result.get('EndorsementQuoteGUID')
            
            logger.info(f"Endorsement created: {endorsement_guid}")
            return {
                'success': True,
                'message': 'Endorsement created successfully',
                'endorsement_quote_guid': endorsement_guid
            }
            
        except Exception as e:
            logger.error(f"Error creating endorsement: {str(e)}")
            raise
    
    def reinstate_policy(self, reinstatement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reinstate policy using stored procedure"""
        try:
            params = [
                'ControlNumber', str(reinstatement_data['control_number']),
                'ReinstatementDate', reinstatement_data['reinstatement_date'].strftime('%Y-%m-%d'),
                'ReasonID', str(reinstatement_data['reason_id']),
                'Comments', reinstatement_data.get('comments', ''),
                'UserGuid', reinstatement_data['user_guid']
            ]
            
            if reinstatement_data.get('payment_received'):
                params.extend(['PaymentReceived', str(reinstatement_data['payment_received'])])
            if reinstatement_data.get('check_number'):
                params.extend(['CheckNumber', reinstatement_data['check_number']])
            
            result = self.execute_command('ReinstatePolicy', params)
            
            logger.info(f"Policy reinstated: {result}")
            return {
                'success': True,
                'message': 'Policy reinstated successfully',
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error reinstating policy: {str(e)}")
            raise
    
    # Invoice Operations
    
    def get_latest_invoice(self, policy_number: str) -> Optional[Dict[str, Any]]:
        """Get latest invoice for policy"""
        try:
            # This would use a custom stored procedure or the invoice service
            # For now, return None to indicate not implemented
            logger.info(f"Getting invoice for policy {policy_number}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting invoice: {str(e)}")
            return None
    
    # Utility Operations
    
    def update_external_id(self, quote_guid: str, external_id: str, source: str):
        """Update external quote ID"""
        try:
            service = self.clients['QuoteFunctions'].service
            
            service.UpdateExternalQuoteId(
                quote_guid,
                external_id,
                source,
                _soapheaders=self._get_header()
            )
            
            logger.info(f"Updated external ID for quote {quote_guid}: {external_id}")
            
        except Exception as e:
            logger.warning(f"Could not update external ID: {str(e)}")
    
    def execute_command(self, procedure_name: str, parameters: List[str]) -> Any:
        """Execute custom stored procedure"""
        try:
            service = self.clients['DataAccess'].service
            
            result = service.ExecuteCommand(
                procedure_name,
                parameters,
                _soapheaders=self._get_header()
            )
            
            logger.info(f"Executed command {procedure_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing command {procedure_name}: {str(e)}")
            raise