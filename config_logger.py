import logging
import datetime

from config import LOGGING_LEVEL, LOGGING_DIR


LOG_FILE = LOGGING_DIR / f"llm_{datetime.date.today()}.log"

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(LOGGING_LEVEL)

    file_handler = logging.FileHandler(
        LOG_FILE,
        mode='a'
    )
    console_handler = logging.StreamHandler()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = get_logger('cli_llm')

