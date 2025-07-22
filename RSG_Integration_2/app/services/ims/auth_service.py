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
        "base_url": os.getenv("IMS_BASE_URL", "http://10.64.32.234"),
        "environments": {
            "login": "/ims_one",
            "services": "/ims_origintest"
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
        self.base_url = IMS_CONFIG["base_url"]
        self.login_env = IMS_CONFIG.get("environments", {}).get("login", "/ims_one")
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
            url = f"{self.base_url}{self.login_env}{self.logon_endpoint}"
            logger.info(f"Attempting IMS login at: {url}")
            
            response = requests.post(
                url,
                data=soap_request,
                headers=headers,
                timeout=self.timeout
            )
            
            # Check HTTP status
            response.raise_for_status()
            
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
            # Parse XML
            root = ET.fromstring(response_xml)
            
            # Define namespaces
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'ims': 'http://tempuri.org/IMSWebServices/Logon'
            }
            
            # Find LoginIMSUserResult
            result = root.find('.//ims:LoginIMSUserResult', namespaces)
            
            if result is None:
                return False, "LoginIMSUserResult not found in response"
            
            # Extract UserGuid and Token
            user_guid_elem = result.find('.//UserGuid')
            token_elem = result.find('.//Token')
            
            if user_guid_elem is None or token_elem is None:
                return False, "UserGuid or Token not found in response"
            
            user_guid = user_guid_elem.text
            token = token_elem.text
            
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