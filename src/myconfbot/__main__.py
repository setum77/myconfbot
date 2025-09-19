# # from src.myconfbot.bot import main

# # if __name__ == "__main__":
# #     main()


# import sys
# import logging
# from src.myconfbot.bot.confectionery_bot import create_bot

# def main():
#     """Основная точка входа для запуска как модуля"""
#     try:
#         # python -m src.myconfbot
#         bot = create_bot()
#         bot.run()
#     except Exception as e:
#         logging.critical(f"💥 Ошибка запуска: {e}", exc_info=True)
#         sys.exit(1)

# if __name__ == "__main__":
#     main()

import sys
import logging
from src.myconfbot.bot.confectionery_bot import create_bot

def main():
    """Основная точка входа для запуска как модуля"""
    try:
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('bot.log', encoding='utf-8')
            ]
        )
        
        # python -m src.myconfbot
        bot = create_bot()
        bot.run()
    except Exception as e:
        logging.critical(f"💥 Ошибка запуска: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

# import sys
# import logging
# from src.myconfbot.bot.confectionery_bot import create_bot

# def main():
#     """Основная точка входа для запуска как модуля"""
#     try:
#         # python -m src.myconfbot
#         bot = create_bot()
#         bot.run()
#     except Exception as e:
#         logging.critical(f"💥 Ошибка запуска: {e}", exc_info=True)
#         print(f"💥 Критическая ошибка: {e}")
#         sys.exit(1)

# if __name__ == "__main__":
#     main()