"""
OIS Grade Checker - Main entry point.
"""
from src.telegram_bot import GradeCheckerBot
from src.keep_alive import keep_alive
from src.monitor import start_monitoring


def main():
    """Run the grade checker bot."""
    # Start Keep-Alive server for Render (binds to PORT)
    keep_alive()
    
    # Start Resource Monitoring (RAM/CPU logs)
    start_monitoring(interval=60)
    
    bot = GradeCheckerBot()
    bot.run()


if __name__ == "__main__":
    main()
