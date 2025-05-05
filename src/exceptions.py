class UrgotMatchupError(Exception):
    """Base exception class for Urgot Matchup Helper"""
    pass

class GoogleSheetsError(UrgotMatchupError):
    """Exception raised for Google Sheets related errors"""
    pass 