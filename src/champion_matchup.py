from dataclasses import dataclass
from typing import List

@dataclass
class ChampionMatchup:
    """Represents a champion matchup with all relevant information for counterplay."""
    
    champion_name: str
    matchup_difficulty: str
    runes: List[str]  # List of rune names to take against this champion
    summoner_spell: str  # Recommended summoner spell, Ignite or Teleport
    matchup_overview: str  # Brief overview of the matchup
    early_game: str
    how_to_trade: str
    what_to_watch_out_for: str
    tips: str
    
    @property
    def image_url(self) -> str:
        """Get the Data Dragon CDN URL for the champion's image."""
        # Convert champion name to the format used in URLs (e.g., "Aatrox" -> "Aatrox")
        formatted_name = self.champion_name
        return f"https://ddragon.leagueoflegends.com/cdn/15.9.1/img/champion/{formatted_name}.png"
            
    def to_dict(self) -> dict:
        """Convert the matchup information to a dictionary."""
        return {
            "champion_name": self.champion_name,
            "matchup_difficulty": self.matchup_difficulty,
            "runes": self.runes,
            "summoner_spell": self.summoner_spell,
            "matchup_overview": self.matchup_overview,
            "early_game": self.early_game,
            "how_to_trade": self.how_to_trade,
            "what_to_watch_out_for": self.what_to_watch_out_for,
            "tips": self.tips
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChampionMatchup':
        """Create a ChampionMatchup instance from a dictionary."""
        return cls(
            champion_name=data["champion_name"],
            matchup_difficulty=data["matchup_difficulty"],
            runes=data["runes"],
            summoner_spell=data["summoner_spell"],
            matchup_overview=data["matchup_overview"],
            early_game=data["early_game"],
            how_to_trade=data["how_to_trade"],
            what_to_watch_out_for=data["what_to_watch_out_for"],
            tips=data["tips"]
        ) 