"""
OIS Grade Checker - Main entry point.
"""
from src.telegram_bot import GradeCheckerBot


def main():
    """Run the grade checker bot."""
    bot = GradeCheckerBot()
    bot.run()


if __name__ == "__main__":
    main()
