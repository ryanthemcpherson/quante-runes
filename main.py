import sys
import asyncio
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from qasync import QEventLoop
from src.ui.main_window import MainWindow
from logger import logger
from pulsefire.clients import BaseClient

async def shutdown(window):
    try:
        if hasattr(window, 'league_client') and window.league_client:
            await window.league_client.close()
            logger.info("LeagueClient session closed gracefully.")
    except Exception as e:
        logger.error(f"Error during LeagueClient shutdown: {str(e)}", exc_info=True)

def main():
    try:
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon("urgot_icon.png"))
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        window = MainWindow()
        window.show()
        
        # Signal handler for graceful shutdown
        def handle_signal(*_):
            logger.info("Received termination signal. Shutting down...")
            try:
                loop.create_task(shutdown(window))
                loop.call_later(1, loop.stop)  # Give time for shutdown to complete
            except Exception as e:
                logger.error(f"Error during signal handling: {str(e)}", exc_info=True)
                loop.stop()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, handle_signal)
            except NotImplementedError:
                # add_signal_handler may not be implemented on Windows event loops
                signal.signal(sig, lambda *_: handle_signal())
        
        # Run the event loop
        with loop:
            loop.run_forever()
            
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        app.quit()

if __name__ == "__main__":
    main()

print(dir(BaseClient)) 