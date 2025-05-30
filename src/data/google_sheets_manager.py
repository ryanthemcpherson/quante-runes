import os
import sys
from typing import List
from googleapiclient.errors import HttpError
import googleapiclient.discovery
import time

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data import image_hack
from src.logger import logger
from src.exceptions import GoogleSheetsError
from src.auth import google_auth

# Debug logging
logger.info("Starting script")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Credentials file exists: {os.path.exists('credentials.json')}")
logger.info(f"Token file exists: {os.path.exists('token.json')}")

# Rate limiting constants
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds
MAX_RETRY_DELAY = 32  # seconds
RATE_LIMIT_DELAY = 1  # seconds between requests

class GoogleSheetsManager:
    def __init__(self, spreadsheet_id: str = None):
        """Initialize the Google Sheets manager with the spreadsheet ID."""
        # Use a default spreadsheet ID if none provided
        self.spreadsheet_id = spreadsheet_id or "1wcrN6SRX1EsEce4s2HL8GBIa1CjPVG5L32mW9ml7K3s"
        logger.info(f"Initializing GoogleSheetsManager with spreadsheet ID: {self.spreadsheet_id}")
        
        self.creds = self._get_credentials()
        self.sheets_service = self._get_sheets_service()
        self.drive_service = self._get_drive_service()
        self.last_request_time = 0
        
        # Cache for storing sheet data
        self.matchups_data = None
        self.champions_list = None
        
        self.image_hack_data = image_hack.get_champion_urls()
        
        # Load sheet data on initialization
        self._load_sheets_data()
        
    def _load_sheets_data(self):
        """Load all relevant data from the Google Sheet at once to minimize API calls."""
        try:
            logger.info("Loading all matchup data from Google Sheets...")
            # Load the entire Matchups sheet
            result = self._execute_with_retry(
                self.sheets_service.spreadsheets().values().get,
                spreadsheetId=self.spreadsheet_id,
                range='Matchups!A1:Z'  # Load all rows in the Matchups sheet
            )
            
            self.matchups_data = result.get('values', [])
            logger.info(f"Successfully loaded data for {len(self.matchups_data)} rows")
            
            # Log the headers to understand the column structure
            if self.matchups_data and len(self.matchups_data) > 0:
                logger.debug(f"Headers: {self.matchups_data[0]}")
            
            # Extract list of champions (champions are usually in column B, index 1)
            # Skip first few rows which might be headers
            start_row = 0
            for i in range(min(10, len(self.matchups_data))):
                if len(self.matchups_data[i]) > 1 and self.matchups_data[i][1].strip().lower() in ['aatrox', 'ahri', 'akali', 'alistar']:
                    start_row = i
                    logger.debug(f"Found champion row starting at index {start_row}")
                    break
            
            self.champions_list = []
            for row in self.matchups_data[start_row:]:
                if len(row) > 1 and row[1].strip():
                    self.champions_list.append(row[1].strip())
            
            logger.info(f"Extracted {len(self.champions_list)} champion names")
            logger.debug(f"Champion examples: {', '.join(self.champions_list[:5])}")
            
            # Create a dictionary of champion name to row index for faster lookups
            self.champion_to_row = {}
            for idx, row in enumerate(self.matchups_data[start_row:], start=start_row):
                if len(row) > 1 and row[1].strip():
                    self.champion_to_row[row[1].strip().lower()] = idx
            
            logger.debug(f"Created mapping for {len(self.champion_to_row)} champions")
                
        except Exception as e:
            logger.error(f"Error loading sheet data: {str(e)}", exc_info=True)
            # Initialize empty data structures if loading fails
            self.matchups_data = []
            self.champions_list = []
            self.champion_to_row = {}

    def refresh_data(self):
        """Refresh all data from the Google Sheet."""
        self._load_sheets_data()

    def _get_credentials(self):
        """Get credentials for both Sheets and Drive APIs using the auth module."""
        creds = google_auth.get_credentials()
        if not creds:
            logger.error("Failed to obtain Google credentials")
            # This will likely cause API calls to fail, but we can continue
            # and let the API call handlers deal with the errors
        return creds

    def _get_sheets_service(self):
        """Get the Google Sheets service."""
        return googleapiclient.discovery.build('sheets', 'v4', credentials=self.creds)

    def _get_drive_service(self):
        """Get the Google Drive service."""
        return googleapiclient.discovery.build('drive', 'v3', credentials=self.creds)

    def _rate_limit(self):
        """Implement rate limiting to avoid hitting API limits."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < RATE_LIMIT_DELAY:
            sleep_time = RATE_LIMIT_DELAY - time_since_last_request
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _execute_with_retry(self, request_func, *args, **kwargs):
        """Execute a request with retry logic for rate limits."""
        retry_delay = INITIAL_RETRY_DELAY
        for attempt in range(MAX_RETRIES):
            try:
                self._rate_limit()
                return request_func(*args, **kwargs).execute()
            except HttpError as e:
                if e.resp.status == 429:  # Rate limit exceeded
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"Rate limit exceeded, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
                        continue
                raise GoogleSheetsError(f"Error accessing Google Sheets: {str(e)}")
            except Exception as e:
                raise GoogleSheetsError(f"Error accessing Google Sheets: {str(e)}")
    
    def get_all_champions(self) -> List[str]:
        """Get a list of all champions from the cached data."""
        if not self.champions_list:
            # If cache is empty, try to reload
            self._load_sheets_data()
            if not self.champions_list:
                logger.error("Failed to load champions list from cache")
                return []
        
        return self.champions_list

    def _find_champion_row_index(self, champion: str) -> int:
        """Find the index of the champion in the cached data."""
        champion = champion.strip().lower()
        logger.debug(f"Looking for champion '{champion}' in champion map")
        
        # Use the champion_to_row mapping for faster lookup
        if hasattr(self, 'champion_to_row') and champion in self.champion_to_row:
            row_idx = self.champion_to_row[champion]
            logger.debug(f"Found champion '{champion}' at row index {row_idx} using mapping")
            
            # Log the entire row for debugging
            if row_idx >= 0 and row_idx < len(self.matchups_data):
                row = self.matchups_data[row_idx]
                logger.debug(f"Champion '{champion}' row data: {row}")
                
            return row_idx
        
        # Fallback to linear search if mapping doesn't exist or champion not found
        logger.debug(f"Falling back to linear search for champion '{champion}' in {len(self.matchups_data)} rows")
        for idx, row in enumerate(self.matchups_data):
            if len(row) > 1:
                row_champion = row[1].strip().lower()
                if row_champion == champion:
                    logger.debug(f"Found champion '{champion}' at row index {idx}")
                    
                    # Log the entire row for debugging
                    logger.debug(f"Champion '{champion}' row data: {row}")
                    
                    return idx
        
        logger.warning(f"Champion '{champion}' not found in any row")
        return -1

    def get_champion_runes(self, champion: str) -> str:
        """Get runes for a specific champion from cached data."""
        try:
            champion = champion.strip()
            row_idx = self._find_champion_row_index(champion)
            if row_idx >= 0:
                #TODO: Implement this better, for now use image hack
                # Find champion position out of total champions
                champion_position = self.champions_list.index(champion.upper())
                # Get runes from image hack list
                
                return self.image_hack_data[champion_position][0]
            return ""
        except Exception as e:
            logger.error(f"Error getting runes for {champion}: {str(e)}")
            return ""

    def get_summoner_spells(self, champion: str) -> str:
        """Get summoner spells for a specific champion from cached data."""
        try:
            champion = champion.strip()
            row_idx = self._find_champion_row_index(champion)
            if row_idx >= 0:
                #TODO: Implement this better, for now use image hack
                # Find champion position out of total champions
                champion_position = self.champions_list.index(champion.upper())
                # Get Summoner Spells from image hack list
                
                return self.image_hack_data[champion_position][1]
            return ""
        except Exception as e:
            logger.error(f"Error getting summoner spells for {champion}: {str(e)}")
            return ""

    def get_matchup_tldr(self, champion: str) -> str:
        """Get the TL;DR for a specific matchup from column D."""
        try:
            champion = champion.strip()
            row_idx = self._find_champion_row_index(champion)
            if row_idx >= 0:
                row = self.matchups_data[row_idx]
                # If the overview is in column D (index 3)
                if len(row) > 3 and row[3]:
                    return row[3]
            return ''
        except Exception as e:
            logger.error(f"Error getting matchup TL;DR for {champion}: {str(e)}")
            return ""

    def get_matchup_gameplay(self, champion: str) -> str:
        """Get gameplay tips for a specific matchup from column F."""
        try:
            champion = champion.strip()
            row_idx = self._find_champion_row_index(champion)
            if row_idx >= 0:
                row = self.matchups_data[row_idx]
                
                # Return content from column E (index 4)
                if len(row) > 4 and row[4]:
                    return row[4]
                    
                logger.warning(f"No gameplay data in column F for {champion}")
                return ""
            
            logger.warning(f"Could not find row for champion {champion}")
            return ""
        except Exception as e:
            logger.error(f"Error getting gameplay for {champion}: {str(e)}")
            return ""

    def get_matchup_difficulty(self, champion: str) -> str:
        """Get the matchup difficulty string for the given champion from cached data."""
        try:
            champion = champion.strip()
            row_idx = self._find_champion_row_index(champion) + 2 # Offset by 2 to account for placement
            logger.debug(f"Looking for difficulty of {champion} at row index {row_idx}")
            
            if row_idx >= 0 and row_idx < len(self.matchups_data):
                row = self.matchups_data[row_idx]
                logger.debug(f"Row data for {champion}: {row}")
                # First check column C (index 2)
                if len(row) > 2 and row[2]:
                    logger.debug(f"Found difficulty in column C (index 2): {row[2]}")
                    return row[2]
            
            logger.warning(f"Invalid row index {row_idx} for champion {champion}")
            return 'Unknown'
        except Exception as e:
            logger.error(f"Error getting matchup difficulty for {champion}: {str(e)}", exc_info=True)
            return 'Unknown'

    def create_gameplay_dict(self, champion: str) -> dict:
        """Create a dictionary of gameplay sections for the given champion."""
        try:
            champion = champion.strip()
            gameplay_text = self.get_matchup_gameplay(champion)
            
            sections = {
                "early_game": "",
                "how_to_trade": "",
                "what_to_watch_out_for": "",
                "tips": ""
            }
            
            if gameplay_text:
                # Parse the gameplay text into sections
                import re
                
                # Define section markers to search for
                section_markers = [
                    r'EARLY\s*GAME:?',
                    r'HOW\s*TO\s*TRADE:?|TRADING:?',
                    r'WHAT\s*TO\s*WATCH\s*OUT\s*FOR:?|WATCH\s*OUT:?',
                    r'TIPS:?'
                ]
                
                # Combine section markers into a single pattern for splitting
                section_pattern = '|'.join(f'({marker})' for marker in section_markers)
                
                # Find all section headers in the text
                matches = list(re.finditer(section_pattern, gameplay_text, re.IGNORECASE))
                
                # Process each section
                for i, match in enumerate(matches):
                    # Get section name
                    section_text = match.group(0).strip().upper()
                    start_pos = match.end()
                    
                    # Determine section key
                    if re.search(r'EARLY', section_text, re.IGNORECASE):
                        section_key = "early_game"
                    elif re.search(r'TRADE|TRADING', section_text, re.IGNORECASE):
                        section_key = "how_to_trade"
                    elif re.search(r'WATCH', section_text, re.IGNORECASE):
                        section_key = "what_to_watch_out_for"
                    elif re.search(r'TIPS', section_text, re.IGNORECASE):
                        section_key = "tips"
                    else:
                        continue
                    
                    # Find end position (next section start or end of text)
                    if i < len(matches) - 1:
                        end_pos = matches[i + 1].start()
                    else:
                        end_pos = len(gameplay_text)
                    
                    # Extract content
                    content = gameplay_text[start_pos:end_pos].strip()
                    
                    # Clean up content
                    if content.startswith(':'):
                        content = content[1:].strip()
                    
                    sections[section_key] = content
                
                # If no sections were found, put all content in early_game
                if not any(sections.values()) and gameplay_text.strip():
                    sections["early_game"] = gameplay_text.strip()
            
            return sections
            
        except Exception as e:
            logger.error(f"Error creating gameplay dictionary for {champion}: {str(e)}", exc_info=True)
            return {
                "early_game": "",
                "how_to_trade": "",
                "what_to_watch_out_for": "",
                "tips": ""
            }

if __name__ == "__main__":
    manager = GoogleSheetsManager(os.getenv('SHEET_ID'))
    test_champion = "Aatrox"  # Change as needed
    print(f"Testing for champion: {test_champion}\n")
    difficulty = manager.get_matchup_difficulty(test_champion)
    print(f"Matchup Difficulty: {difficulty}\n")
    tldr = manager.get_matchup_tldr(test_champion)
    print(f"TL;DR: {tldr}\n")
    gameplay_dict = manager.create_gameplay_dict(test_champion)
    print(f"Gameplay Dictionary: {gameplay_dict}\n")
    
    print(f"Runes: {manager.get_champion_runes(test_champion)}")
    print(f"Summoner Spells: {manager.get_summoner_spells(test_champion)}")

    
