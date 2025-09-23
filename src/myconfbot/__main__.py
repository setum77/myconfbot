import logging.config
from .logging_config import setup_logging

# 🔴 ВАЖНО: вызываем setup_logging() ПЕРЕД импортом остальных модулей!
setup_logging()

import sys
from src.myconfbot.config import Config

def main():
    """Основная точка входа для запуска как модуля"""
    try:
        # python -m src.myconfbot
        from src.myconfbot.bot.confectionery_bot import create_bot
        bot = create_bot()
        bot.run()
    except Exception as e:
        logging.critical(f"💥 Ошибка запуска: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()