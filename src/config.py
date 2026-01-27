"""
Configuration module - loads and validates environment variables.
"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Config:
    """Application configuration from environment variables."""
    
    # OIS Credentials
    OIS_USERNAME: str = os.getenv("OIS_USERNAME", "")
    OIS_PASSWORD: str = os.getenv("OIS_PASSWORD", "")
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Settings
    CHECK_INTERVAL: int = int(os.getenv("CHECK_INTERVAL", "300"))
    
    # URLs
    OIS_BASE_URL: str = "https://ois.atlas.edu.tr"
    OIS_LOGIN_URL: str = f"{OIS_BASE_URL}/auth/login"
    OIS_CAPTCHA_URL: str = f"{OIS_BASE_URL}/auth/captcha"
    OIS_GRADES_URL: str = f"{OIS_BASE_URL}/ogrenciler/belge/ogrsinavsonuc"
    
    # Paths
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    GRADES_FILE: str = os.path.join(DATA_DIR, "grades.json")
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration. Returns list of missing fields."""
        missing = []
        if not cls.OIS_USERNAME:
            missing.append("OIS_USERNAME")
        if not cls.OIS_PASSWORD:
            missing.append("OIS_PASSWORD")
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not cls.TELEGRAM_CHAT_ID:
            missing.append("TELEGRAM_CHAT_ID")
        return missing
    
    @classmethod
    def is_valid(cls) -> bool:
        """Check if all required configuration is present."""
        return len(cls.validate()) == 0


# Create data directory if it doesn't exist
os.makedirs(Config.DATA_DIR, exist_ok=True)
