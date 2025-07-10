"""
Simplified Triton configuration
Central place for all Triton-IMS integration settings
"""

import os
from typing import Dict, Any

# Load from environment variables with clear defaults
TRITON_CONFIG = {
    # IMS Connection
    'ims': {
        'environments': {
            'ims_one': {
                'base_url': 'http://10.64.32.234/ims_one',  # Using actual IMS_ONE endpoint
                'username': os.getenv('IMS_ONE_USERNAME', 'david.korff'),
                'password': os.getenv('IMS_ONE_PASSWORD', 'kCeTLc2bxqOmG72ZBvMFkA==')
            },
            'iscmga_test': {
                'base_url': 'https://ws2.mgasystems.com/iscmga_test',
                'username': os.getenv('ISCMGA_TEST_USERNAME', 'dkorff'),
                'password': os.getenv('ISCMGA_TEST_PASSWORD', 'kCeTLc2bxqOmG72ZBvMFkA==')
            }
        },
        'default_environment': os.getenv('IMS_ENV', 'ims_one')  # Match .env file
    },
    
    # Triton API Security
    'security': {
        'api_keys': os.getenv('TRITON_API_KEYS', 'triton_test_key').split(','),
        'allowed_ips': os.getenv('TRITON_ALLOWED_IPS', '').split(',') if os.getenv('TRITON_ALLOWED_IPS') else []
    },
    
    # Producer Mapping
    'producers': {
        'default': os.getenv('TRITON_DEFAULT_PRODUCER_GUID', '895E9291-CFB6-4299-8799-9AF77DF937D6'),
        'mapping': {
            # Map Triton producer names to IMS GUIDs
            'ABC Agency': '12345678-1234-1234-1234-123456789012',
            'XYZ Broker': '87654321-4321-4321-4321-210987654321'
        }
    },
    
    # Line of Business GUIDs
    'lines': {
        'primary': os.getenv('TRITON_PRIMARY_LINE_GUID', '07564291-CBFE-4BBE-88D1-0548C88ACED4'),
        'excess': os.getenv('TRITON_EXCESS_LINE_GUID', '08798559-321C-4FC0-98ED-A61B92215F31')
    },
    
    # Location GUIDs
    'locations': {
        'issuing': os.getenv('TRITON_ISSUING_LOCATION_GUID', 'C5C006BB-6437-42F3-95D4-C090ADD3B37D'),
        'company': os.getenv('TRITON_COMPANY_LOCATION_GUID', 'DF35D4C7-C663-4974-A886-A1E18D3C9618'),
        'quoting': os.getenv('TRITON_QUOTING_LOCATION_GUID', 'C5C006BB-6437-42F3-95D4-C090ADD3B37D')
    },
    
    # Default Values
    'defaults': {
        'business_type_id': int(os.getenv('TRITON_DEFAULT_BUSINESS_TYPE_ID', '1')),
        'underwriter_guid': os.getenv('TRITON_DEFAULT_UNDERWRITER_GUID', 'E4391D2A-58FB-4E2D-8B7D-3447D9E18C88'),
        'office_guid': os.getenv('TRITON_DEFAULT_OFFICE_GUID', '00000000-0000-0000-0000-000000000000'),
        'user_guid': os.getenv('TRITON_DEFAULT_USER_GUID', '00000000-0000-0000-0000-000000000000')
    },
    
    # Excel Rating Configuration
    'rating': {
        'use_excel_rating': os.getenv('TRITON_USE_EXCEL_RATING', 'true').lower() == 'true',
        'raters': {
            'primary': {
                'rater_id': int(os.getenv('TRITON_PRIMARY_RATER_ID', '1')),
                'factor_set_guid': os.getenv('TRITON_PRIMARY_FACTOR_SET_GUID'),
                'template': 'triton_primary.xlsx'
            },
            'excess': {
                'rater_id': int(os.getenv('TRITON_EXCESS_RATER_ID', '2')),
                'factor_set_guid': os.getenv('TRITON_EXCESS_FACTOR_SET_GUID'),
                'template': 'triton_excess.xlsx'
            },
            'primary_CA': {  # State-specific example
                'rater_id': int(os.getenv('TRITON_PRIMARY_CA_RATER_ID', '3')),
                'factor_set_guid': os.getenv('TRITON_PRIMARY_CA_FACTOR_SET_GUID'),
                'template': 'triton_primary_ca.xlsx'
            }
        }
    },
    
    # Reason Code Mappings
    'mappings': {
        'cancellation_reasons': {
            'non-payment': 1,
            'insured-request': 2,
            'underwriting': 3,
            'fraud': 4,
            'other': 99
        },
        'endorsement_reasons': {
            'add-coverage': 1,
            'remove-coverage': 2,
            'change-limit': 3,
            'add-location': 4,
            'remove-location': 5,
            'other': 99
        },
        'reinstatement_reasons': {
            'payment-received': 1,
            'error': 2,
            'appeal': 3,
            'other': 99
        }
    },
    
    # Processing Options
    'processing': {
        'store_raw_data': True,  # Store all Triton data in IMS
        'retry_attempts': 3,
        'retry_delay_seconds': 5,
        'invoice_retrieval_attempts': 3,
        'invoice_retrieval_delay_seconds': 2
    },
    
    # Webhook Configuration
    'webhooks': {
        'error_callback_url': os.getenv('TRITON_ERROR_CALLBACK_URL'),
        'success_callback_url': os.getenv('TRITON_SUCCESS_CALLBACK_URL'),
        'timeout_seconds': 30
    }
}


def get_config_for_environment(environment: str = None) -> Dict[str, Any]:
    """
    Get configuration for a specific IMS environment
    """
    env = environment or TRITON_CONFIG['ims']['default_environment']
    
    if env not in TRITON_CONFIG['ims']['environments']:
        raise ValueError(f"Unknown environment: {env}")
    
    # Build environment-specific config
    env_config = TRITON_CONFIG['ims']['environments'][env].copy()
    
    # Merge with rest of config
    config = {
        'ims_base_url': env_config['base_url'],
        'ims_username': env_config['username'],  # Changed to match IMS client expectation
        'ims_password': env_config['password'],  # Changed to match IMS client expectation
        'use_excel_rating': TRITON_CONFIG['rating']['use_excel_rating'],
        'producers': TRITON_CONFIG['producers'],
        'lines': TRITON_CONFIG['lines'],
        'locations': TRITON_CONFIG['locations'],
        'defaults': TRITON_CONFIG['defaults'],
        'raters': TRITON_CONFIG['rating']['raters'],
        'mappings': TRITON_CONFIG['mappings'],
        'processing': TRITON_CONFIG['processing']
    }
    
    return config