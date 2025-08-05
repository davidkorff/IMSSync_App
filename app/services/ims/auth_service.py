import logging
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import os

# Try to import config, but provide defaults if not available
try:
    from config import IMS_CONFIG
except ImportError:
    # Fallback configuration if config.py can't be loaded
    IMS_CONFIG = {
        "BASE_URL": os.getenv("IMS_BASE_URL", "http://10.64.32.234/ims_one"),  # Already includes environment
        "base_url": os.getenv("IMS_BASE_URL", "http://10.64.32.234/ims_one").rsplit('/', 1)[0],  # Without environment
        "environments": {
            "login": "/ims_one",
            "services": "/ims_one"
        },
        "endpoints": {
            "logon": "/logon.asmx",
        },
        "credentials": {
            "username": os.getenv("IMS_ONE_USERNAME"),
            "password": os.getenv("IMS_ONE_PASSWORD"),
        },
        "timeout": int(os.getenv("IMS_TIMEOUT", "30"))
    }

logger = logging.getLogger(__name__)


class IMSAuthService:
    """Service for handling IMS authentication and token management."""
    
    def __init__(self):
        self.base_url = IMS_CONFIG["BASE_URL"]  # This already includes /ims_one
        self.logon_endpoint = IMS_CONFIG["endpoints"]["logon"]
        self.username = IMS_CONFIG["credentials"]["username"]
        self.password = IMS_CONFIG["credentials"]["password"]
        self.timeout = IMS_CONFIG["timeout"]
        
        # Token management
        self._token: Optional[str] = None
        self._user_guid: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        
    @property
    def token(self) -> Optional[str]:
        """Get current token, refresh if expired."""
        if self._token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._token
        
        # Token expired or doesn't exist, need to login
        success, message = self.login()
        if success:
            return self._token
        else:
            logger.error(f"Failed to refresh token: {message}")
            return None
    
    @property
    def user_guid(self) -> Optional[str]:
        """Get current user GUID, refresh if expired."""
        if self._user_guid and self._token_expiry and datetime.now() < self._token_expiry:
            return self._user_guid
        
        # Token expired or doesn't exist, need to login
        success, message = self.login()
        if success:
            return self._user_guid
        else:
            logger.error(f"Failed to refresh token and get user GUID: {message}")
            return None
    
    def login(self) -> Tuple[bool, str]:
        """
        Authenticate with IMS and obtain a session token.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Construct SOAP request
            soap_request = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <LoginIMSUser xmlns="http://tempuri.org/IMSWebServices/Logon">
            <userName>{self.username}</userName>
            <tripleDESEncryptedPassword>{self.password}</tripleDESEncryptedPassword>
        </LoginIMSUser>
    </soap:Body>
</soap:Envelope>'''
            
            # Prepare headers
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://tempuri.org/IMSWebServices/Logon/LoginIMSUser'
            }
            
            # Make request
            url = f"{self.base_url}{self.logon_endpoint}"
            logger.info(f"Attempting IMS login at: {url}")
            logger.debug(f"SOAP Request:\n{soap_request}")
            
            response = requests.post(
                url,
                data=soap_request,
                headers=headers,
                timeout=self.timeout
            )
            
            # Check HTTP status
            response.raise_for_status()
            
            # Log response
            logger.debug(f"SOAP Response Status: {response.status_code}")
            logger.debug(f"SOAP Response:\n{response.text}")
            
            # Parse response
            return self._parse_login_response(response.text)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP request failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during login: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _parse_login_response(self, response_xml: str) -> Tuple[bool, str]:
        """
        Parse the login response XML and extract token.
        
        Args:
            response_xml: The SOAP response XML string
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Log raw response for debugging
            logger.debug(f"Raw response to parse:\n{response_xml}")
            
            # Parse XML - use a simpler approach
            import re
            
            # Extract UserGuid and Token using regex
            user_guid_match = re.search(r'<UserGuid>([^<]+)</UserGuid>', response_xml)
            token_match = re.search(r'<Token>([^<]+)</Token>', response_xml)
            
            if not user_guid_match or not token_match:
                return False, "UserGuid or Token not found in response"
            
            user_guid = user_guid_match.group(1)
            token = token_match.group(1)
            
            logger.debug(f"Extracted UserGuid: {user_guid}")
            logger.debug(f"Extracted Token: {token}")
            
            
            # Check for null GUIDs (login failure)
            if user_guid == "00000000-0000-0000-0000-000000000000" or \
               token == "00000000-0000-0000-0000-000000000000":
                return False, "Authentication failed - received null GUIDs"
            
            # Store credentials
            self._user_guid = user_guid
            self._token = token
            self._token_expiry = datetime.now() + timedelta(hours=8)  # Assume 8-hour session
            
            logger.info(f"Successfully authenticated. UserGuid: {user_guid}")
            return True, f"Login successful. Token: {token[:8]}..."
            
        except ET.ParseError as e:
            error_msg = f"Failed to parse XML response: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error processing login response: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get headers required for authenticated IMS requests.
        
        Returns:
            Dict containing required headers including token
        """
        return {
            'Content-Type': 'text/xml; charset=utf-8',
            'Authorization': f'Bearer {self.token}' if self.token else ''
        }
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated with valid token."""
        return self._token is not None and \
               self._token_expiry is not None and \
               datetime.now() < self._token_expiry
    
    def logout(self):
        """Clear stored authentication credentials."""
        self._token = None
        self._user_guid = None
        self._token_expiry = None
        logger.info("Logged out - cleared authentication credentials")


# Singleton instance
_auth_service = None


def get_auth_service() -> IMSAuthService:
    """Get singleton instance of auth service."""
    global _auth_service
    if _auth_service is None:
        _auth_service = IMSAuthService()
    return _auth_service