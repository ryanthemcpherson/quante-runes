from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                         QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import os

from src.logger import logger

class AuthInfoDialog(QDialog):
    """Simple dialog to inform users about the Google authentication process."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Google Sheets Authentication")
        self.setMinimumWidth(450)
        self.setModal(True)
        
        # Set up the layout
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Urgot Matchup Helper - Google Authentication")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        layout.addSpacing(10)
        
        # Information text
        info_text = (
            "This application needs to access Google Sheets to retrieve matchup data.\n\n"
            "You'll need to sign in with your Google account that has access to the shared matchup sheet.\n\n"
            "When you click 'Continue', your web browser will open for you to sign in to Google and grant "
            "read-only access to Google Sheets data."
        )
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addSpacing(10)
        
        # Privacy note
        privacy_text = (
            "Note: This application only requests read-only access to Google Sheets. "
            "Your credentials are stored locally on your device and are not sent to any third-party servers."
        )
        
        privacy_label = QLabel(privacy_text)
        privacy_label.setWordWrap(True)
        privacy_font = QFont()
        privacy_font.setItalic(True)
        privacy_label.setFont(privacy_font)
        layout.addWidget(privacy_label)
        
        # Privacy policy link
        privacy_link = QPushButton("View Privacy Policy")
        privacy_link.setFlat(True)
        privacy_link.setCursor(Qt.CursorShape.PointingHandCursor)
        privacy_link.clicked.connect(self.show_privacy_policy)
        
        link_layout = QHBoxLayout()
        link_layout.addStretch()
        link_layout.addWidget(privacy_link)
        link_layout.addStretch()
        
        layout.addLayout(link_layout)
        layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.continue_button = QPushButton("Continue")
        self.continue_button.clicked.connect(self.start_authentication)
        self.continue_button.setDefault(True)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.continue_button)
        
        layout.addLayout(button_layout)
    
    def show_privacy_policy(self):
        """Show the privacy policy dialog."""
        try:
            # Check if the privacy policy exists
            policy_file = 'PRIVACY_POLICY.md'
            
            if os.path.exists(policy_file):
                # Read the privacy policy file
                with open(policy_file, 'r') as f:
                    policy_text = f.read()
                
                # Create and show the privacy policy dialog
                policy_dialog = QMessageBox(self)
                policy_dialog.setWindowTitle("Privacy Policy")
                policy_dialog.setText("Urgot Matchup Helper Privacy Policy")
                policy_dialog.setDetailedText(policy_text)
                policy_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
                policy_dialog.exec()
            else:
                QMessageBox.warning(
                    self,
                    "Privacy Policy Not Found",
                    "The privacy policy file could not be found. Please contact the application developer for more information."
                )
        except Exception as e:
            logger.error(f"Error showing privacy policy: {str(e)}", exc_info=True)
            QMessageBox.warning(
                self,
                "Error",
                f"An error occurred while trying to show the privacy policy: {str(e)}"
            )
    
    def start_authentication(self):
        """Start the OAuth authentication process."""
        try:
            # Check if the embedded credentials file exists
            credentials_file = 'client_secrets.json'
            if not os.path.exists(credentials_file):
                QMessageBox.critical(
                    self,
                    "Missing Credentials File",
                    f"The OAuth credentials file '{credentials_file}' was not found. "
                    "Please contact the application developer for support."
                )
                self.reject()
                return
            
            # Accept the dialog (close it)
            self.accept()
            
            # Start the authentication flow (this will open the browser)
            # We handle this in main.py after the dialog closes
            
        except Exception as e:
            logger.error(f"Error starting authentication: {str(e)}", exc_info=True)
            QMessageBox.critical(
                self,
                "Authentication Error",
                f"An error occurred while starting authentication: {str(e)}"
            )
            self.reject() 