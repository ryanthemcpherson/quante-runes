from dataclasses import dataclass

@dataclass
class ChampionMatchup:
    """Represents a champion matchup with all relevant information for counterplay."""
    
    champion_name: str
    matchup_difficulty: str
    runes: str  # List of rune names to take against this champion
    summoner_spell: str  # Recommended summoner spell, Ignite or Teleport
    matchup_overview: str  # Brief overview of the matchup
    early_game: str
    how_to_trade: str
    what_to_watch_out_for: str
    tips: str
    rune_image_url: str = ""  # URL for the rune image
    summoner_spell_image_url: str = ""  # URL for the summoner spell image
    
    @property
    def image_url(self) -> str:
        """Get the Data Dragon CDN URL for the champion's image."""
        # Convert champion name to the format used in URLs (e.g., "Aatrox" -> "Aatrox")
        # Handle special cases for champion names with spaces or other characters
        formatted_name = self.champion_name.strip()
        
        # Make sure the name is in proper case
        formatted_name = formatted_name.title()
        
        # Handle special cases
        if " " in formatted_name:
            # Remove spaces for champions like "Aurelion Sol" -> "AurelionSol"
            formatted_name = formatted_name.replace(" ", "")
        
        # Handle apostrophes for champions like "Kai'Sa" -> "Kaisa"
        formatted_name = formatted_name.replace("'", "")
        
        # Handle dots for champions like "Dr. Mundo" -> "DrMundo"
        formatted_name = formatted_name.replace(".", "")
        
        # Handle periods for champions like "Rek'Sai" -> "RekSai"
        formatted_name = formatted_name.replace("'", "")
        
        # Special case mappings for champions with unique naming
        special_cases = {
            "Wukong": "MonkeyKing",
            "Renata Glasc": "Renata",
            "Nunu & Willump": "Nunu"
        }
        
        if formatted_name in special_cases:
            formatted_name = special_cases[formatted_name]
            
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
            "tips": self.tips,
            "rune_image_url": self.rune_image_url,
            "summoner_spell_image_url": self.summoner_spell_image_url
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
            tips=data["tips"],
            rune_image_url=data["rune_image_url"],
            summoner_spell_image_url=data["summoner_spell_image_url"]
        ) 