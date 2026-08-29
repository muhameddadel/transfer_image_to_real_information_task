import sys
from pathlib import Path
from datetime import datetime
from loguru import logger
from src.config import Config


def setup_logger():
    """Setup logging configuration"""
    Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    Config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.remove()
    
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level="DEBUG"
    )
    
    log_file = Config.LOGS_DIR / f"fakturama_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger.add(
        str(log_file),
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )
    
    error_file = Config.LOGS_DIR / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    logger.add(
        str(error_file),
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        retention="30 days"
    )
    
    logger.info("Logger initialized")
    
    return logger


def capture_screenshot(name: str = "screenshot"):
    """Capture screenshot for debugging"""
    try:
        import pyautogui
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = Config.SCREENSHOTS_DIR / f"{name}_{timestamp}.png"
        pyautogui.screenshot(str(filename))
        logger.debug(f"Screenshot saved: {filename}")
        return str(filename)
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
        return None