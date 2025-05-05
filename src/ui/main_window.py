from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from .matchup_display import MatchupDisplay
from .champion_selector import ChampionSelector
from ..core.league_client import LeagueClient
from ..data.google_sheets_manager import GoogleSheetsManager
from qasync import asyncSlot
from logger import logger
from exceptions import LeagueClientError, GoogleSheetsError

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Urgot Matchup Helper")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        
        # Initialize components
        self.league_client = LeagueClient()
        # self.league_client.start()  # No longer needed
        self.sheets_manager = GoogleSheetsManager()
        self.manual_mode = False
        self.in_champion_select = False
        
        # Set up UI
        self.setup_ui()
        self.setup_timers()
        
        # Initial setup
        self.populate_champion_dropdown()
        self.show_waiting_message()
        
    def setup_ui(self):
        """Set up the main UI components"""
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #181a1b;")
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # Create and add components
        self.champion_selector = ChampionSelector()
        self.champion_selector.test_button.clicked.connect(self.on_test_matchup_clicked)
        layout.addWidget(self.champion_selector)
        
        self.matchup_display = MatchupDisplay()
        layout.addWidget(self.matchup_display)
        
        # Set initial size and position
        self.resize(1000, 1100)
        self.move(100, 100)
        
    def setup_timers(self):
        """Set up the timers for periodic updates"""
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_champion_select)
        self.check_timer.start(2000)
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_matchups)
        
    @asyncSlot()
    async def check_champion_select(self):
        """Check if we're in champion select"""
        if self.manual_mode:
            return
        try:
            phase = await self.league_client.get_gameflow_phase()
            self.setWindowTitle(f"Urgot Matchup Helper - State: {phase if phase else 'Unknown'}")
            if phase == "ChampSelect":
                self.in_champion_select = True
                self.show()
                self.raise_()
                self.activateWindow()
                self.update_timer.start(5000)
                await self.update_matchups()
            else:
                self.in_champion_select = False
                self.update_timer.stop()
                self.show_waiting_message()
        except Exception as e:
            logger.error(f"Error checking champion select: {str(e)}", exc_info=True)
            self.in_champion_select = False
            self.update_timer.stop()
            self.show_waiting_message()

    def show_waiting_message(self):
        """Show the waiting message in the matchup display"""
        self.matchup_display.clear_matchups()
        self.matchup_display.add_matchup("Waiting for enemy champions...", 
                                       "The app will update when champion select starts.")
        self.setWindowTitle("Urgot Matchup Helper - Waiting for Champion Select")

    @asyncSlot()
    async def update_matchups(self):
        """Update the displayed matchup information"""
        try:
            enemy_champions = await self.league_client.get_enemy_champions()
            self.matchup_display.clear_matchups()
            
            if not enemy_champions:
                if self.in_champion_select:
                    self.show_ban_suggestions()
                else:
                    self.show_waiting_message()
                return
                
            for champion in enemy_champions:
                tips = await self.sheets_manager.get_matchup_tips(champion)
                self.matchup_display.add_matchup(champion, tips)
        except Exception as e:
            logger.error(f"Error updating matchups: {str(e)}", exc_info=True)
            self.matchup_display.clear_matchups()
            self.matchup_display.add_matchup("Error", "Unable to fetch matchup information")

    def show_ban_suggestions(self):
        """Display ban suggestions in the matchup display"""
        self.matchup_display.clear_matchups()
        ban_list = [
            "Rumble", "Ambessa", "Vayne", "Mordekaiser", "Olaf",
            "Illaoi", "Gnar", "Jayce", "K'Sante"
        ]
        
        for ban in ban_list:
            self.matchup_display.add_matchup(ban, "Recommended ban")

    @asyncSlot()
    async def on_test_matchup_clicked(self):
        """Handle the test matchup button click"""
        logger.debug("Test matchup button clicked")
        self.check_timer.stop()
        self.update_timer.stop()
        self.manual_mode = True
        await self.test_selected_matchup()
        self.setWindowTitle(f"Urgot Matchup Helper - Viewing {self.champion_selector.get_selected_champion()}")

    async def test_selected_matchup(self):
        """Display the selected matchup information"""
        try:
            champion = self.champion_selector.get_selected_champion()
            logger.debug(f"Selected champion: {champion}")
            if not champion:
                logger.warning("No champion selected")
                self.matchup_display.clear_matchups()
                self.matchup_display.add_matchup("Error", "Please select a champion first")
                return
                
            logger.debug(f"Requesting matchup tips for champion: {champion}")
            tips = await self.sheets_manager.get_matchup_tips(champion)
            logger.debug(f"Received tips for {champion}: {tips}")
            self.matchup_display.clear_matchups()
            if not tips or 'No matchup information found' in tips or 'Failed to get matchup tips' in tips:
                logger.warning(f"No matchup information found for {champion}")
                self.matchup_display.add_matchup(champion, f"Error: No matchup information found for {champion}.")
            else:
                logger.debug(f"Adding matchup display for {champion}")
                self.matchup_display.add_matchup(champion, tips)
        except Exception as e:
            logger.error(f"Error displaying matchup: {str(e)}", exc_info=True)
            self.matchup_display.clear_matchups()
            self.matchup_display.add_matchup("Error", f"Unable to fetch matchup information for {champion}: {str(e)}")

    def populate_champion_dropdown(self):
        """Populate the dropdown with champions from the Google Sheet"""
        try:
            champions = self.sheets_manager.get_all_champions()
            self.champion_selector.populate_champions(champions)
        except Exception as e:
            logger.error(f"Error populating champion dropdown: {str(e)}", exc_info=True)
            self.champion_selector.populate_champions(["Error loading champions"]) 