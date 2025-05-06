import os
import json

from google.oauth2 import service_account
from google.auth.exceptions import GoogleAuthError

from src.logger import logger

# Set the scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Default service account file name
DEFAULT_SERVICE_ACCOUNT_FILE = 'urgot-matchup-service-account.json'

def get_credentials(service_account_file: str = DEFAULT_SERVICE_ACCOUNT_FILE):
    """
    Get credentials from a service account file.
    
    Args:
        service_account_file: Path to the service account JSON file
        
    Returns:
        Service account credentials or None if authentication failed
    """
    try:
        # Check if the service account file exists
        if not os.path.exists(service_account_file):
            logger.error(f"Service account file not found: {service_account_file}")
            return None
        
        # Create credentials from the service account file
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES)
        
        logger.info(f"Successfully loaded service account credentials from {service_account_file}")
        return credentials
        
    except GoogleAuthError as e:
        logger.error(f"Google authentication error: {str(e)}", exc_info=True)
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in service account file: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error loading service account credentials: {str(e)}", exc_info=True)
        return None

def extract_embedded_credentials():
    """
    Extract embedded service account credentials to a file if it doesn't exist already.
    This is useful for bundling credentials with the application.
    
    Returns:
        Path to the extracted credentials file or None if extraction failed
    """
    try:
        # Check if the credentials file already exists
        if os.path.exists(DEFAULT_SERVICE_ACCOUNT_FILE):
            logger.info(f"Service account file already exists: {DEFAULT_SERVICE_ACCOUNT_FILE}")
            return DEFAULT_SERVICE_ACCOUNT_FILE
        
        # The embedded credentials would be stored in a separate file or as a string constant
        # For now, we'll just return the default file name and assume it exists
        logger.warning(f"Service account file not found: {DEFAULT_SERVICE_ACCOUNT_FILE}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting embedded credentials: {str(e)}", exc_info=True)
        return None 