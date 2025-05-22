import os
import webbrowser
import socket
import http.server
import socketserver
import threading
import urllib.parse
from typing import Optional

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.logger import logger

# Set the scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Constants
DEFAULT_PORT = 8080
REDIRECT_URI_FORMAT = 'http://localhost:{port}'
DEFAULT_SECRETS_FILE = 'client_secrets.json'
DEFAULT_TOKEN_FILE = 'token.json'
TARGET_SPREADSHEET_ID = '1wcrN6SRX1EsEce4s2HL8GBIa1CjPVG5L32mW9ml7K3s'

# Success HTML page shown after authentication
AUTH_COMPLETE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Authentication Complete</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #1e2124;
            color: #ffffff;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background-color: #2c2f33;
            border-radius: 8px;
            padding: 40px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            text-align: center;
            max-width: 600px;
        }
        h1 {
            color: #43b581;
            margin-bottom: 20px;
        }
        .success-icon {
            font-size: 64px;
            color: #43b581;
            margin-bottom: 20px;
        }
        .close-button {
            background-color: #7289da;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 20px;
        }
        .close-button:hover {
            background-color: #5b6eae;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">✓</div>
        <h1>Authentication Complete</h1>
        <button class="close-button" onclick="window.close()">Close Window</button>
    </div>
    <script>
        // Close the window automatically after 5 seconds
        setTimeout(function() {
            window.close();
        }, 5000);
    </script>
</body>
</html>
"""

class AuthHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for OAuth callback."""
    
    def __init__(self, *args, auth_code_callback=None, **kwargs):
        self.auth_code_callback = auth_code_callback
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET request with OAuth callback."""
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        
        if 'code' in query_components:
            code = query_components['code'][0]
            if self.auth_code_callback:
                self.auth_code_callback(code)
            
            # Send success page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(AUTH_COMPLETE_HTML.encode())
        else:
            # Handle error or other requests
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Authentication Failed</h1><p>No authorization code received.</p></body></html>')

def find_available_port(start_port=DEFAULT_PORT) -> int:
    """Find an available port to use for the local server."""
    port = start_port
    max_port = start_port + 100  # Try up to 100 ports
    
    while port < max_port:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            port += 1
    
    # If no port is available, return the default and hope for the best
    logger.warning(f"No available ports found between {start_port} and {max_port}. Using default port {DEFAULT_PORT}.")
    return DEFAULT_PORT

class OAuthLocalServer:
    """Run a local server to handle OAuth 2.0 callback."""
    
    def __init__(self, port=None):
        self.port = port or find_available_port()
        self.server = None
        self.auth_code = None
    
    def start_server(self):
        """Start the local server."""
        def handler(*args, **kwargs):
            return AuthHandler(*args, auth_code_callback=self.handle_auth_code, **kwargs)
        
        self.server = socketserver.TCPServer(("localhost", self.port), handler)
        
        # Run server in a thread
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        logger.info(f"Started local authentication server on port {self.port}")
    
    def handle_auth_code(self, code):
        """Store the authentication code."""
        self.auth_code = code
        logger.info("Received authentication code")
        # Shutdown the server after receiving the code
        threading.Thread(target=self.server.shutdown).start()
    
    def get_redirect_uri(self) -> str:
        """Get the redirect URI for OAuth flow."""
        return REDIRECT_URI_FORMAT.format(port=self.port)
    
    def wait_for_code(self, timeout=120) -> Optional[str]:
        """Wait for the authentication code to be received."""
        import time
        
        start_time = time.time()
        while self.auth_code is None:
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                logger.warning(f"Timed out waiting for authentication code after {timeout} seconds")
                return None
        
        return self.auth_code

def get_credentials(force_new_auth=False) -> Optional[Credentials]:
    """
    Get or refresh user credentials.
    
    Args:
        force_new_auth: If True, force new authentication even if valid tokens exist
    
    Returns:
        Credentials object or None if authentication failed
    """
    creds = None
    
    # Check if token.json exists
    if os.path.exists(DEFAULT_TOKEN_FILE) and not force_new_auth:
        logger.info(f"Loading credentials from {DEFAULT_TOKEN_FILE}")
        try:
            creds = Credentials.from_authorized_user_file(DEFAULT_TOKEN_FILE, SCOPES)
        except Exception as e:
            logger.error(f"Error loading credentials from {DEFAULT_TOKEN_FILE}: {str(e)}", exc_info=True)
            # Continue to authentication flow if loading fails
    
    # Check if credentials need to be refreshed or obtained
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials")
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing credentials: {str(e)}", exc_info=True)
                # If refresh fails, proceed to full authentication
                creds = None
        
        # If no valid credentials available, run the auth flow
        if not creds:
            logger.info("Starting new authentication flow")
            
            if not os.path.exists(DEFAULT_SECRETS_FILE):
                logger.error(f"Client secrets file {DEFAULT_SECRETS_FILE} not found")
                return None
            
            try:
                # Start local server
                server = OAuthLocalServer()
                server.start_server()
                
                # Set up the flow with the local server
                flow = InstalledAppFlow.from_client_secrets_file(
                    DEFAULT_SECRETS_FILE, 
                    scopes=SCOPES,
                    redirect_uri=server.get_redirect_uri()
                )
                
                # Get the authorization URL
                auth_url, _ = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true',
                    prompt='consent'  # Force display of consent screen to get refresh token
                )
                
                # Open browser for user to authenticate
                logger.info(f"Opening browser for authentication: {auth_url}")
                webbrowser.open(auth_url)
                
                # Wait for the redirect with the auth code
                auth_code = server.wait_for_code()
                
                if not auth_code:
                    logger.error("Failed to receive authentication code")
                    return None
                
                # Exchange auth code for credentials
                flow.fetch_token(code=auth_code)
                creds = flow.credentials
                
                # Save credentials for future use
                save_credentials(creds)
                
            except Exception as e:
                logger.error(f"Error during authentication flow: {str(e)}", exc_info=True)
                return None
    
    # Verify the user has access to the sheet
    if not verify_sheet_access(creds):
        logger.error("User does not have access to the required spreadsheet")
        return None
    
    return creds

def save_credentials(creds: Credentials) -> bool:
    """Save credentials to the token file."""
    try:
        token_dir = os.path.dirname(DEFAULT_TOKEN_FILE)
        if token_dir and not os.path.exists(token_dir):
            os.makedirs(token_dir)
            
        with open(DEFAULT_TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
        
        logger.info(f"Saved credentials to {DEFAULT_TOKEN_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving credentials to {DEFAULT_TOKEN_FILE}: {str(e)}", exc_info=True)
        return False

def verify_sheet_access(creds: Credentials) -> bool:
    """
    Verify that the user has access to the required spreadsheet.
    
    Args:
        creds: Google credentials to verify
        
    Returns:
        True if the user has access, False otherwise
    """
    try:
        # Build the Sheets API client
        service = build('sheets', 'v4', credentials=creds)
        
        # Try to access basic metadata from the spreadsheet
        # This will fail if the user doesn't have access
        result = service.spreadsheets().get(
            spreadsheetId=TARGET_SPREADSHEET_ID,
            fields='properties.title'
        ).execute()
        
        sheet_title = result.get('properties', {}).get('title', '')
        logger.info(f"Successfully verified access to spreadsheet: {sheet_title}")
        return True
        
    except HttpError as e:
        if e.resp.status == 403:  # Forbidden - No access
            logger.error("User does not have access to the required spreadsheet")
        elif e.resp.status == 404:  # Not Found
            logger.error("Spreadsheet not found. It may have been deleted or moved.")
        else:
            logger.error(f"HTTP error verifying sheet access: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error verifying sheet access: {str(e)}", exc_info=True)
        return False

def force_reauthentication() -> bool:
    """Force re-authentication by removing the token file."""
    try:
        if os.path.exists(DEFAULT_TOKEN_FILE):
            os.remove(DEFAULT_TOKEN_FILE)
            logger.info(f"Removed token file {DEFAULT_TOKEN_FILE} to force re-authentication")
        return True
    except Exception as e:
        logger.error(f"Error removing token file {DEFAULT_TOKEN_FILE}: {str(e)}", exc_info=True)
        return False 