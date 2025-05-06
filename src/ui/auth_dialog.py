from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                        QFileDialog, QProgressBar, QMessageBox, QWizard, QWizardPage)
from PyQt6.QtCore import QThread, pyqtSignal

import os
import threading
import webbrowser
import time

from src.logger import logger
from src.auth import google_auth

# Constants
DEFAULT_CREDS_FILE = 'credentials.json'
DEFAULT_TOKEN_FILE = 'token.json'
INSTRUCTIONS_URL = "https://github.com/bvanelli/quante-runes/blob/main/docs/google_api_setup.md"

class AuthenticationThread(QThread):
    """Thread to handle authentication without blocking the UI."""
    auth_success = pyqtSignal(bool, str)
    progress_update = pyqtSignal(int, str)
    
    def __init__(self, credentials_file):
        super().__init__()
        self.credentials_file = credentials_file
        self.stop_event = threading.Event()
    
    def run(self):
        try:
            self.progress_update.emit(10, "Checking credentials file...")
            
            if not os.path.exists(self.credentials_file):
                self.auth_success.emit(False, f"Credentials file '{self.credentials_file}' not found.")
                return
                
            self.progress_update.emit(30, "Starting authentication process...")
            
            # Force re-authentication
            google_auth.force_reauthentication()
            
            self.progress_update.emit(50, "Launching browser for authentication...")
            
            # Get credentials (this will launch the browser and OAuth flow)
            creds = google_auth.get_credentials(credentials_file=self.credentials_file)
            
            # Monitor authentication progress
            start_time = time.time()
            timeout = 180  # 3 minutes timeout
            
            # Wait for token file to be created or timeout
            while not os.path.exists(DEFAULT_TOKEN_FILE) and not self.stop_event.is_set():
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    self.auth_success.emit(False, "Authentication timed out. Please try again.")
                    return
                
                # Calculate progress - from 50% to 90% during waiting period
                progress = 50 + int(min(elapsed / timeout * 40, 40))
                self.progress_update.emit(progress, "Waiting for authentication to complete...")
                time.sleep(0.5)
            
            if self.stop_event.is_set():
                return
            
            self.progress_update.emit(95, "Finalizing authentication...")
            
            if creds and os.path.exists(DEFAULT_TOKEN_FILE):
                self.progress_update.emit(100, "Authentication successful!")
                self.auth_success.emit(True, "Authentication successful!")
            else:
                self.auth_success.emit(False, "Failed to authenticate. Please try again.")
                
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}", exc_info=True)
            self.auth_success.emit(False, f"Authentication error: {str(e)}")

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to Urgot Matchup Helper")
        self.setSubTitle("Let's set up your Google Sheets connection")
        
        layout = QVBoxLayout()
        
        # Welcome message
        welcome_text = QLabel(
            "This wizard will help you connect to Google Sheets to access champion matchup data.\n\n"
            "You'll need to authorize access to your Google account to read the spreadsheet data.\n\n"
            "The app only requests read-only access and will only attempt to read a single sheet (I Promise)"
        )
        welcome_text.setWordWrap(True)
        layout.addWidget(welcome_text)
        
        # Add some spacing
        layout.addSpacing(20)
        
        # Information about credentials
        creds_info = QLabel(
            "To get started, you'll need a Google API credentials file (credentials.json).\n\n"
            "If you don't have one already, we'll guide you through creating it."
        )
        creds_info.setWordWrap(True)
        layout.addWidget(creds_info)
        
        self.setLayout(layout)

class CredentialsPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Google API Credentials")
        self.setSubTitle("Please provide your Google API credentials file")
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel(
            "You need a credentials.json file from the Google Developer Console.\n\n"
            "If you already have this file, please select it. If not, click the button below for instructions on how to create one."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setWordWrap(True)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_for_credentials)
        
        file_layout.addWidget(QLabel("Credentials file:"))
        file_layout.addWidget(self.file_path_label, 1)
        file_layout.addWidget(browse_button)
        
        layout.addLayout(file_layout)
        
        # Help button
        help_layout = QHBoxLayout()
        help_button = QPushButton("How to get credentials")
        help_button.clicked.connect(self.open_instructions)
        help_layout.addStretch()
        help_layout.addWidget(help_button)
        
        layout.addSpacing(20)
        layout.addLayout(help_layout)
        
        # Register the field for completion tracking
        self.registerField("credentials_file*", self, "credentialsFile")
        
        self.setLayout(layout)
        
        # If credentials file exists in the current directory, pre-select it
        if os.path.exists(DEFAULT_CREDS_FILE):
            self.set_credentials_file(os.path.abspath(DEFAULT_CREDS_FILE))
    
    def open_instructions(self):
        webbrowser.open(INSTRUCTIONS_URL)
    
    def browse_for_credentials(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Google API Credentials", "", "JSON Files (*.json)"
        )
        if file_path:
            self.set_credentials_file(file_path)
    
    def set_credentials_file(self, file_path):
        self.file_path_label.setText(file_path)
        self.setField("credentials_file", file_path)
        self.completeChanged.emit()
    
    # Property for the credentials file path
    def getCredentialsFile(self):
        return self.file_path_label.text() if self.file_path_label.text() != "No file selected" else ""
    
    def setCredentialsFile(self, value):
        self.file_path_label.setText(value)
    
    credentialsFile = property(getCredentialsFile, setCredentialsFile)
    
    def isComplete(self):
        return os.path.exists(self.getCredentialsFile())

class AuthorizationPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Google Authorization")
        self.setSubTitle("Authenticate with your Google account")
        
        layout = QVBoxLayout()
        
        # Instructions
        auth_instructions = QLabel(
            "Click the button below to start the authentication process. "
            "This will open your web browser where you can sign in to your Google account.\n\n"
            "After you authorize the app, you'll be redirected to a page confirming the authentication is complete."
        )
        auth_instructions.setWordWrap(True)
        layout.addWidget(auth_instructions)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to start authentication")
        layout.addWidget(self.status_label)
        
        # Start button
        self.auth_button = QPushButton("Start Authentication")
        self.auth_button.clicked.connect(self.start_authentication)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.auth_button)
        
        layout.addSpacing(10)
        layout.addLayout(button_layout)
        
        # Initialize the authentication thread
        self.auth_thread = None
        self.is_auth_complete = False
        
        # Register a field to track completion
        self.registerField("auth_complete", self, "authComplete")
        
        self.setLayout(layout)
    
    def start_authentication(self):
        credentials_file = self.field("credentials_file")
        
        if not credentials_file or not os.path.exists(credentials_file):
            QMessageBox.warning(
                self, 
                "Missing Credentials", 
                "Credentials file not found. Please go back and select a valid credentials file."
            )
            return
        
        # Disable the button while authentication is in progress
        self.auth_button.setEnabled(False)
        self.auth_button.setText("Authentication in progress...")
        
        # Start the authentication thread
        self.auth_thread = AuthenticationThread(credentials_file)
        self.auth_thread.auth_success.connect(self.on_auth_complete)
        self.auth_thread.progress_update.connect(self.update_progress)
        self.auth_thread.start()
    
    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def on_auth_complete(self, success, message):
        if success:
            self.status_label.setText("Authentication successful!")
            self.progress_bar.setValue(100)
            self.auth_button.setText("Authentication Complete")
            self.setField("auth_complete", True)
            self.is_auth_complete = True
            self.completeChanged.emit()
        else:
            self.status_label.setText(f"Authentication failed: {message}")
            self.progress_bar.setValue(0)
            self.auth_button.setEnabled(True)
            self.auth_button.setText("Retry Authentication")
    
    # Property for auth completion
    def getAuthComplete(self):
        return self.is_auth_complete
    
    def setAuthComplete(self, value):
        self.is_auth_complete = value
    
    authComplete = property(getAuthComplete, setAuthComplete)
    
    def isComplete(self):
        return self.is_auth_complete

class CompletionPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Setup Complete")
        self.setSubTitle("You're ready to use Urgot Matchup Helper")
        
        layout = QVBoxLayout()
        
        # Success message
        success_label = QLabel(
            "Congratulations! You've successfully set up the Google Sheets connection.\n\n"
            "The app will now be able to access the matchup data and provide you with the information you need during your games.\n\n"
            "Click Finish to start using the application."
        )
        success_label.setWordWrap(True)
        layout.addWidget(success_label)
        
        self.setLayout(layout)

class AuthenticationWizard(QWizard):
    """Wizard to guide users through the authentication process."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Urgot Matchup Helper - Google Authentication")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(600, 400)
        
        # Add pages
        self.addPage(WelcomePage())
        self.addPage(CredentialsPage())
        self.addPage(AuthorizationPage())
        self.addPage(CompletionPage())
        
        # Set button text
        self.setButtonText(QWizard.WizardButton.FinishButton, "Start App")
        
        # Connect signals
        self.finished.connect(self.on_finished)
    
    def on_finished(self, result):
        """Called when the wizard is finished."""
        if result == QWizard.DialogCode.Accepted:
            logger.info("Authentication wizard completed successfully")
        else:
            logger.warning("Authentication wizard was cancelled") 