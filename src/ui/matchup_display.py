from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .base_ui import BaseUI
from logger import logger

class MatchupDisplay(BaseUI):
    def __init__(self):
        super().__init__()
        self.content_widget = None
        self.content_layout = None
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
        """Clear all matchup widgets"""
        logger.debug("Clearing matchup display")
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.content_layout.addStretch()  # Add stretch back after clearing

    def add_matchup(self, champion, tips):
        """Add a matchup widget"""
        logger.debug(f"Adding matchup display for {champion}")
        logger.debug(f"Raw tips: {tips}")
        
        matchup_frame = QFrame()
        matchup_frame.setStyleSheet("""
            QFrame {
                background-color: #1e2021;
                border-radius: 4px;
                padding: 8px;
                margin-bottom: 8px;
            }
        """)
        
        layout = QVBoxLayout(matchup_frame)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Add champion name
        champion_label = QLabel(champion)
        champion_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff4444;")
        layout.addWidget(champion_label)
        
        # Extract difficulty text
        difficulty = "Unknown"
        if tips:
            import re
            match = re.search(r'Difficulty:\s*([^\n]+)', tips)
            if match:
                difficulty = match.group(1).strip()
                # Remove the difficulty line from tips
                tips = re.sub(r'Difficulty:[^\n]+\n?', '', tips, flags=re.IGNORECASE).strip()
                logger.debug(f"Found difficulty text: {difficulty}")
        
        # Add difficulty label
        difficulty_label = QLabel(f"Difficulty: {difficulty}")
        difficulty_label.setStyleSheet("font-size: 14px; color: #ff4444;")
        layout.addWidget(difficulty_label)
        
        # Define sections with their headers and colors
        sections = [
            ("Early Game", ["EARLY GAME", "EARLY", "EARLY GAME:", "EARLY:"], "#ff4444"),
            ("How to Trade", ["HOW TO TRADE", "TRADING", "TRADING:", "HOW TO TRADE:"], "#44ff44"),
            ("What to Watch Out For", ["WHAT TO WATCH OUT FOR", "WATCH OUT", "WATCH OUT:", "WHAT TO WATCH OUT FOR:"], "#4444ff"),
            ("Tips", ["TIPS", "TIPS:", "GENERAL TIPS", "GENERAL TIPS:"], "#ffff44")
        ]
        
        for title, headers, color in sections:
            content = None
            for header in headers:
                content = self.extract_section(tips, header)
                if content:
                    break
            
            if content:
                section_frame = QFrame()
                section_frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: #2d2d2d;
                        border-radius: 4px;
                        padding: 8px;
                        margin-top: 4px;
                    }}
                """)
                section_layout = QVBoxLayout(section_frame)
                
                section_title = QLabel(title)
                section_title.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 14px;")
                section_layout.addWidget(section_title)
                
                # Clean up the content
                content = self.clean_section_content(content)
                
                section_content = QLabel(content)
                section_content.setStyleSheet("color: #cccccc; font-size: 14px;")
                section_content.setWordWrap(True)
                section_layout.addWidget(section_content)
                
                layout.addWidget(section_frame)
        
        # If no sections were found, display the raw tips
        if not any(self.extract_section(tips, header) for _, headers, _ in sections for header in headers):
            tips_label = QLabel(tips)
            tips_label.setStyleSheet("color: #cccccc; font-size: 14px;")
            tips_label.setWordWrap(True)
            layout.addWidget(tips_label)
        
        # Insert at the beginning (before the stretch)
        self.content_layout.insertWidget(self.content_layout.count() - 1, matchup_frame)
        logger.debug(f"Matchup display added for {champion}")

    def extract_section(self, text, header):
        """Extract a section from the text based on its header"""
        if not text or not header:
            return None
        
        # Normalize the text and header
        text = text.upper()
        header = header.upper()
        
        if header not in text:
            return None
        
        start_idx = text.find(header) + len(header)
        
        # Find the next section header
        next_section_start = len(text)
        for _, headers, _ in [
            ("Early Game", ["EARLY GAME", "EARLY", "EARLY GAME:", "EARLY:"], "#44ff44"),
            ("How to Trade", ["HOW TO TRADE", "TRADING", "HOW TO TRADE:", "TRADING:"], "#4444ff"),
            ("What to Watch Out For", ["WHAT TO WATCH OUT FOR", "WATCH OUT", "WHAT TO WATCH OUT FOR:", "WATCH OUT:"], "#ff4444"),
            ("Tips", ["TIPS", "TIPS:", "ADDITIONAL TIPS", "ADDITIONAL TIPS:"], "#ffff44")
        ]:
            for h in headers:
                idx = text.find(h.upper(), start_idx)
                if idx != -1 and idx < next_section_start:
                    next_section_start = idx
        
        content = text[start_idx:next_section_start].strip()
        return content if content else None

    def clean_section_content(self, content):
        """Clean up section content"""
        if not content:
            return content
            
        # Remove extra newlines and leading/trailing whitespace
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Remove any remaining section headers and colons
        headers = [
            "EARLY GAME", "EARLY", "EARLY GAME:", "EARLY:",
            "HOW TO TRADE", "TRADING", "HOW TO TRADE:", "TRADING:",
            "WHAT TO WATCH OUT FOR", "WATCH OUT", "WHAT TO WATCH OUT FOR:", "WATCH OUT:",
            "TIPS", "TIPS:", "ADDITIONAL TIPS", "ADDITIONAL TIPS:"
        ]
        
        cleaned_lines = []
        for line in lines:
            # Remove any section headers
            for header in headers:
                line = line.replace(header, '')
            
            # Remove leading colons and spaces
            line = line.lstrip(':').strip()
            
            # Remove any remaining colons at the start of the line
            if line.startswith(':'):
                line = line[1:].strip()
            
            if line:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines) 