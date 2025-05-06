from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QFrame, QWidget, 
                          QTabWidget)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from .base_ui import BaseUI
from src.logger import logger
import tempfile
import os
from PyQt6 import sip
from PyQt6.QtWidgets import QApplication

class MatchupDisplay(BaseUI):
    def __init__(self):
        super().__init__()
        self.content_widget = None
        self.content_layout = None
        self.network_manager = QNetworkAccessManager()
        # Add a dictionary to cache images and track ongoing requests
        self.image_cache = {}
        self.active_replies = set()
        self.max_cache_size = 20  # Maximum number of images to keep in cache
        self.setup_matchup_display()

    def setup_matchup_display(self):
        """Set up the matchup display components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # Create scroll area for matchups
        scroll = self.create_scroll_area()
        scroll.setWidgetResizable(True)  # Make the scroll area resize with content
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Disable horizontal scroll
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #181a1b;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(4)
        self.content_layout.setContentsMargins(4, 4, 4, 4)
        self.content_layout.addStretch()  # Add stretch to push content to top
        scroll.setWidget(self.content_widget)
        scroll.viewport().setStyleSheet("background-color: #181a1b;")
        
        layout.addWidget(scroll)

    def clear_matchups(self):
        """Clear all matchup widgets and ensure proper resource cleanup"""
        logger.debug("Clearing matchup display")
        
        # Cancel any ongoing network requests
        self._cancel_pending_requests()
        
        # Clear widgets
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                # Explicitly clean up any QLabel with pixmaps
                self._clean_widget_resources(item.widget())
                item.widget().deleteLater()
                
        # Process events to help with immediate cleanup
        QApplication.processEvents()
        
        # Add stretch back after clearing
        self.content_layout.addStretch()
        
        logger.debug("Finished clearing matchup display")
    
    def _clean_widget_resources(self, widget):
        """Recursively clean resources in a widget and its children"""
        # Handle QLabels with pixmaps
        if isinstance(widget, QLabel) and widget.pixmap() and not widget.pixmap().isNull():
            widget.clear()
            logger.debug("Cleared pixmap from QLabel")
            
        # Recursively clean child widgets
        children = widget.findChildren(QWidget)
        for child in children:
            self._clean_widget_resources(child)
    
    def _cancel_pending_requests(self):
        """Cancel any pending network requests"""
        logger.debug(f"Cancelling {len(self.active_replies)} pending network requests")
        # Make a copy since we'll be modifying the set during iteration
        replies = list(self.active_replies)
        for reply in replies:
            try:
                if not reply.isFinished():
                    reply.abort()
                reply.deleteLater()
                self.active_replies.discard(reply)
            except Exception as e:
                logger.error(f"Error cancelling network reply: {str(e)}")
        
        logger.debug("All pending requests cancelled")

    def add_matchup(self, champion, matchup_info):
        """Add a matchup widget with improved layout"""
        logger.debug(f"Adding matchup display for {champion}")
        
        try:
            # Log matchup_info type for debugging
            logger.debug(f"Matchup info type: {type(matchup_info)}")
            
            # Main container frame
            matchup_frame = QFrame()
            matchup_frame.setStyleSheet("""
                QFrame {
                    background-color: #1e2021;
                    border-radius: 4px;
                    padding: 8px;
                    margin-bottom: 8px;
                }
            """)
            
            main_layout = QVBoxLayout(matchup_frame)
            main_layout.setSpacing(12)
            main_layout.setContentsMargins(12, 12, 12, 12)
            
            # Top section with champion info and overview
            logger.debug(f"Creating top section for {champion}")
            top_section = QFrame()
            top_section.setStyleSheet("""
                QFrame {
                    background-color: #252729;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            
            top_layout = QHBoxLayout(top_section)
            top_layout.setSpacing(12)
            
            # Champion image on the left
            logger.debug(f"Creating image frame for {champion}")
            img_frame = QFrame()
            img_frame.setFixedSize(100, 100)
            img_frame.setStyleSheet("""
                QFrame {
                    border: none;
                    border-radius: 4px;
                    background-color: transparent;
                }
            """)
            img_layout = QVBoxLayout(img_frame)
            img_layout.setContentsMargins(0, 0, 0, 0)
            
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_label.setFixedSize(90, 90)
            img_layout.addWidget(img_label, 0, Qt.AlignmentFlag.AlignCenter)
            
            # Load champion image if available
            logger.debug(f"Attempting to load image for {champion}")
            if hasattr(matchup_info, 'image_url'):
                # Debug the image URL
                try:
                    # Access image_url property directly
                    champion_name = matchup_info.champion_name if hasattr(matchup_info, 'champion_name') else champion
                    logger.debug(f"Loading image for champion: {champion_name}")
                    
                    # Access the property directly (it's a property method, not an attribute)
                    image_url = matchup_info.image_url
                    logger.debug(f"Generated image URL: {image_url}")
                    
                    self.load_image(img_label, image_url)
                except Exception as e:
                    logger.error(f"Error loading champion image: {str(e)}", exc_info=True)
                    # Create a fallback URL with the champion name
                    try:
                        formatted_name = champion.replace(" ", "").replace("'", "").replace(".", "")
                        fallback_url = f"https://ddragon.leagueoflegends.com/cdn/15.9.1/img/champion/{formatted_name}.png"
                        logger.debug(f"Using fallback image URL: {fallback_url}")
                        self.load_image(img_label, fallback_url)
                    except Exception as fallback_e:
                        logger.error(f"Fallback image loading failed: {str(fallback_e)}", exc_info=True)
            
            # Champion info on the right
            logger.debug(f"Creating info layout for {champion}")
            info_layout = QVBoxLayout()
            info_layout.setSpacing(4)
            
            # Champion name and difficulty
            name_difficulty_layout = QHBoxLayout()
            name_difficulty_layout.setSpacing(8)
            
            # Champion name
            logger.debug(f"Creating champion label for {champion}")
            champion_label = QLabel(champion)
            champion_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #ff4444;")
            name_difficulty_layout.addWidget(champion_label)
            
            # Difficulty label
            logger.debug(f"Getting difficulty for {champion}")
            difficulty = ""
            if isinstance(matchup_info, str):
                difficulty = "Unknown"
            else:
                if hasattr(matchup_info, 'matchup_difficulty') and matchup_info.matchup_difficulty:
                    difficulty = matchup_info.matchup_difficulty
                    
            logger.debug(f"Creating difficulty label with value: {difficulty}")
            difficulty_label = QLabel(difficulty)
            difficulty_label.setStyleSheet("""
                color: white;
                font-size: 18px;
                background-color: rgba(45, 45, 45, 0.7);
                border-radius: 4px;
                padding: 4px 8px;
            """)
            name_difficulty_layout.addWidget(difficulty_label)
            
            with open("matchup_processing.log", "a") as f:
                f.write(f"Processing UI for {champion} - got to summoner spell check\n")

            # Add summoner spell image if available
            logger.debug(f"Checking for summoner spell for {champion}")
            if not isinstance(matchup_info, str) and hasattr(matchup_info, 'summoner_spell') and matchup_info.summoner_spell:
                logger.debug(f"Found summoner spell image URL for {champion}: {matchup_info.summoner_spell}")
                spell_label = QLabel()
                spell_label.setFixedSize(160, 80)
                spell_label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(45, 45, 45, 0.7);
                        border-radius: 4px;
                    }
                """)
                self.load_image(spell_label, matchup_info.summoner_spell)
                name_difficulty_layout.addWidget(spell_label)
            else:
                logger.debug(f"No summoner spell image URL found for {champion}")
            
            name_difficulty_layout.addStretch()
            
            info_layout.addLayout(name_difficulty_layout)
            
            # Matchup overview
            logger.debug(f"Creating overview for {champion}")
            overview = ""
            if isinstance(matchup_info, str):
                overview = matchup_info
            else:
                if hasattr(matchup_info, 'matchup_overview') and matchup_info.matchup_overview:
                    overview = matchup_info.matchup_overview
                    logger.debug(f"Found overview: {overview[:30]}...")
            
            if overview:
                overview_label = QLabel(overview)
                overview_label.setWordWrap(True)
                overview_label.setStyleSheet("""
                    color: white;
                    font-size: 15px;
                    background-color: rgba(45, 45, 45, 0.7);
                    border-radius: 4px;
                    padding: 8px;
                """)
                info_layout.addWidget(overview_label)
            
            with open("matchup_processing.log", "a") as f:
                f.write(f"Processing UI for {champion} - completed overview\n")
            
            # Add champion info to top layout
            logger.debug(f"Adding components to layouts for {champion}")
            top_layout.addWidget(img_frame)
            top_layout.addLayout(info_layout, 1)
            
            # Add top section to main layout
            main_layout.addWidget(top_section)
            
            # Create tabbed section for detailed information
            if not isinstance(matchup_info, str):
                logger.debug(f"Creating tabs for {champion}")
                with open("matchup_processing.log", "a") as f:
                    f.write(f"Processing UI for {champion} - creating tabs\n")
                    
                # Dump all attributes for debugging
                try:
                    attrs = dir(matchup_info)
                    logger.debug(f"Matchup info attributes: {attrs}")
                    with open("matchup_processing.log", "a") as f:
                        f.write(f"Matchup attributes: {', '.join(attrs)}\n")
                except Exception as e:
                    logger.error(f"Error getting attributes: {str(e)}")
                
                # Create tab widget
                tabs = QTabWidget()
                tabs.setStyleSheet("""
                    QTabWidget::pane {
                        border: 1px solid #3d3d3d;
                        background-color: #252729;
                        border-radius: 4px;
                    }
                    QTabBar::tab {
                        background-color: #2d2d2d;
                        color: #cccccc;
                        padding: 8px 12px;
                        margin-right: 2px;
                        border-top-left-radius: 4px;
                        border-top-right-radius: 4px;
                    }
                    QTabBar::tab:selected {
                        background-color: #252729;
                        border-bottom: 2px solid #ff4444;
                    }
                    QTabBar::tab:hover:!selected {
                        background-color: #353537;
                    }
                """)
                
                # Try creating each tab in a separate try-except block
                try:
                    # Create tabs for each section
                    sections = []
                    
                    # Tips & Runes tab
                    logger.debug(f"Creating Tips & Runes tab for {champion}")
                    tips_tab = self.create_tips_runes_tab(matchup_info)
                    if tips_tab:
                        sections.append(("Tips & Runes", tips_tab))
                        
                    # Gameplan tab
                    logger.debug(f"Creating Gameplan tab for {champion}")
                    gameplan_tab = self.create_gameplan_tab(matchup_info)
                    if gameplan_tab:
                        sections.append(("Gameplan", gameplan_tab))
                        
                    # Trading tab
                    logger.debug(f"Creating Trading tab for {champion}")
                    trading_tab = self.create_trading_tab(matchup_info)
                    if trading_tab:
                        sections.append(("Trading", trading_tab))
                        
                    # Watchouts tab
                    logger.debug(f"Creating Watchouts tab for {champion}")
                    watchouts_tab = self.create_watchouts_tab(matchup_info)
                    if watchouts_tab:
                        sections.append(("Watchouts", watchouts_tab))
                    
                    # Add all the tabs to the tab widget
                    logger.debug(f"Adding {len(sections)} tabs to tab widget")
                    for title, widget in sections:
                        if widget:  # Only add if widget exists
                            tabs.addTab(widget, title)
                            
                    # Add tabs to main layout if there are any tabs
                    if tabs.count() > 0:
                        main_layout.addWidget(tabs)
                    
                    with open("matchup_processing.log", "a") as f:
                        f.write(f"Processing UI for {champion} - finished creating tabs\n")
                
                except Exception as tabs_error:
                    logger.error(f"Error creating tabs for {champion}: {str(tabs_error)}", exc_info=True)
                    with open("matchup_processing.log", "a") as f:
                        f.write(f"ERROR creating tabs for {champion}: {str(tabs_error)}\n")
            
            # Add the main container to the content layout
            logger.debug(f"Adding matchup frame to content layout for {champion}")
            # Remove the stretch, add the widget, then add the stretch back
            if self.content_layout.count() > 0 and self.content_layout.itemAt(self.content_layout.count() - 1).spacerItem():
                self.content_layout.takeAt(self.content_layout.count() - 1)
            
            self.content_layout.addWidget(matchup_frame)
            self.content_layout.addStretch()
            
            with open("matchup_processing.log", "a") as f:
                f.write(f"Successfully completed UI setup for {champion}\n")
            logger.debug(f"Successfully added matchup for {champion}")
            
        except Exception as e:
            logger.error(f"Critical error in add_matchup for {champion}: {str(e)}", exc_info=True)
            with open("matchup_processing.log", "a") as f:
                f.write(f"CRITICAL ERROR in add_matchup for {champion}: {str(e)}\n")
            
            # Add a minimal error widget as fallback
            try:
                error_frame = QFrame()
                error_frame.setStyleSheet("background-color: #662222; padding: 10px; border-radius: 4px;")
                error_layout = QVBoxLayout(error_frame)
                
                error_label = QLabel(f"Error displaying {champion}: {str(e)}")
                error_label.setStyleSheet("color: white; font-weight: bold;")
                error_label.setWordWrap(True)
                
                error_layout.addWidget(error_label)
                
                # Remove the stretch, add the widget, then add the stretch back
                if self.content_layout.count() > 0 and self.content_layout.itemAt(self.content_layout.count() - 1).spacerItem():
                    self.content_layout.takeAt(self.content_layout.count() - 1)
                
                self.content_layout.addWidget(error_frame)
                self.content_layout.addStretch()
                
                logger.debug("Added error fallback widget")
            except Exception as fallback_e:
                logger.critical(f"Failed to create fallback error widget: {str(fallback_e)}", exc_info=True)

    def create_gameplan_tab(self, matchup_info):
        """Create a tab for early game strategy"""
        # Check for the attribute using both camel case and snake case
        early_game = None
        if hasattr(matchup_info, 'early_game'):
            early_game = matchup_info.early_game
        elif hasattr(matchup_info, 'Early_Game'):
            early_game = matchup_info.Early_Game
            
        if not early_game:
            return None
            
        logger.debug(f"Creating gameplan tab with early game content: {early_game[:30]}...")
            
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        title = QLabel("Early Game Strategy")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff4444;")
        layout.addWidget(title)
        
        content = QLabel(early_game)
        content.setWordWrap(True)
        content.setStyleSheet("color: #cccccc; font-size: 14px;")
        layout.addWidget(content)
        layout.addStretch()
        
        return widget
        
    def create_trading_tab(self, matchup_info):
        """Create a tab for trading information"""
        # Check for the attribute using both camel case and snake case
        how_to_trade = None
        if hasattr(matchup_info, 'how_to_trade'):
            how_to_trade = matchup_info.how_to_trade
        elif hasattr(matchup_info, 'How_to_Trade'):
            how_to_trade = matchup_info.How_to_Trade
            
        if not how_to_trade:
            return None
            
        logger.debug(f"Creating trading tab with content: {how_to_trade[:30]}...")
            
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        title = QLabel("How to Trade")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #44ff44;")
        layout.addWidget(title)
        
        content = QLabel(how_to_trade)
        content.setWordWrap(True)
        content.setStyleSheet("color: #cccccc; font-size: 14px;")
        layout.addWidget(content)
        layout.addStretch()
        
        return widget
        
    def create_watchouts_tab(self, matchup_info):
        """Create a tab for what to watch out for"""
        # Check for the attribute using both camel case and snake case
        what_to_watch = None
        if hasattr(matchup_info, 'what_to_watch_out_for'):
            what_to_watch = matchup_info.what_to_watch_out_for
        elif hasattr(matchup_info, 'What_to_Watch_Out_For'):
            what_to_watch = matchup_info.What_to_Watch_Out_For
            
        if not what_to_watch:
            return None
            
        logger.debug(f"Creating watchouts tab with content: {what_to_watch[:30]}...")
            
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        title = QLabel("What to Watch Out For")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #4444ff;")
        layout.addWidget(title)
        
        content = QLabel(what_to_watch)
        content.setWordWrap(True)
        content.setStyleSheet("color: #cccccc; font-size: 14px;")
        layout.addWidget(content)
        layout.addStretch()
        
        return widget
        
    def create_tips_runes_tab(self, matchup_info):
        """Create a tab for tips and runes"""
        # Check for the attribute using both camel case and snake case
        tips = None
        if hasattr(matchup_info, 'tips'):
            tips = matchup_info.tips
        elif hasattr(matchup_info, 'Tips'):
            tips = matchup_info.Tips
            
        has_tips = tips is not None and tips
        has_runes = hasattr(matchup_info, 'runes') and matchup_info.runes and any(matchup_info.runes)
        
        if not (has_tips or has_runes):
            return None
            
        logger.debug(f"Creating tips tab with content: {has_tips=}, {has_runes=}")
            
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)
        
        # Runes section
        if has_runes:
            runes_frame = QFrame()
            runes_frame.setStyleSheet("""
                QFrame {
                    background-color: #2d2d2d;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            runes_layout = QVBoxLayout(runes_frame)
            runes_layout.setSpacing(8)
            
            runes_title = QLabel("Recommended Runes")
            runes_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #44aaff;")
            runes_layout.addWidget(runes_title)
            
            # Rune image (full size)
            rune_image_label = QLabel()
            rune_image_label.setFixedSize(512, 512)
            rune_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if matchup_info.runes and matchup_info.runes.strip():
                logger.debug(f"Loading rune image from URL: {matchup_info.runes}")
                self.load_image(rune_image_label, matchup_info.runes)
            else:
                logger.debug("No valid rune image URL found")
            runes_layout.addWidget(rune_image_label, 0, Qt.AlignmentFlag.AlignCenter)
            
            layout.addWidget(runes_frame)
        
        # Tips section
        if has_tips:
            tips_frame = QFrame()
            tips_frame.setStyleSheet("""
                QFrame {
                    background-color: #2d2d2d;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            tips_layout = QVBoxLayout(tips_frame)
            
            tips_title = QLabel("Tips")
            tips_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffff44;")
            tips_layout.addWidget(tips_title)
            
            tips_content = QLabel(tips)
            tips_content.setWordWrap(True)
            tips_content.setStyleSheet("color: #cccccc; font-size: 14px;")
            tips_layout.addWidget(tips_content)
            
            layout.addWidget(tips_frame)
        
        layout.addStretch() 
        return widget

    def load_image(self, label, image_url):
        """Load image from URL with caching"""
        try:
            logger.debug(f"Loading image from URL: {image_url}")
            
            # Check cache first
            if image_url in self.image_cache:
                logger.debug(f"Using cached image for {image_url}")
                pixmap = self.image_cache[image_url]
                # Scale the pixmap to fit the label
                scaled_pixmap = pixmap.scaled(
                    label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                label.setPixmap(scaled_pixmap)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                return
                
            # If not cached, make network request
            url = image_url
            request = QNetworkRequest(QUrl(url))
            reply = self.network_manager.get(request)
            
            # Add to active replies set
            self.active_replies.add(reply)
            
            # Connect to the finished signal
            reply.finished.connect(lambda: self.on_image_downloaded(reply, label, image_url))
            
        except Exception as e:
            logger.error(f"Error loading image: {str(e)}", exc_info=True)
            
    def on_image_downloaded(self, reply, label, image_url):
        """Handle downloaded image data with improved error handling and cleanup"""
        temp_file = None
        try:
            # Remove from active replies
            self.active_replies.discard(reply)
            
            if reply.error() == QNetworkReply.NetworkError.NoError:
                # Check if label still exists
                if not label or sip.isdeleted(label):
                    logger.debug("Label no longer exists, skipping image processing")
                    return
                    
                # Read the image data
                img_data = reply.readAll()
                data_size = len(img_data.data())
                logger.debug(f"Image data size: {data_size} bytes")
                
                if data_size == 0:
                    logger.warning(f"Received empty image data for URL: {image_url}")
                    return
                
                # Save to a temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_file.write(img_data.data())
                temp_file.close()
                
                # Load image from the file
                pixmap = QPixmap(temp_file.name)
                if pixmap.isNull():
                    logger.error(f"Failed to load pixmap from temporary file for URL: {image_url}")
                    return
                
                # Cache the original pixmap and limit cache size
                self.image_cache[image_url] = pixmap.copy()
                self._limit_cache_size()
                    
                # Scale the pixmap to fit the label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                logger.debug(f"Scaled pixmap size: {scaled_pixmap.size().width()}x{scaled_pixmap.size().height()}")
                
                # Set the pixmap to the label and center it
                if not sip.isdeleted(label):
                    label.setPixmap(scaled_pixmap)
                    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    label.setMinimumSize(1, 1)  # Allow the label to shrink if needed
                
            else:
                logger.error(f"Error downloading image: {reply.errorString()} for URL: {image_url}")
                
        except Exception as e:
            logger.error(f"Error processing downloaded image: {str(e)}", exc_info=True)
        finally:
            # Clean up resources
            reply.deleteLater()
            
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.error(f"Error deleting temporary file: {str(e)}")
                    
    def _limit_cache_size(self):
        """Limit the size of the image cache to prevent memory issues"""
        if len(self.image_cache) > self.max_cache_size:
            logger.debug(f"Cache size ({len(self.image_cache)}) exceeds limit ({self.max_cache_size}), pruning oldest items")
            # Remove the oldest items (we can't know which ones are oldest, so just remove random ones)
            items_to_remove = len(self.image_cache) - self.max_cache_size
            keys_to_remove = list(self.image_cache.keys())[:items_to_remove]
            
            for key in keys_to_remove:
                # Explicitly delete the pixmap before removing from cache
                self.image_cache[key] = None
                del self.image_cache[key]
                
            logger.debug(f"Removed {items_to_remove} items from cache, new cache size: {len(self.image_cache)}")
            
            # Force garbage collection to clean up the removed pixmaps
            import gc
            gc.collect()

    def __del__(self):
        """Destructor to ensure cleanup when the widget is deleted"""
        try:
            self._cancel_pending_requests()
            self.image_cache.clear()
            logger.debug("MatchupDisplay destructor called - resources cleaned up")
        except Exception as e:
            logger.error(f"Error in MatchupDisplay destructor: {str(e)}") 