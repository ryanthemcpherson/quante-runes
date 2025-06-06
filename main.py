import sys
import asyncio
import signal
import traceback
import os
from PyQt6.QtWidgets import QApplication, QMessageBox, QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from qasync import QEventLoop
from src.logger import logger
from src.auth import google_auth

# Log startup information
startup_log_file = "startup_log.txt"
try:
    with open(startup_log_file, "w") as f:
        f.write(f"Python version: {sys.version}\n")
        f.write(f"Working directory: {os.getcwd()}\n")
        f.write(f"Command line args: {sys.argv}\n")
        f.write(f"Modules loaded: {list(sys.modules.keys())}\n")
        f.write("Starting application...\n")
except Exception as e:
    print(f"Failed to write startup log: {str(e)}")

# Try importing from exceptions, but use a safer approach
try:
    from exceptions import LeagueClientError
    with open(startup_log_file, "a") as f:
        f.write("Imported LeagueClientError from exceptions\n")
except ImportError:
    try:
        from src.exceptions import LeagueClientError
        with open(startup_log_file, "a") as f:
            f.write("Imported LeagueClientError from src.exceptions\n")
    except ImportError:
        # Define a fallback class if imports fail
        class LeagueClientError(Exception):
            pass
        with open(startup_log_file, "a") as f:
            f.write("Using fallback LeagueClientError definition\n")
        logger.error("Could not import LeagueClientError, using fallback definition")

# Create a fallback main window in case the real one fails
class MinimalMainWindow(QMainWindow):
    def __init__(self, error_message=None):
        super().__init__()
        self.setWindowTitle("Urgot Matchup Helper - ERROR MODE")
        self.resize(800, 600)
        
        # Create a central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # Add error message
        error_label = QLabel("Error starting application")
        error_label.setStyleSheet("font-size: 18px; color: red; font-weight: bold;")
        layout.addWidget(error_label)
        
        if error_message:
            details_label = QLabel(error_message)
            details_label.setWordWrap(True)
            layout.addWidget(details_label)
        
        # Add instructions
        instructions = QLabel("Please check the startup_log.txt file for details.")
        instructions.setStyleSheet("font-size: 14px;")
        layout.addWidget(instructions)
        
        # Add a quit button
        quit_button = QPushButton("Quit Application")
        quit_button.clicked.connect(self.close)
        layout.addWidget(quit_button)
        
        # Set the central widget
        self.setCentralWidget(central_widget)
        
        # For shutdown handling compatibility
        self.check_timer = None
        self.update_timer = None
        self.league_client = None
        self.matchup_display = None
        self.matchups = []
        
    async def close(self):
        """Async version of close for compatibility with shutdown function"""
        super().close()

# Wrap imports in try blocks
real_main_window_available = False
try:
    from src.ui.main_window import MainWindow
    real_main_window_available = True
    with open(startup_log_file, "a") as f:
        f.write("Imported MainWindow\n")
except Exception as e:
    error_msg = f"Failed to import MainWindow: {str(e)}\n{traceback.format_exc()}"
    with open(startup_log_file, "a") as f:
        f.write(error_msg)
    logger.critical(error_msg)
    # We'll use the fallback MainWindow

async def shutdown(window):
    """Gracefully shutdown all resources."""
    logger.info("Starting graceful shutdown sequence...")
    try:
        # Stop all timers
        if hasattr(window, 'check_timer') and window.check_timer:
            window.check_timer.stop()
            logger.info("Check timer stopped.")
            
        if hasattr(window, 'update_timer') and window.update_timer:
            window.update_timer.stop()
            logger.info("Update timer stopped.")
            
        # Hide the tray icon if it exists
        if hasattr(window, 'tray_icon') and window.tray_icon:
            window.tray_icon.hide()
            logger.info("Tray icon hidden.")
            
        # Close league client connection
        if hasattr(window, 'league_client') and window.league_client:
            await window.league_client.close()
            logger.info("LeagueClient session closed gracefully.")
            
        # Clear any cached data
        if hasattr(window, 'matchups'):
            window.matchups = []
            
        # Clean up any other resources
        if hasattr(window, 'sheets_manager') and window.sheets_manager:
            # No specific close method for sheets_manager, but good to log it
            logger.info("GoogleSheetsManager resources released.")
            
        # Clean up UI components if needed
        if hasattr(window, 'matchup_display') and window.matchup_display:
            window.matchup_display.clear_matchups()
            logger.info("UI components cleared.")
        
        # Set force quit flag if supported
        if hasattr(window, '_force_quit'):
            window._force_quit = True
            logger.info("Force quit flag set.")
            
        logger.info("All resources cleaned up successfully.")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)

