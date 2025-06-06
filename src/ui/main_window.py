from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QAction
from .matchup_display import MatchupDisplay
from .champion_selector import ChampionSelector
from ..core.league_client import LeagueClient
from ..data.google_sheets_manager import GoogleSheetsManager
from qasync import asyncSlot
from src.logger import logger
from src.matchup_loader import MatchupLoader
from src.champion_matchup import ChampionMatchup
from PyQt6.QtWidgets import QApplication

# Try to import LeagueClientError
try:
    from exceptions import LeagueClientError
except ImportError:
    try:
        from src.exceptions import LeagueClientError
    except ImportError:
        # Fallback class if imports fail
        class LeagueClientError(Exception):
            pass
        logger.error("Could not import LeagueClientError in main_window.py, using fallback")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Urgot Matchup Helper")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        
        # Initialize system tray
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("urgot_icon.png"))
        
        # Create tray menu
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        
        # Connect tray icon signals
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Show tray icon
        self.tray_icon.show()
        
        # Initialize variables first
        self.status_label = None
        self.champion_selector = None
        self.matchup_display = None
        self.check_timer = None
        self.update_timer = None
        self.matchups = []  # Will store loaded matchups
        self.manual_mode = False
        self.in_champion_select = False
        self.client_connected = False
        
        # Create components safely
        try:
            self.league_client = LeagueClient()
            self.client_connected = self.league_client.client_running
            logger.info(f"League client connection status: {self.client_connected}")
        except Exception as e:
            logger.error(f"Error initializing LeagueClient: {str(e)}", exc_info=True)
            self.league_client = None
            self.client_connected = False
        
        try:
            self.sheets_manager = GoogleSheetsManager()
        except Exception as e:
            logger.error(f"Error initializing GoogleSheetsManager: {str(e)}", exc_info=True)
            self.sheets_manager = None
        
        try:
            self.matchup_loader = MatchupLoader()
        except Exception as e:
            logger.error(f"Error initializing MatchupLoader: {str(e)}", exc_info=True)
            self.matchup_loader = None
        
        # Set up UI
        try:
            self.setup_ui()
        except Exception as e:
            logger.error(f"Error setting up UI: {str(e)}", exc_info=True)
            
        # Set up timers
        try:
            self.setup_timers()
        except Exception as e:
            logger.error(f"Error setting up timers: {str(e)}", exc_info=True)
        
        # Initial setup
        try:
            if self.sheets_manager:
                self.populate_champion_dropdown()
                
            if not self.client_connected:
                self.show_client_connection_message()
            else:
                self.show_waiting_message()
        except Exception as e:
            logger.error(f"Error during initial setup: {str(e)}", exc_info=True)
            # Try to display an error message
            try:
                if self.matchup_display:
                    self.matchup_display.clear_matchups()
                    self.matchup_display.add_matchup("Error", f"Initialization error: {str(e)}")
                if self.status_label:
                    self.update_status_label("ERROR DURING INITIALIZATION", is_error=True)
            except Exception:
                pass
        
    def setup_ui(self):
        """Set up the main UI components"""
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #181a1b;")
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # Add status label at the top
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("""
            background-color: #23272a;
            color: #ffffff;
            font-size: 14px;
            padding: 8px;
            border-radius: 4px;
            margin-bottom: 4px;
            qproperty-alignment: AlignCenter;
        """)
        layout.addWidget(self.status_label)
        
        # Create and add components
        self.champion_selector = ChampionSelector()
        if self.champion_selector:
            try:
                self.champion_selector.connect_selection_changed(self.on_champion_selection_changed)
            except Exception as e:
                logger.error(f"Error connecting champion selector: {str(e)}", exc_info=True)
            layout.addWidget(self.champion_selector)
        
        self.matchup_display = MatchupDisplay()
        if self.matchup_display:
            layout.addWidget(self.matchup_display)
        
        # Set initial size and position
        self.resize(1000, 1100)
        self.move(100, 100)
    
    def update_status_label(self, status_text, is_error=False):
        """Update the status label with appropriate styling"""
        if not self.status_label:
            logger.warning(f"Status label not initialized, can't set status: {status_text}")
            return
            
        try:
            if is_error:
                self.status_label.setStyleSheet("""
                    background-color: #662222;
                    color: #ffffff;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px;
                    border-radius: 4px;
                    margin-bottom: 4px;
                    qproperty-alignment: AlignCenter;
                """)
            else:
                self.status_label.setStyleSheet("""
                    background-color: #23272a;
                    color: #ffffff;
                    font-size: 14px;
                    padding: 8px;
                    border-radius: 4px;
                    margin-bottom: 4px;
                    qproperty-alignment: AlignCenter;
                """)
            self.status_label.setText(status_text)
        except Exception as e:
            logger.error(f"Error updating status label: {str(e)}", exc_info=True)
        
    def setup_timers(self):
        """Set up the timers for periodic updates"""
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_champion_select)
        self.check_timer.start(2000)
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_matchups)
        self.update_timer.start(5000)  # Start the update timer with a 5-second interval
        
    @asyncSlot()
    async def check_champion_select(self):
        """Check if we're in champion select"""
        if self.manual_mode:
            return
            
        # Check if league_client exists
        if not self.league_client:
            logger.warning("Cannot check champion select: league_client not initialized")
            if self.status_label:
                self.update_status_label("League Client Not Available", is_error=True)
            return
            
        try:
            # Try to get the gameflow phase
            phase = await self.league_client.get_gameflow_phase()
            
            # If we got here, we're connected to the client
            if not self.client_connected:
                self.client_connected = True
                logger.info("Connected to League Client")
                self.update_status_label("Connected to League Client")
                
            self.setWindowTitle(f"Urgot Matchup Helper - State: {phase if phase else 'Unknown'}")
            
            if phase == "ChampSelect":
                self.in_champion_select = True
                self.show()
                self.raise_()
                self.activateWindow()
                self.update_timer.start(5000)
                self.update_status_label("Champion Select Active")
                await self.update_matchups()
            else:
                self.in_champion_select = False
                if self.update_timer:
                    self.update_timer.stop()
                self.update_status_label(f"Current State: {phase if phase else 'Unknown'}")
                self.show_waiting_message()
        except LeagueClientError as e:
            if "League Client is not running" in str(e):
                # Specific handling for League Client not running
                if self.client_connected:
                    self.client_connected = False
                    logger.warning("Lost connection to League Client")
                self.show_client_connection_message()
            else:
                # Other League Client errors
                logger.error(f"League Client error: {str(e)}", exc_info=True)
                self.update_status_label(f"League Client Error: {str(e)}", is_error=True)
                self.show_waiting_message()
            self.in_champion_select = False
            if self.update_timer:
                self.update_timer.stop()
        except Exception as e:
            # General error handling
            logger.error(f"Error checking champion select: {str(e)}", exc_info=True)
            self.in_champion_select = False
            if self.update_timer:
                self.update_timer.stop()
            self.update_status_label(f"Error: {str(e)}", is_error=True)
            self.show_waiting_message()

    def show_waiting_message(self):
        """Show the waiting message in the matchup display"""
        if not self.matchup_display:
            logger.error("Cannot show waiting message: matchup_display not initialized")
            return
            
        try:
            self.matchup_display.clear_matchups()
            self.matchup_display.add_matchup("Waiting for enemy champions...", 
                                          "The app will update when champion select starts.")
            self.setWindowTitle("Urgot Matchup Helper - Waiting for Champion Select")
            if self.status_label:
                self.update_status_label("Waiting for Champion Select")
        except Exception as e:
            logger.error(f"Error showing waiting message: {str(e)}", exc_info=True)
        
    def show_client_connection_message(self):
        """Show message when waiting for League Client to start"""
        if not self.matchup_display:
            logger.error("Cannot show client connection message: matchup_display not initialized")
            return
            
        try:
            self.matchup_display.clear_matchups()
            self.matchup_display.add_matchup(
                "Waiting for League Client...", 
                "Please start the League of Legends client. This app will automatically connect when the client starts."
            )
            self.setWindowTitle("Urgot Matchup Helper - Waiting for League Client")
            if self.status_label:
                self.update_status_label("WAITING FOR LEAGUE CLIENT CONNECTION", is_error=True)
        except Exception as e:
            logger.error(f"Error showing client connection message: {str(e)}", exc_info=True)

    @asyncSlot()
    async def update_matchups(self):
        """Update the displayed matchup information"""
        try:
            # Ensure matchups are loaded
            if not self.matchups:
                logger.info("Loading matchups for the first time in update_matchups")
                self.matchups = await self.matchup_loader.load_matchups()
                # Populate the dropdown with the loaded matchups
                self.populate_champion_dropdown()
                
            logger.info("Fetching enemy champions from League client")
            enemy_champions = await self.league_client.get_enemy_champions()
            
            logger.info("Clearing previous matchups display")
            self.matchup_display.clear_matchups()
            
            if not enemy_champions:
                logger.info("No enemy champions detected")
                if self.in_champion_select:
                    logger.info("In champion select but no champions - showing ban suggestions")
                    self.show_ban_suggestions()
                else:
                    logger.info("Not in champion select - showing waiting message")
                    self.show_waiting_message()
                return
                
            logger.info(f"Processing {len(enemy_champions)} enemy champions: {', '.join(enemy_champions)}")
            
            # Create a crash detection file to help identify where crashes happen
            with open("matchup_processing.log", "a") as f:
                f.write(f"Starting to process {len(enemy_champions)} champions: {', '.join(enemy_champions)}\n")
            
            for i, champion in enumerate(enemy_champions):
                try:
                    # Log processing of each champion
                    logger.info(f"Processing champion {i+1}/{len(enemy_champions)}: {champion}")
                    with open("matchup_processing.log", "a") as f:
                        f.write(f"Processing champion {i+1}/{len(enemy_champions)}: {champion}\n")
                    
                    matchup_info = self.find_matchup_by_name(champion)
                    if matchup_info:
                        logger.info(f"Found matchup info for {champion}")
                        # Pass the matchup object directly to the display
                        try:
                            logger.debug(f"Adding matchup to display: {champion}")
                            self.matchup_display.add_matchup(champion, matchup_info)
                            logger.info(f"Successfully added matchup for {champion}")
                            with open("matchup_processing.log", "a") as f:
                                f.write(f"Successfully added matchup for {champion}\n")
                        except Exception as display_e:
                            logger.error(f"Error adding matchup display for {champion}: {str(display_e)}", exc_info=True)
                            with open("matchup_processing.log", "a") as f:
                                f.write(f"ERROR adding matchup for {champion}: {str(display_e)}\n")
                    else:
                        logger.warning(f"No matchup information found for {champion}")
                        try:
                            self.matchup_display.add_matchup(champion, f"No matchup information found for {champion}.")
                            logger.info(f"Added placeholder for {champion}")
                        except Exception as display_e:
                            logger.error(f"Error adding placeholder for {champion}: {str(display_e)}", exc_info=True)
                except Exception as champ_e:
                    logger.error(f"Error processing champion {champion}: {str(champ_e)}", exc_info=True)
                    with open("matchup_processing.log", "a") as f:
                        f.write(f"ERROR processing champion {champion}: {str(champ_e)}\n")
            
            with open("matchup_processing.log", "a") as f:
                f.write("Finished processing all champions\n")
            logger.info("Successfully processed all champions")
                    
        except LeagueClientError as e:
            if "League Client is not running" in str(e):
                self.client_connected = False
                self.show_client_connection_message()
            else:
                logger.error(f"League Client error: {str(e)}", exc_info=True)
                self.matchup_display.clear_matchups()
                self.matchup_display.add_matchup("Error", f"Unable to fetch matchup information: {str(e)}")
                self.update_status_label(f"League Client Error: {str(e)}", is_error=True)
        except Exception as e:
            logger.error(f"Error updating matchups: {str(e)}", exc_info=True)
            with open("matchup_processing.log", "a") as f:
                f.write(f"CRITICAL ERROR in update_matchups: {str(e)}\n")
            self.matchup_display.clear_matchups()
            self.matchup_display.add_matchup("Error", f"Unable to fetch matchup information: {str(e)}")
            self.update_status_label(f"Error: {str(e)}", is_error=True)

    def format_matchup_tips(self, matchup: ChampionMatchup) -> str:
        """Format the matchup information as a string for display (legacy method, kept for compatibility)"""
        sections = []
        
        # Add matchup overview if available
        if matchup.matchup_overview:
            sections.append(f"Matchup Overview: {matchup.matchup_overview}")
            
        # Add Early Game section if available
        if matchup.Early_Game:
            sections.append(f"EARLY GAME: {matchup.Early_Game}")
            
        # Add How to Trade section if available
        if matchup.How_to_Trade:
            sections.append(f"HOW TO TRADE: {matchup.How_to_Trade}")
            
        # Add What to Watch Out For section if available
        if matchup.What_to_Watch_Out_For:
            sections.append(f"WHAT TO WATCH OUT FOR: {matchup.What_to_Watch_Out_For}")
            
        # Add Tips section if available
        if matchup.Tips:
            sections.append(f"TIPS: {matchup.Tips}")
            
        return "\n\n".join(sections)

    def find_matchup_by_name(self, champion_name: str) -> ChampionMatchup:
        """Find a matchup by champion name"""
        champion_name = champion_name.strip().lower()
        for matchup in self.matchups:
            if matchup.champion_name.strip().lower() == champion_name:
                return matchup
        return None

    def show_ban_suggestions(self):
        """Display ban suggestions in the matchup display"""
        self.matchup_display.clear_matchups()
        ban_list = [
            "Rumble", "Ambessa", "Vayne", "Mordekaiser", "Olaf",
            "Illaoi", "Gnar", "Jayce", "K'Sante"]
        
        for ban in ban_list:
            self.matchup_display.add_matchup(ban, "Recommended ban")

    @asyncSlot()
    async def on_champion_selection_changed(self):
        """Handle champion selection change in dropdown"""
        logger.debug("Champion selection changed")
        # Force garbage collection to help with memory management
        import gc
        
        try:
            # Stop the timers before processing to prevent concurrent updates
            self.check_timer.stop()
            self.update_timer.stop()
            
            # Enable manual mode
            self.manual_mode = True
            
            # Process pending events to ensure UI is responsive
            QApplication.processEvents()
            
            # Explicitly clear previous matchups before loading new ones
            # This ensures resources are properly released
            if self.matchup_display:
                self.matchup_display.clear_matchups()
                
            # Process events again to ensure cleanup completes
            QApplication.processEvents()
            
            # Force garbage collection
            gc.collect()
            
            # Now load the new matchup
            await self.test_selected_matchup()
            
            # Update the window title
            selected_champion = self.champion_selector.get_selected_champion()
            self.setWindowTitle(f"Urgot Matchup Helper - Viewing {selected_champion}")
            
            # Log successful champion change
            logger.info(f"Successfully switched to champion: {selected_champion}")
            
        except Exception as e:
            logger.error(f"Error during champion selection change: {str(e)}", exc_info=True)
            if self.matchup_display:
                self.matchup_display.clear_matchups()
                self.matchup_display.add_matchup("Error", f"Error loading champion data: {str(e)}")
                
            # Ensure window title reflects error state
            self.setWindowTitle("Urgot Matchup Helper - Error Loading Champion")
        
        # Always ensure we're processing events after a selection change
        QApplication.processEvents()

    @asyncSlot()
    async def on_test_matchup_clicked(self):
        """Backward compatibility method"""
        await self.on_champion_selection_changed()

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
            
            # Ensure matchups are loaded
            if not self.matchups:
                logger.info("Loading matchups for the first time")
                self.matchups = await self.matchup_loader.load_matchups()
                
            logger.debug(f"Requesting matchup info for champion: {champion}")
            matchup_info = self.find_matchup_by_name(champion)
            
            self.matchup_display.clear_matchups()
            if not matchup_info:
                logger.warning(f"No matchup information found for {champion}")
                # Create a basic matchup object with minimal information
                matchup_info = ChampionMatchup(
                    champion_name=champion,
                    matchup_difficulty="Unknown",
                    runes=[],
                    summoner_spell="",
                    matchup_overview="No matchup information available.",
                    early_game="",
                    how_to_trade="",
                    what_to_watch_out_for="",
                    tips=""
                )
                self.matchup_display.add_matchup(champion, matchup_info)
            else:
                # Log the matchup difficulty for debugging
                difficulty = getattr(matchup_info, 'matchup_difficulty', 'Unknown')
                logger.debug(f"Found matchup for {champion} with difficulty: {difficulty}")
                
                # Make sure difficulty is set to something other than empty string
                if hasattr(matchup_info, 'matchup_difficulty') and not matchup_info.matchup_difficulty:
                    matchup_info.matchup_difficulty = "Unknown"
                
                # Pass the matchup object directly to the display
                logger.debug(f"Adding matchup display for {champion}")
                self.matchup_display.add_matchup(champion, matchup_info)
        except Exception as e:
            logger.error(f"Error displaying matchup: {str(e)}", exc_info=True)
            self.matchup_display.clear_matchups()
            self.matchup_display.add_matchup("Error", f"Unable to fetch matchup information for {champion}: {str(e)}")

    def populate_champion_dropdown(self):
        """Populate the dropdown with champions from the Google Sheet"""
        if not self.champion_selector:
            logger.error("Cannot populate champion dropdown: champion_selector not initialized")
            return
            
        if not self.sheets_manager:
            logger.error("Cannot populate champion dropdown: sheets_manager not initialized")
            self.champion_selector.populate_champions(["Error loading champions"])
            return
            
        try:
            champions = self.sheets_manager.get_all_champions()
            if not champions or len(champions) == 0:
                logger.warning("No champions returned from sheets_manager")
                self.champion_selector.populate_champions(["No champions found"])
                return
                
            self.champion_selector.populate_champions(champions)
            logger.info(f"Populated champion dropdown with {len(champions)} champions")
        except Exception as e:
            logger.error(f"Error populating champion dropdown: {str(e)}", exc_info=True)
            self.champion_selector.populate_champions(["Error loading champions"])
            try:
                if self.status_label:
                    self.update_status_label("Error loading champion data", is_error=True)
            except Exception as e:
                logger.error(f"Error updating status label: {str(e)}", exc_info=True)
                pass 

    def closeEvent(self, event):
        """Override close event to minimize to tray instead of closing"""
        # Check if this is a quit request or just a close
        if hasattr(self, '_force_quit') and self._force_quit:
            # Allow the close event to proceed normally
            event.accept()
        else:
            # Ignore close event and minimize to tray instead
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Urgot Matchup Helper",
                "Application minimized to tray. Right-click the tray icon to show or quit.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # Single click
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
                
    def quit_application(self):
        """Properly quit the application"""
        # Stop all timers
        if self.check_timer:
            self.check_timer.stop()
        if self.update_timer:
            self.update_timer.stop()
            
        # Set flag to allow the window to close
        self._force_quit = True
        
        # Hide the tray icon
        self.tray_icon.hide()
        
        # Close the window (which will now be accepted due to _force_quit flag)
        self.close()
        
        # Quit the application
        QApplication.quit() 