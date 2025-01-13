import logging
from logging.handlers import RotatingFileHandler
import sys
import datetime

from config import LOGGING_LEVEL, LOGGING_DIR


LOG_FILE = LOGGING_DIR / f"llm_{datetime.date.today()}.log"

def get_logger(name):
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Remove any existing handlers
    logger.handlers = []
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # File handler (with rotation)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        mode='a'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOGGING_LEVEL)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Create stderr handler
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(detailed_formatter)
    logger.addHandler(stderr_handler)
    
    # Set up exception handling
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Call the default handler for keyboard interrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.error("Uncaught exception:", 
                    exc_info=(exc_type, exc_value, exc_traceback))
    
    # Install exception handler
    sys.excepthook = handle_exception
    
    return logger

logger = get_logger('cli_llm')
