import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from playwright.sync_api import sync_playwright
import time

# Scopes required for Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_google_credentials():
    """Get Google credentials, creating or refreshing them as needed."""
    creds = None
    # Look for existing token
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_info(
            json.load(open('token.json')), SCOPES)
    
    # If no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

def access_sheets_with_playwright():
    # Get credentials first
    creds = get_google_credentials()
    
    # Get the actual access token
    token = creds.token
    
    # Use Playwright to navigate to Google Sheets with the token
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        
        # First, access Google to set cookies
        page = context.new_page()
        page.goto('https://accounts.google.com')
        
        # Set authentication cookies using the token
        # This uses OAuth 2.0 token to set appropriate cookies
        page.evaluate(f'''
        () => {{
            document.cookie = "GAPS=1:authentication_token={token};domain=.google.com;path=/";
        }}
        ''')
        
        sheet_id = "1wcrN6SRX1EsEce4s2HL8GBIa1CjPVG5L32mW9ml7K3s"
        page.goto(f'https://docs.google.com/spreadsheets/d/{sheet_id}/edit')
        
        # Check if we're properly authenticated by looking for sheet elements
        if page.query_selector('.grid-container'):
            print("Successfully accessed the Google Sheet!")
            
            # Now you can interact with the sheet using Playwright
            # For example:
            # page.click('.some-sheet-element')
            # page.fill('input.cell-input', 'New Value')
            
            # Do your sheet interactions here...
            time.sleep(5)  # Just for demonstration
        else:
            print("Failed to access the sheet properly")
        
        browser.close()

if __name__ == "__main__":
    access_sheets_with_playwright()