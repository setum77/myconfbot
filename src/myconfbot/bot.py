import os
import asyncio
import logging
import telebot

# from aiogram import Bot, Dispatcher
# from aiogram.client.default import DefaultBotProperties
# from aiogram.enums import ParseMode

from src.myconfbot.config import Config
from src.myconfbot.utils.database import db_manager
from src.myconfbot.handlers import register_handlers




class ConfectioneryBot:
    def __init__(self):
        # Настраиваем логирование через Config
        self.logger = Config.setup_logging()
        self.logger.info("Инициализация бота кондитера...")
        try:
            # Получаем токен
            self.token = Config.get_bot_token()
            self.logger.info("✓ Токен бота успешно получен")
            
            # Инициализируем базу данных
            self.db = db_manager
            self.logger.info("✓ База данных инициализирована")
            
            # Создаем экземпляр бота
            self.bot = telebot.TeleBot(
                self.token,
                parse_mode='HTML',
                threaded=True
            )
            self.logger.info("✓ Экземпляр бота создан")
            
            # Регистрируем обработчики
            register_handlers(self.bot)
            self.logger.info("✓ Обработчики зарегистрированы")
            
            self.logger.info("✓ Бот инициализирован успешно")
            
        except ValueError as e:
            self.logger.error("✗ Ошибка конфигурации: %s", e)
            raise
        except Exception as e:
            self.logger.critical("✗ Критическая ошибка при инициализации: %s", e, exc_info=True)
            raise

        # Отладочная информация
        try:
            config = Config.load()
            print(f"✅ Admin IDs: {config.admin_ids}")
            print(f"✅ Database path: {config.db.path}")
        except Exception as e:
            print(f"⚠️  Config error: {e}")
    
    def run(self):
        """Запуск бота"""
        try:
            self.logger.info("🚀 Запуск бота...")
            self.logger.info("Для остановки нажмите Ctrl+C")
            print("🎂 Бот кондитера запущен...")
            
            # Запускаем бота
            self.bot.infinity_polling(
                timeout=30,
                long_polling_timeout=30,
                logger_level=logging.INFO
            )
            
        except KeyboardInterrupt:
            self.logger.info("⏹️ Бот остановлен пользователем")
            print("\n⏹️ Бот остановлен")
            
        except Exception as e:
            self.logger.error("❌ Ошибка при работе бота: %s", e, exc_info=True)
            print(f"❌ Произошла ошибка: {e}")
            
        finally:
            self.logger.info("🔚 Бот завершил работу")
            print("Бот завершил работу")
    


def main():
    """Основная функция запуска"""
    try:
        bot = ConfectioneryBot()
        bot.run()
    except Exception as e:
        logging.critical("💥 Не удалось запустить бота: %s", e, exc_info=True)
        print(f"💥 Критическая ошибка: {e}")

# Обработчик необработанных исключений
def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """Обработчик необработанных исключений"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Для KeyboardInterrupt используем стандартный обработчик
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logging.critical("Необработанное исключение:", exc_info=(exc_type, exc_value, exc_traceback))

# Устанавливаем глобальный обработчик исключений
import sys
sys.excepthook = handle_uncaught_exception