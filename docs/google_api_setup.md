# Setting Up Google API Credentials

This guide walks you through the process of creating credentials for the Urgot Matchup Helper application to access Google Sheets data.

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

## Step 3: Create OAuth 2.0 Credentials

1. In the Google Cloud Console, navigate to "APIs & Services" > "Credentials".
2. Click "Create Credentials" and select "OAuth client ID".
3. If prompted to configure the OAuth consent screen:
   - Click "Configure Consent Screen".
   - Choose "External" as the user type (this is fine for personal use).
   - Fill in the required fields (App name, user support email, developer contact information).
   - For scopes, no additional scopes are needed at this step.
   - Add your own email address as a test user.
   - Complete the setup process.
4. Return to the "Create OAuth client ID" screen:
   - Select "Desktop app" as the Application type.
   - Give your client a name (e.g., "Urgot Matchup Helper Desktop Client").
   - Click "Create".
5. A popup will appear with your client ID and client secret. Click "Download JSON".
6. Save the downloaded file as `credentials.json` in the same directory as the Urgot Matchup Helper application.

## Step 4: Use the Credentials in Urgot Matchup Helper

1. Place the `credentials.json` file in the same directory as the application executable.
2. When you start the app for the first time, it will prompt you to authorize access:
   - A browser window will open asking you to sign in to your Google account.
   - You might see a warning that the app is "not verified" - this is normal for personal projects.
   - Click "Continue" and grant the requested permissions to access Google Sheets data.
3. After successful authorization, the application will store a token file and you won't need to authorize again unless the token expires.

## Troubleshooting

### "This app isn't verified" Warning

When using the app for the first time, you might see a warning that says "This app isn't verified". This is normal for personal projects that aren't published for wide use.

To proceed:
1. Click "Advanced" at the bottom-left of the warning screen.
2. Click "Go to [Your Project Name] (unsafe)".
3. Continue with the authorization process.

### Invalid Credentials

If you encounter errors related to invalid credentials:
1. Delete the `token.json` file if it exists.
2. Ensure your `credentials.json` file is correctly placed in the application directory.
3. Restart the application and go through the authorization process again.

### API Quota Limits

Google APIs have usage quotas. For personal use, these limits are quite generous and should not pose issues. If you encounter quota limit errors, wait a few minutes and try again.

## Security Information

- The application only requests read-only access to your Google Sheets and Drive data.
- Your authentication tokens are stored locally on your computer.
- No data is sent to any third-party servers.
- The application only accesses the specific spreadsheet containing matchup data. 