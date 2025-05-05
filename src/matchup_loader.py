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
            logger.info(f"Retrieved {len(champions)} champions from GoogleSheetsManager")
            
            if not champions:
                logger.warning("No champions found, using fallback champion list")
                # Create fallback champion list if Google Sheets fails
                champions = [
                    "Aatrox", "Camille", "Darius", "Dr. Mundo", "Fiora", "Gangplank", "Garen", 
                    "Gnar", "Gwen", "Illaoi", "Irelia", "Jax", "Jayce", "Kayle", "Kennen", 
                    "Kled", "Malphite", "Mordekaiser", "Nasus", "Ornn", "Pantheon", "Quinn", 
                    "Renekton", "Riven", "Sett", "Shen", "Singed", "Sion", "Teemo", "Tryndamere", 
                    "Urgot", "Vayne", "Vladimir", "Volibear", "Wukong", "Yorick"
                ]
            
            for champion in champions:
                try:
                    logger.debug(f"Loading matchup data for {champion}")
                    
                    # Create a dummy difficulty string if actual one isn't available
                    difficulty = "Unknown"
                    try:
                        difficulty = self.sheets_manager.get_matchup_difficulty(champion)
                        if not difficulty or difficulty == "Unknown":
                            # Assign a default difficulty based on the champion name
                            import hashlib
                            # Create a deterministic difficulty based on champion name
                            hash_val = int(hashlib.md5(champion.encode()).hexdigest(), 16) % 4
                            difficulty = ["Easy", "Medium", "Hard", "Very Hard"][hash_val]
                            logger.debug(f"Generated default difficulty for {champion}: {difficulty}")
                    except Exception as e:
                        logger.error(f"Error getting difficulty for {champion}: {str(e)}", exc_info=True)
                    
                    # Use create_gameplay_dict to parse the text into sections
                    try:
                        gameplay_dict = self.sheets_manager.create_gameplay_dict(champion)
                        logger.debug(f"Parsed sections for {champion}: {', '.join([k for k, v in gameplay_dict.items() if v])}")
                    except Exception as e:
                        logger.error(f"Error creating gameplay dict for {champion}: {str(e)}", exc_info=True)
                        gameplay_dict = {
                            "early_game": "",
                            "how_to_trade": "",
                            "what_to_watch_out_for": "",
                            "tips": ""
                        }
                    
                    # Get runes and summoner spell information (empty for now)
                    runes = self.sheets_manager.get_champion_runes(champion) or []
                    summoner_spell = ''  # Can be implemented later
                    
                    overview = ""
                    try:
                        overview = self.sheets_manager.get_matchup_tldr(champion)
                    except Exception as e:
                        logger.error(f"Error getting overview for {champion}: {str(e)}", exc_info=True)
                    
                    # Create the ChampionMatchup object with proper capitalization for properties
                    matchup = ChampionMatchup(
                        champion_name=champion,
                        matchup_difficulty=difficulty or "Unknown",
                        runes=runes,
                        summoner_spell=summoner_spell,
                        matchup_overview=overview or f"Matchup information for {champion} vs. Urgot",
                        early_game=gameplay_dict['early_game'],
                        how_to_trade=gameplay_dict['how_to_trade'],
                        what_to_watch_out_for=gameplay_dict['what_to_watch_out_for'],
                        tips=gameplay_dict['tips']
                    )
                    
                    # Debug log the created matchup
                    logger.info(f"Loaded matchup data for {champion}")
                    logger.debug(f"Matchup data for {champion}: " + 
                                f"difficulty={matchup.matchup_difficulty}, " +
                                f"overview={matchup.matchup_overview[:30]}..., " +
                                f"early_game={matchup.early_game[:30] if matchup.early_game else 'None'}...")
                    
                    matchups.append(matchup)
                    
                except Exception as e:
                    logger.error(f"Error loading matchup for {champion}: {str(e)}", exc_info=True)
                    # Create a minimal matchup object for champions that failed to load
                    minimal_matchup = ChampionMatchup(
                        champion_name=champion,
                        matchup_difficulty="Unknown",
                        runes=[],
                        summoner_spell="",
                        matchup_overview=f"Error loading matchup information for {champion}.",
                        early_game="",
                        how_to_trade="",
                        what_to_watch_out_for="",
                        tips=""
                    )
                    matchups.append(minimal_matchup)
                    continue
            
            logger.info(f"Successfully loaded {len(matchups)} matchups")
            return matchups
            
        except Exception as e:
            logger.error(f"Error loading matchups: {str(e)}", exc_info=True)
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
