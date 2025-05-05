# Urgot Matchup Helper

A tool to help Urgot players by displaying matchup information from a Quante's matchup bible during champion select.

## Setup Instructions

1. Install Python 3.8 or higher
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up Google Sheets API:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Sheets API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the credentials JSON file and save it as `credentials.json` in the project root
   
## Usage

Run the application:
```
python main.py
```

The application will:
- Connect to your Google Sheet
- Display a window that shows matchup information
- Update automatically when new champions are detected in the lobby

## Features

- Real-time matchup information display
- Easy-to-read interface
- Automatic updates from Google Sheet

## TODO:

- Replace shitty Urgot AI art with shitty urgot handmade art
- Package into some kinda executable for less tech inclined
