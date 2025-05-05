class UrgotMatchupError(Exception):
    """Base exception class for Urgot Matchup Helper"""
    pass

class GoogleSheetsError(UrgotMatchupError):
    """Exception raised for Google Sheets related errors"""
    pass

class LeagueClientError(UrgotMatchupError):
    """Exception raised for League Client API related errors"""
    pass

class UIError(UrgotMatchupError):
    """Exception raised for UI related errors"""
    pass

class ConfigurationError(UrgotMatchupError):
    """Exception raised for configuration related errors"""
    pass 