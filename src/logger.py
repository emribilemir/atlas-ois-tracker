from datetime import datetime
from collections import deque

class BotLogger:
    """Logger that stores logs in memory for Telegram access."""
    
    _logs = deque(maxlen=20)  # Keep last 20 logs to avoid spam
    
    @classmethod
    def log(cls, message: str, level: str = "INFO"):
        """Add a log entry."""
        time_str = datetime.now().strftime("%H:%M:%S")
        entry = f"{time_str} - [{level}] {message}"
        
        # Print to console (for Render logs)
        print(entry)
        
        # Add to memory (for Telegram /logs)
        cls._logs.append(entry)
    
    @classmethod
    def get_logs(cls) -> str:
        """Get all stored logs as a string."""
        if not cls._logs:
            return "📭 Henüz log kaydı yok."
        
        return "\n".join(cls._logs)

    @classmethod
    def error(cls, message: str):
        """Log an error."""
        cls.log(message, "ERROR")

    @classmethod
    def info(cls, message: str):
        """Log info."""
        cls.log(message, "INFO")
