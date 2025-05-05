import logging
import os

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/urgot_matchup_helper.log'),
        logging.StreamHandler()
    ]
)

# Create logger instance
logger = logging.getLogger('urgot_matchup_helper') 