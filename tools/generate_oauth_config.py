#!/usr/bin/env python
"""
Generate OAuth client_secrets.json file from user input.
This helps developers set up the OAuth configuration without manual JSON editing.
"""

import json
import sys
from pathlib import Path

# Template for the client_secrets.json file
CLIENT_SECRETS_TEMPLATE = {
    "installed": {
        "client_id": "",
        "project_id": "",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "",
        "redirect_uris": ["http://localhost"]
    }
}

def get_user_input():
    """Get the required OAuth credentials from user input."""
    print("\n=== Urgot Matchup Helper OAuth Configuration Generator ===\n")
    
    print("This script will help you create the client_secrets.json file for OAuth authentication.")
    print("You'll need to provide your OAuth client ID and client secret from the Google Cloud Console.")
    print("If you haven't created these yet, please follow the instructions in DEVELOPER_AUTH_SETUP.md")
    print("\nPress Enter to continue...")
    input()
    
    project_id = input("\nEnter your Google Cloud Project ID: ")
    client_id = input("Enter your OAuth Client ID: ")
    client_secret = input("Enter your OAuth Client Secret: ")
    
    # Apply the values to the template
    config = CLIENT_SECRETS_TEMPLATE.copy()
    config["installed"]["project_id"] = project_id
    config["installed"]["client_id"] = client_id
    config["installed"]["client_secret"] = client_secret
    
    return config

def write_config_file(config, output_path="client_secrets.json"):
    """Write the config to the client_secrets.json file."""
    try:
        with open(output_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"\nSuccessfully created {output_path}")
        print("\nIMPORTANT: Do not commit this file to version control!")
        return True
    except Exception as e:
        print(f"\nError writing config file: {str(e)}")
        return False

def confirm_overwrite(file_path):
    """Confirm with the user whether to overwrite an existing file."""
    while True:
        response = input(f"\nFile {file_path} already exists. Overwrite? (y/n): ").lower()
        if response == 'y':
            return True
        elif response == 'n':
            return False
        print("Please enter 'y' or 'n'.")

def main():
    """Main entry point."""
    # Determine the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    output_path = project_root / "client_secrets.json"
    
    # Check if the file already exists
    if output_path.exists() and not confirm_overwrite(output_path):
        print("Operation cancelled.")
        return 1
    
    # Get the configuration from user input
    config = get_user_input()
    
    # Write the configuration to the file
    if write_config_file(config, output_path):
        # Check if there's a spreadsheet ID to update
        update_spreadsheet = input("\nWould you like to update the target spreadsheet ID? (y/n): ").lower() == 'y'
        
        if update_spreadsheet:
            spreadsheet_id = input("Enter the target Google Spreadsheet ID: ")
            
            # Find the google_auth.py file
            auth_file = project_root / "src" / "auth" / "google_auth.py"
            
            if auth_file.exists():
                try:
                    # Read the file
                    with open(auth_file, "r") as f:
                        content = f.read()
                    
                    # Replace the spreadsheet ID
                    import re
                    updated_content = re.sub(
                        r'TARGET_SPREADSHEET_ID\s*=\s*[\'"](.+?)[\'"]',
                        f'TARGET_SPREADSHEET_ID = "{spreadsheet_id}"',
                        content
                    )
                    
                    # Write the updated content
                    with open(auth_file, "w") as f:
                        f.write(updated_content)
                    
                    print(f"\nSuccessfully updated spreadsheet ID in {auth_file}")
                    
                except Exception as e:
                    print(f"\nError updating spreadsheet ID: {str(e)}")
            else:
                print(f"\nCould not find {auth_file} to update spreadsheet ID")
        
        print("\nSetup complete! The application is now ready to use OAuth authentication.")
        return 0
    
    return 1

if __name__ == "__main__":
    sys.exit(main()) 