import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    FAKTURAMA_WINDOW_TITLE = "Fakturama"
    FAKTURAMA_PROCESS_NAME = "Fakturama"
    
    OCR_LANGUAGE = "eng"
    OCR_CONFIDENCE_THRESHOLD = 80
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = "gpt-4o"
    LLM_TEMPERATURE = 0.1
    
    ELEMENT_TIMEOUT = 10
    RETRY_COUNT = 3
    RETRY_DELAY = 1
    
    TOTAL_TOLERANCE = 0.02
    
    BASE_DIR = Path(__file__).parent.parent
    LOGS_DIR = BASE_DIR / "logs"
    SCREENSHOTS_DIR = BASE_DIR / "screenshots"
    
    PAYMENT_CODE_MAP = {
        "Bank Transfer": "Credit transfer",
        "Credit Card": "Credit card",
        "SEPA Direct Debit": "SEPA direct debit",
        "Cash": "Cash",
        "Check": "Check"
    }
    
    DEFAULT_VAT_COUNTRY = "DE"
    COUNTRY_VAT_MAP = {
        "DE": 19,
        "AT": 20,
        "FR": 20,
        "NL": 21,
        "BE": 21,
        "IT": 22,
        "ES": 21,
        "GB": 20,
        "CH": 7.7,
        "US": 0
    }