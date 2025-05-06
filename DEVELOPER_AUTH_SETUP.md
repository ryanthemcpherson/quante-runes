# Setting Up OAuth for Urgot Matchup Helper

This guide is for developers who need to set up the OAuth credentials for the Urgot Matchup Helper application.

## Why OAuth?

The application needs to access a specific Google Sheet containing matchup data. We use OAuth 2.0 to:

1. Allow users to authenticate with their own Google accounts
2. Verify they have access to the specific sheet containing matchup data
3. Only request read-only access to Google Sheets and Drive APIs

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click on the project dropdown at the top of the page.
3. Click "New Project" and give it a name (e.g., "Urgot Matchup Helper").
4. Click "Create" to set up the project.
5. Wait for the project to be created (this might take a few moments).

## Step 2: Enable Required APIs

1. In the Google Cloud Console, select your new project.
2. From the left sidebar, navigate to "APIs & Services" > "Library".
3. Search for and enable the following APIs:
   - Google Sheets API
   - Google Drive API
4. For each API, click on it, then click the "Enable" button.

## Step 3: Configure the OAuth Consent Screen

1. In the Google Cloud Console, navigate to "APIs & Services" > "OAuth consent screen".
2. Select "External" as the user type (unless you have a Google Workspace organization).
3. Fill in the required fields:
   - App name: "Urgot Matchup Helper"
   - User support email: Your email address
   - Developer contact information: Your email address
4. Click "Save and Continue"
5. For scopes, add:
   - `.../auth/spreadsheets.readonly`
   - `.../auth/drive.readonly`
6. Click "Save and Continue"
7. Add your own email address as a test user (and emails of any other testers).
8. Click "Save and Continue", then "Back to Dashboard"

## Step 4: Create OAuth Client ID

1. In the Google Cloud Console, navigate to "APIs & Services" > "Credentials".
2. Click "Create Credentials" and select "OAuth client ID".
3. Application type: "Desktop app"
4. Name: "Urgot Matchup Helper Desktop"
5. Click "Create"
6. Download the JSON file by clicking "Download JSON"
7. Rename the downloaded file to `client_secrets.json`
8. Place this file in the root directory of the application

## Step 5: Sharing the Google Sheet

1. Open the Google Sheet containing the matchup data
2. Click "Share" in the top-right corner
3. Add the email addresses of users who should have access
4. Make sure they have at least "Viewer" permission
5. Click "Done"

## Step 6: Packaging the Application

When distributing the application:

1. Include the `client_secrets.json` file in the package
2. Make sure the `TARGET_SPREADSHEET_ID` in `src/auth/google_auth.py` is set to the correct spreadsheet ID
3. Inform users they will need to authorize the application with their Google account on first use

## Important Notes for Development

- During development and testing, the app will be in "Testing" mode, meaning only the test users you added can authenticate
- You can apply for verification to remove the "unverified app" warning, but this is typically not necessary for internal/limited-use applications
- The `client_secrets.json` file should NEVER be committed to version control (add it to `.gitignore`)
- The spreadsheet ID is hardcoded in `src/auth/google_auth.py` - update this if you change sheets 