import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googleapiclient.discovery
from dotenv import load_dotenv
from logger import logger
from exceptions import GoogleSheetsError

class GoogleSheetsManager:
    def __init__(self):
        self.sheet_service = None
        self.setup_google_sheets()

    def setup_google_sheets(self):
        """Initialize Google Sheets API connection"""
        load_dotenv()
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        creds = None
        
        try:
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            
            self.sheet_service = googleapiclient.discovery.build('sheets', 'v4', credentials=creds)
            logger.info("Successfully connected to Google Sheets")
        except Exception as e:
            logger.error(f"Failed to setup Google Sheets: {str(e)}", exc_info=True)
            raise GoogleSheetsError(f"Failed to setup Google Sheets: {str(e)}")

    async def get_matchup_tips(self, champion):
        """Get matchup tips from Google Sheet"""
        try:
            sheet_id = os.getenv('SHEET_ID')
            range_name = os.getenv('SHEET_RANGE', 'Matchups!B2:E')
            
            logger.debug(f"Fetching data from sheet {sheet_id} with range {range_name}")
            result = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            logger.debug(f"Retrieved {len(values)} rows from sheet")
            
            # Get the starting row number from the range
            start_row = int(range_name.split('!')[1].split(':')[0][1:])
            
            sheet_champions = [row[0].strip() for row in values if row and row[0]]
            logger.debug(f"Champion names in sheet: {sheet_champions}")
            logger.debug(f"Looking up champion: '{champion}' (stripped: '{champion.strip()}')")
            
            # Log the full row data with cell references for debugging
            for i, row in enumerate(values, start=start_row):
                if row and row[0]:
                    logger.debug(f"Row {i} (B{i}:E{i}):")
                    logger.debug(f"  B{i}: Champion='{row[0]}'")
                    logger.debug(f"  C{i}: Difficulty='{row[1] if len(row) > 1 else 'N/A'}'")
                    logger.debug(f"  D{i}: Summary='{row[2] if len(row) > 2 else 'N/A'}'")
                    logger.debug(f"  E{i}: Details='{row[3] if len(row) > 3 else 'N/A'}'")
            
            for i, row in enumerate(values, start=start_row):
                if row and row[0]:
                    champion_name = row[0].strip()
                    logger.debug(f"Comparing '{champion_name}' (B{i}) with '{champion}' (stripped: '{champion.strip()}')")
                    if champion_name.strip().lower() == champion.strip().lower():
                        # Get raw difficulty text
                        difficulty = row[1].strip() if len(row) > 1 and row[1].strip() else "Unknown"
                        summary = row[2] if len(row) > 2 else "No summary available"
                        details = row[3] if len(row) > 3 else "No detailed tips available"
                        logger.debug(f"Found match for {champion} in row {i}!")
                        logger.debug(f"  B{i}: Champion='{champion_name}'")
                        logger.debug(f"  C{i}: Difficulty='{difficulty}'")
                        logger.debug(f"  D{i}: Summary='{summary}'")
                        logger.debug(f"  E{i}: Details='{details}'")
                        return f"Difficulty: {difficulty}\n\nQuick Summary:\n{summary}\n\nDetailed Guide:\n{details}"
            
            logger.warning(f"No matchup information found for {champion}")
            logger.debug(f"Available champions: {', '.join(sheet_champions)}")
            return f"No matchup information found for {champion}"
        except Exception as e:
            logger.error(f"Error getting matchup tips for {champion}: {str(e)}", exc_info=True)
            raise GoogleSheetsError(f"Failed to get matchup tips: {str(e)}")

    def get_all_champions(self):
        """Get all champions from the Google Sheet"""
        try:
            sheet_id = os.getenv('SHEET_ID')
            range_name = os.getenv('SHEET_RANGE', 'Matchups!B3:E')
            
            result = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            champions = []
            
            for row in values:
                if row and row[0]:
                    champion = row[0].strip()
                    if champion and champion.lower() != "champion":
                        champions.append(champion)
            
            return sorted(champions)
        except Exception as e:
            logger.error(f"Error getting all champions: {str(e)}", exc_info=True)
            raise GoogleSheetsError(f"Failed to get all champions: {str(e)}") 