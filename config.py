"""
Configuration file for IMS Policy Loader
Contains multiple environment configurations and credentials
"""

# Available environments
ENVIRONMENTS = {
    "ims_one": {
        "config_file": "IMS_ONE.config",
        "username": "david.korff",
        "password": "kCeTLc2bxqOmG72ZBvMFkA=="
    },
    "iscmga_test": {
        "config_file": "ISCMGA_Test.config",
        "username": "dkorff",
        "password": "kCeTLc2bxqOmG72ZBvMFkA=="
    }
    # Add more environments as needed
}

# Default environment to use if none specified
DEFAULT_ENVIRONMENT = "iscmga_test"

# IMS Authentication Credentials
IMS_USERNAME = "dkorff"
IMS_PASSWORD = "kCeTLc2bxqOmG72ZBvMFkA=="  # This is the encrypted password

# Config file path
IMS_CONFIG_FILE = "ISCMGA_Test.config" 