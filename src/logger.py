import logging
import os
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging
log_file = 'logs/urgot_matchup_helper.log'
max_bytes = 5 * 1024 * 1024  # 5MB
backup_count = 3  # Keep 3 backup files

# Create rotating file handler
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=max_bytes,
    backupCount=backup_count
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        file_handler,
        logging.StreamHandler()
    ]
)

# Create logger instance
logger = logging.getLogger('urgot_matchup_helper') 