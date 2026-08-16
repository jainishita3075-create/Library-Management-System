import logging
import os

# Resolve App.log path relative to Backend root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_LOG_FILE = os.path.join(BASE_DIR, "App.log")
LOG_FILE = os.getenv("LOG_FILE", DEFAULT_LOG_FILE)

def get_logger(name: str):
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 1. Console Stream Handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # 2. File Handler writing to App.log
        try:
            log_path = os.getenv("LOG_FILE", DEFAULT_LOG_FILE)
            fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception as e:
            logger.warning(f"Could not initialize FileHandler for {LOG_FILE}: {e}")
        
    return logger

loggers = get_logger("AppLogger")