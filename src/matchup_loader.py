from typing import List
import os
import sys

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.champion_matchup import ChampionMatchup
from src.data.google_sheets_manager import GoogleSheetsManager
from src.logger import logger
import asyncio

class MatchupLoader:
    def __init__(self):
        """Initialize the MatchupLoader with a GoogleSheetsManager instance."""
        self.sheets_manager = GoogleSheetsManager(os.getenv('SHEET_ID'))
    
    async def load_matchups(self) -> List[ChampionMatchup]:
        """Load all champion matchups from the Google Sheet."""
        try:
            matchups = []
            champions = self.sheets_manager.get_all_champions()
            
            for champion in champions:
                try:
                    # Use create_gameplay_dict to parse the text into sections
                    gameplay_dict = self.sheets_manager.create_gameplay_dict(champion)
                    logger.debug(f"Parsed sections for {champion}: {', '.join([k for k, v in gameplay_dict.items() if v])}")
                    print(gameplay_dict)
                    runes = ''
                    summoner_spell = ''
                    
                    # Create the ChampionMatchup object
                    matchup = ChampionMatchup(
                        champion_name=champion,
                        matchup_difficulty=self.sheets_manager.get_matchup_difficulty(champion),
                        runes=runes,
                        summoner_spell=summoner_spell,
                        matchup_overview=self.sheets_manager.get_matchup_tldr(champion),
                        early_game=gameplay_dict['early_game'],
                        how_to_trade=gameplay_dict['how_to_trade'],
                        what_to_watch_out_for=gameplay_dict['what_to_watch_out_for'],
                        tips=gameplay_dict['tips']
                    )
                    
                    matchups.append(matchup)
                    logger.info(f"Loaded matchup data for {champion}")
                    
                except Exception as e:
                    logger.error(f"Error loading matchup for {champion}: {str(e)}")
                    continue
            
            logger.info(f"Successfully loaded {len(matchups)} matchups")
            return matchups
            
        except Exception as e:
            logger.error(f"Error loading matchups: {str(e)}")
            return []

async def test_matchup_loader():
    """Test function to demonstrate the usage of MatchupLoader."""
    try:
        loader = MatchupLoader()
        print("Loading matchups...")
        matchups = await loader.load_matchups()
        
        print(f"\nLoaded {len(matchups)} matchups")
        
        # Test with a specific champion
        test_champion = "Aatrox"
        print(f"\nLooking for matchup data for {test_champion}")
        
        for matchup in matchups:
            if matchup.champion_name.lower() == test_champion.lower():
                print(f"\nFound matchup for {test_champion}:")
                print(f"Champion name: {matchup.champion_name}")
                print(f"Matchup Difficulty: {matchup.matchup_difficulty}")
                print(f"Runes: {matchup.runes}")
                print(f"Summoner Spell: '{matchup.summoner_spell}'")
                print(f"Matchup Overview: '{matchup.matchup_overview}'")
                print(f"Early Game: '{matchup.early_game}'")
                print(f"How to Trade: '{matchup.how_to_trade}'")
                print(f"What to Watch Out For: '{matchup.what_to_watch_out_for}'")
                print(f"Tips: '{matchup.tips}'")
                break
        else:
            print(f"No matchup data found for {test_champion}")
                
    except Exception as e:
        logger.error(f"Error in test_matchup_loader: {str(e)}", exc_info=True)
        print(f"Error in test_matchup_loader: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_matchup_loader())
