#!/usr/bin/env python
from src.data.google_sheets_manager import GoogleSheetsManager
from src.logger import logger
import os

def main():
    logger.info("Starting difficulty debugging script")
    
    # Initialize the Google Sheets manager
    manager = GoogleSheetsManager(os.getenv('SHEET_ID'))
    
    # Test champions
    test_champions = ['Aatrox', 'Darius', 'Garen', 'Riven', 'Vayne']
    
    print("\nTesting difficulty extraction for champions:")
    for champion in test_champions:
        # Get the row index for the champion
        row_idx = manager._find_champion_row_index(champion)
        
        # Get the raw row data
        row_data = "No data found" if row_idx < 0 else manager.matchups_data[row_idx]
        
        # Get the difficulty
        difficulty = manager.get_matchup_difficulty(champion)
        
        print(f"{champion}:")
        print(f"  Row index: {row_idx}")
        print(f"  Raw row data: {row_data}")
        print(f"  Difficulty: '{difficulty}'")
        print()

if __name__ == "__main__":
    main() 