def main():
    # Create app before anything else
    app = None
    window = None
    critical_error = None
    
    try:
        with open(startup_log_file, "a") as f:
            f.write("Starting main function\n")

        # Initialize application
        try:
            app = QApplication(sys.argv)
            with open(startup_log_file, "a") as f:
                f.write("Created QApplication\n")
        except Exception as e:
            error_msg = f"Failed to create QApplication: {str(e)}\n{traceback.format_exc()}"
            with open(startup_log_file, "a") as f:
                f.write(error_msg)
            logger.critical(error_msg)
            critical_error = error_msg
            raise
        
        # Set window icon
        try:
            icon_path = "urgot_icon.png"
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
                with open(startup_log_file, "a") as f:
                    f.write(f"Set window icon: {icon_path}\n")
            else:
                with open(startup_log_file, "a") as f:
                    f.write(f"Icon not found: {icon_path}\n")
        except Exception as e:
            with open(startup_log_file, "a") as f:
                f.write(f"Failed to set icon: {str(e)}\n")
        
        # Check for credentials and show authentication wizard if needed
        try:
            with open(startup_log_file, "a") as f:
                f.write("Checking for Google credentials\n")
            
            # Check if there's an existing token file
            token_exists = os.path.exists('token.json')
            client_secrets_exist = os.path.exists('client_secrets.json')
            
            if not client_secrets_exist:
                with open(startup_log_file, "a") as f:
                    f.write("Client secrets file missing. Cannot continue.\n")
                
                error_box = QMessageBox()
                error_box.setIcon(QMessageBox.Icon.Critical)
                error_box.setWindowTitle("Missing Credentials")
                error_box.setText("The OAuth client secrets file is missing.")
                error_box.setInformativeText(
                    "The application cannot connect to Google Sheets without this file. "
                    "Please contact the application developer for support."
                )
                error_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                error_box.exec()
                return
            
            # If no token exists or it's invalid, show the auth dialog
            needs_auth = not token_exists
            
            if token_exists:
                # Verify the token still works
                try:
                    with open(startup_log_file, "a") as f:
                        f.write("Token exists. Verifying if it's valid...\n")
                    
                    # Try loading credentials without forcing reauth
                    creds = google_auth.get_credentials(force_new_auth=False)
                    
                    if not creds:
                        with open(startup_log_file, "a") as f:
                            f.write("Existing token is invalid or expired.\n")
                        needs_auth = True
                except Exception as e:
                    with open(startup_log_file, "a") as f:
                        f.write(f"Error validating token: {str(e)}\n")
                    needs_auth = True
            
            if needs_auth:
                with open(startup_log_file, "a") as f:
                    f.write("Need to show auth dialog.\n")
                
                # Import here to avoid circular imports
                from src.ui.service_account_dialog import AuthInfoDialog
                
                # Show the auth info dialog
                auth_dialog = AuthInfoDialog()
                dialog_result = auth_dialog.exec()
                
                with open(startup_log_file, "a") as f:
                    f.write(f"Auth dialog completed with result: {dialog_result}\n")
                
                # If user cancelled the dialog, exit
                if dialog_result == 0:
                    with open(startup_log_file, "a") as f:
                        f.write("User cancelled authentication. Exiting.\n")
                    logger.warning("Authentication cancelled by user.")
                    return
                
                # Start the authentication flow
                with open(startup_log_file, "a") as f:
                    f.write("Starting OAuth authentication flow.\n")
                
                creds = google_auth.get_credentials(force_new_auth=True)
                
                if not creds:
                    with open(startup_log_file, "a") as f:
                        f.write("Authentication failed. Exiting.\n")
                    
                    error_box = QMessageBox()
                    error_box.setIcon(QMessageBox.Icon.Critical)
                    error_box.setWindowTitle("Authentication Error")
                    error_box.setText("Authentication failed or you don't have access to the spreadsheet.")
                    error_box.setInformativeText(
                        "The application cannot continue without successful authentication. "
                        "Please try again or contact the application developer for support."
                    )
                    error_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                    error_box.exec()
                    return
                
                with open(startup_log_file, "a") as f:
                    f.write("Authentication successful.\n")
            else:
                with open(startup_log_file, "a") as f:
                    f.write("Valid token already exists. No need for authentication.\n")
            
        except Exception as e:
            with open(startup_log_file, "a") as f:
                f.write(f"Error during authentication check: {str(e)}\n{traceback.format_exc()}\n")
            logger.error(f"Error during authentication check: {str(e)}", exc_info=True)
            # Continue execution, the sheets manager will handle credential errors
            
        # Set up event loop with error handling
        loop = None
        try:
            loop = QEventLoop(app)
            asyncio.set_event_loop(loop)
            with open(startup_log_file, "a") as f:
                f.write("Created event loop\n")
        except Exception as e:
            error_msg = f"Failed to create event loop: {str(e)}\n{traceback.format_exc()}"
            with open(startup_log_file, "a") as f:
                f.write(error_msg)
            logger.critical(error_msg)
            critical_error = error_msg
            raise
        
        # Create main window with error handling
        try:
            if real_main_window_available:
                window = MainWindow()
                with open(startup_log_file, "a") as f:
                    f.write("Created MainWindow\n")
            else:
                window = MinimalMainWindow(critical_error)
                with open(startup_log_file, "a") as f:
                    f.write("Created MinimalMainWindow (fallback)\n")
                critical_error = "Using fallback minimal UI due to MainWindow import failure"
                
            window.show()
            with open(startup_log_file, "a") as f:
                f.write("Called window.show()\n")
        except Exception as e:
            error_msg = f"Failed to create or show window: {str(e)}\n{traceback.format_exc()}"
            with open(startup_log_file, "a") as f:
                f.write(error_msg)
            logger.critical(error_msg)
            critical_error = error_msg
            if window:
                try:
                    window.close()
                except Exception as e:
                    logger.error(f"Error closing window: {str(e)}", exc_info=True)
                    with open(startup_log_file, "a") as f:
                        f.write(f"Error closing window: {str(e)}\n")
            
            # Try to show a minimal fallback window
            try:
                window = MinimalMainWindow(f"Error creating main window: {str(e)}")
                window.show()
                with open(startup_log_file, "a") as f:
                    f.write("Created and showed fallback window after error\n")
            except Exception as e2:
                with open(startup_log_file, "a") as f:
                    f.write(f"Failed to create fallback window: {str(e2)}\n")
                raise e  # Re-raise the original exception
        
        # Signal handler for graceful shutdown
        def handle_signal(*_):
            with open(startup_log_file, "a") as f:
                f.write("Received signal for shutdown\n")
            logger.info("Received termination signal. Shutting down...")
            try:
                # Create and await shutdown task
                shutdown_task = loop.create_task(shutdown(window))
                
                # Define a function to clean up and stop the loop
                def terminate_app():
                    try:
                        if not shutdown_task.done():
                            logger.warning("Shutdown task not completed, forcing stop...")
                        
                        # Stop the loop, which will cause the app to exit
                        loop.stop()
                        
                        # Explicitly quit the application
                        if app:
                            app.quit()
                            
                        with open(startup_log_file, "a") as f:
                            f.write("Stopped event loop and quit application\n")
                    except Exception as e:
                        logger.error(f"Error during termination: {str(e)}", exc_info=True)
                        with open(startup_log_file, "a") as f:
                            f.write(f"Error during termination: {str(e)}\n")
                        loop.stop()
                
                # Allow up to 3 seconds for shutdown to complete
                loop.call_later(3, terminate_app)
            except Exception as e:
                logger.error(f"Error during signal handling: {str(e)}", exc_info=True)
                with open(startup_log_file, "a") as f:
                    f.write(f"Error during signal handling: {str(e)}\n")
                # Stop the loop immediately in case of error
                loop.stop()
                if app:
                    app.quit()
        
        # Set up signal handlers with error handling
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                with open(startup_log_file, "a") as f:
                    f.write(f"Setting up signal handler for {sig}\n")
                loop.add_signal_handler(sig, handle_signal)
            except NotImplementedError:
                # add_signal_handler may not be implemented on Windows event loops
                with open(startup_log_file, "a") as f:
                    f.write(f"Using fallback signal handler for {sig}\n")
                signal.signal(sig, handle_signal)
            except Exception as e:
                logger.error(f"Error setting up signal handler for {sig}: {str(e)}", exc_info=True)
                with open(startup_log_file, "a") as f:
                    f.write(f"Error setting up signal handler for {sig}: {str(e)}\n")
                
        # Log that we're about to run the event loop
        with open(startup_log_file, "a") as f:
            f.write("About to run event loop\n")
        
        # Run the event loop
        with loop:
            # Add a safety timer to keep the app running
            keep_alive_timer = QTimer()
            keep_alive_timer.setInterval(100)  # 100ms
            keep_alive_timer.timeout.connect(lambda: None)  # Do nothing, just keep event loop active
            keep_alive_timer.start()
            
            with open(startup_log_file, "a") as f:
                f.write("Running event loop\n")
            loop.run_forever()
            with open(startup_log_file, "a") as f:
                f.write("Event loop finished\n")
                
            # Stop the keep-alive timer
            keep_alive_timer.stop()
            
    except LeagueClientError as e:
        # If League Client is not running, continue running the app but with a message
        logger.warning(f"League Client connection issue: {str(e)}")
        with open(startup_log_file, "a") as f:
            f.write(f"LeagueClientError: {str(e)}\n")
        if "window" in locals() and window:
            try:
                if hasattr(window, 'show_client_connection_message'):
                    window.show_client_connection_message()
                with open(startup_log_file, "a") as f:
                    f.write("Showed client connection message\n")
            except Exception as e2:
                logger.error(f"Error showing client connection message: {str(e2)}", exc_info=True)
                with open(startup_log_file, "a") as f:
                    f.write(f"Error showing client connection message: {str(e2)}\n")
        # Continue execution
    except Exception as e:
        error_msg = f"Application error: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        with open(startup_log_file, "a") as f:
            f.write(error_msg)
        critical_error = error_msg
    finally:
        with open(startup_log_file, "a") as f:
            f.write("Entering finally block\n")
            
        # If we had a critical error, show a message box
        if critical_error and app:
            try:
                with open(startup_log_file, "a") as f:
                    f.write("Showing error message box\n")
                error_box = QMessageBox()
                error_box.setIcon(QMessageBox.Icon.Critical)
                error_box.setWindowTitle("Application Error")
                error_box.setText("The application encountered a critical error and needs to close.")
                error_box.setDetailedText(critical_error)
                error_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                error_box.exec()
            except Exception as e:
                with open(startup_log_file, "a") as f:
                    f.write(f"Failed to show error box: {str(e)}\n")
            
        # Ensure app quits and any remaining resources are cleaned up
        try:
            if 'window' in locals() and window:
                # Run cleanup one last time in case the signal handler didn't complete
                try:
                    with open(startup_log_file, "a") as f:
                        f.write("Running final shutdown\n")
                    # Use a timeout to prevent blocking if the shutdown task doesn't complete
                    try:
                        # Create a new event loop for the final shutdown
                        final_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(final_loop)
                        
                        # Run shutdown with a timeout
                        shutdown_future = asyncio.ensure_future(shutdown(window), loop=final_loop)
                        final_loop.run_until_complete(asyncio.wait_for(shutdown_future, timeout=3.0))
                    except asyncio.TimeoutError:
                        logger.warning("Final shutdown timed out after 3 seconds")
                        with open(startup_log_file, "a") as f:
                            f.write("Final shutdown timed out after 3 seconds\n")
                    except Exception as e:
                        logger.error(f"Error during final shutdown: {str(e)}", exc_info=True)
                        with open(startup_log_file, "a") as f:
                            f.write(f"Error during final shutdown: {str(e)}\n")
                except Exception as e:
                    logger.error(f"Error during final shutdown: {str(e)}", exc_info=True)
                    with open(startup_log_file, "a") as f:
                        f.write(f"Error during final shutdown: {str(e)}\n")
        except Exception as e:
            logger.error(f"Error during final cleanup: {str(e)}", exc_info=True)
            with open(startup_log_file, "a") as f:
                f.write(f"Error during final cleanup: {str(e)}\n")
        
        try:
            if app:
                with open(startup_log_file, "a") as f:
                    f.write("Quitting application\n")
                app.quit()
                # Force app to process events and shut down
                app.processEvents()
        except Exception as e:
            logger.error(f"Error quitting application: {str(e)}", exc_info=True)
            with open(startup_log_file, "a") as f:
                f.write(f"Error quitting application: {str(e)}\n")
            
        logger.info("Application terminated.")
        with open(startup_log_file, "a") as f:
            f.write("Application terminated\n")
            
        # As a last resort, force exit
        sys.exit(0)

if __name__ == "__main__":
    try:
        with open(startup_log_file, "a") as f:
            f.write("Calling main() function\n")
        main()
    except Exception as e:
        error_msg = f"Uncaught exception in main: {str(e)}\n{traceback.format_exc()}"
        logger.critical(error_msg)
        with open(startup_log_file, "a") as f:
            f.write(error_msg)
        try:
            app = QApplication.instance()
            if app:
                error_box = QMessageBox()
                error_box.setIcon(QMessageBox.Icon.Critical)
                error_box.setWindowTitle("Fatal Error")
                error_box.setText("The application encountered a fatal error and needs to close.")
                error_box.setDetailedText(error_msg)
                error_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                error_box.exec()
        except Exception as e:
            logger.error(f"Error showing fatal error box: {str(e)}", exc_info=True)
            with open(startup_log_file, "a") as f:
                f.write(f"Error showing fatal error box: {str(e)}\n")
        sys.exit(1) 