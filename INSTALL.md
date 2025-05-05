# Installation Guide for Urgot Matchup Helper

This document provides detailed instructions for installing and setting up the Urgot Matchup Helper application.

## Prerequisites

Before installing, ensure you have the following:

1. **Python 3.8+** installed and available in your PATH
   - Verify with: `python --version` or `python3 --version`
   - Download from [python.org](https://www.python.org/downloads/) if needed

2. **Pip** (Python package manager)
   - Usually comes with Python installation
   - Verify with: `pip --version` or `pip3 --version`

3. **League of Legends Client** installed
   - This application connects to your local League client
   - Ensure the client can be run with administrator permissions (for API access)

4. **Internet connection** for Google Sheets API access

## Installation Steps

### 1. Download the Application

Choose one of these methods:

**Option A: Clone with Git**
```bash
git clone https://github.com/yourusername/urgot-matchup-helper.git
cd urgot-matchup-helper
```

**Option B: Download ZIP**
- Download the ZIP file from the repository
- Extract the contents to a location of your choice
- Open a terminal/command prompt and navigate to the extracted folder

### 2. Create a Virtual Environment (Recommended)

Creating a virtual environment keeps dependencies isolated and prevents conflicts:

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

After activation, your command prompt should show `(venv)` at the beginning.

### 3. Install Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

This will install:
- PyQt6 and related packages for the GUI
- Google API libraries for sheet access
- Async libraries for non-blocking operations
- Pulsefire for League client communication
- Other utility packages

### 4. Set up Google Sheets API

To access the matchup data from Google Sheets, you need to set up API access:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the Google Sheets API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click on it and press "Enable"

4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: Desktop application
   - Name it (e.g., "Urgot Matchup Helper")
   - Click "Create"

5. Download the credentials:
   - Download the JSON file
   - Rename it to `credentials.json`
   - Place it in the root directory of the application

6. First-time setup:
   - When you first run the application, a browser window will open
   - Log in with your Google account
   - Grant permission to access your Google Sheets
   - This will create a `token.json` file for future authentication

### 5. Configure the Application (Optional)

**Use a custom Google Sheet:**

If you want to use your own Google Sheet:
- Set the `SHEET_ID` environment variable
- Or modify the default ID in `src/data/google_sheets_manager.py`

**Environment variables:**
Create a `.env` file in the root directory with:
```
SHEET_ID=your_sheet_id_here
```

## Running the Application

After installation, run the application:

```bash
python main.py
```

The first time you run it, you'll need to authenticate with Google as described above.

## Troubleshooting Installation

### Common Installation Issues

1. **"Package not found" errors**
   - Try updating pip: `pip install --upgrade pip`
   - If behind a proxy, configure pip to use it

2. **PyQt6 installation errors**
   - On some systems, you might need additional packages:
     - Windows: Visual C++ build tools
     - Linux: `sudo apt-get install python3-pyqt6` (Ubuntu/Debian)
     - macOS: `brew install pyqt6` (Homebrew)

3. **Google authentication errors**
   - Ensure `credentials.json` is in the right location
   - Check that the Google account has access to the sheet
   - If the authentication flow doesn't complete, delete `token.json` and try again

4. **League Client connection issues**
   - Make sure the League client is running before the application
   - On Windows, try running both the client and application as Administrator

### Still Having Issues?

Check the log files for detailed error information:
- `logs/urgot_matchup_helper.log`
- `startup_log.txt`

If problems persist, submit an issue on GitHub with:
- Your operating system and Python version
- The exact error message
- Contents of your log files (with sensitive information removed)

## Updating the Application

To update to the latest version:

**If you cloned with Git:**
```bash
git pull
pip install -r requirements.txt
```

**If you downloaded ZIP:**
- Download the latest ZIP
- Extract and replace the existing files
- Run `pip install -r requirements.txt` again to update dependencies 