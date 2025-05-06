# OAuth Authentication for Urgot Matchup Helper

## Overview

Urgot Matchup Helper uses Google's OAuth 2.0 to authenticate users and securely access matchup data stored in Google Sheets. This document explains how the authentication works and provides information for both users and developers.

## For Users

### Authentication Process

When you first start the application, you'll be guided through a simple authentication process:

1. A dialog will appear explaining that you need to authenticate with Google
2. Click "Continue" to proceed with authentication
3. Your default web browser will open to Google's sign-in page
4. Sign in with your Google account that has access to the matchup spreadsheet
5. Google will ask if you want to grant the application read-only access to your Google Sheets
6. Click "Allow" to grant access
7. You'll see a confirmation page, and you can close the browser and return to the application

### Privacy Information

- The application only requests read-only access to Google Sheets data
- All authentication credentials are stored locally on your device
- No data is sent to third-party servers
- You can revoke access at any time through [Google's Security Settings](https://myaccount.google.com/permissions)

For more details, see the [Privacy Policy](./PRIVACY_POLICY.md).

### Troubleshooting

#### "This app isn't verified" Warning

You might see a warning that says "This app isn't verified" during authentication. This is normal for applications that aren't published on the Google Workspace Marketplace.

To proceed:
1. Click "Advanced" at the bottom-left of the warning screen
2. Click "Go to [App Name] (unsafe)"
3. Continue with the authentication process

#### Access Denied

If you receive an "Access Denied" error after authentication, it means your Google account doesn't have access to the required spreadsheet. Contact the application developer to request access.

#### Authentication Errors

If you encounter any other authentication errors:
1. Delete the `token.json` file from the application directory (if it exists)
2. Restart the application and try again
3. If the issue persists, contact the application developer

## For Developers

If you're a developer working on the application, see [Developer Auth Setup](./DEVELOPER_AUTH_SETUP.md) for detailed instructions on:

1. Creating a Google Cloud project
2. Configuring OAuth credentials
3. Setting up API access
4. Sharing the spreadsheet with users

You can also use the OAuth configuration generator tool:
```
python tools/generate_oauth_config.py
```

This script will guide you through creating the `client_secrets.json` file with the correct format. 