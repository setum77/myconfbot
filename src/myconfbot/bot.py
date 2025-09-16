import os
import sys
import time
import asyncio
import logging
import telebot

from src.myconfbot.config import Config
from src.myconfbot.utils.database import db_manager
# from src.myconfbot.handlers import register_handlers
from src.myconfbot.handlers import (
    register_admin_handlers,
    register_main_handlers,
    register_order_handlers,
    register_recipe_handlers
)

class ConfectioneryBot:
    def __init__(self):
        # Настраиваем логирование через Config
        self.logger = Config.setup_logging()
        self.logger.info("Инициализация бота кондитера...")
        
        try:
            # Загружаем конфигурацию
            self.config = Config.load()
            self.logger.info("✓ Конфигурация загружена")
            
            # Получаем токен
            self.token = self.config.bot_token
            self.logger.info("✓ Токен бота успешно получен")
            
            # Инициализируем базу данных
            self.db = db_manager
            self.logger.info(f"✓ База данных инициализирована: {self.config.db.url}")
            
            # Логируем тип БД
            if self.config.db.use_postgres:
                self.logger.info("📊 Используется PostgreSQL")
            else:
                self.logger.info("📊 Используется SQLite")
            
            # Создаем экземпляр бота
            self.bot = telebot.TeleBot(
                self.token,
                parse_mode='HTML',
                threaded=True
            )
            self.logger.info("✓ Экземпляр бота создан")
            
            # Регистрируем обработчики
            self.register_handlers()
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
            print(f"✅ Admin IDs: {self.config.admin_ids}")
            print(f"✅ Use PostgreSQL: {self.config.db.use_postgres}")
            if self.config.db.use_postgres:
                print(f"✅ DB Host: {self.config.db.host}")
                print(f"✅ DB Name: {self.config.db.name}")
        except Exception as e:
            print(f"⚠️  Config error: {e}")
    
    def register_handlers(self):
        """Регистрация всех обработчиков"""
        register_main_handlers(self.bot)
        register_admin_handlers(self.bot) 
        register_order_handlers(self.bot)
        register_recipe_handlers(self.bot)

    def run(self):
        """Запуск бота"""
        try:
            self.logger.info("🚀 Запуск бота...")
            self.logger.info("Для остановки нажмите Ctrl+C")
            
            # Проверяем подключение к БД
            if not self.db.test_connection():
                self.logger.error("❌ Не удалось подключиться к базе данных")
                print("❌ Ошибка подключения к БД. Проверьте настройки.")
                return
            
            print("🎂 Бот кондитера запущен...")
            print(f"📊 База данных: {'PostgreSQL' if self.config.db.use_postgres else 'SQLite'}")
            
            # Запускаем бота c отработкой сетевых ошибок
            while True:
                try:
                    self.bot.infinity_polling(
                        timeout=30,
                        long_polling_timeout=30,
                        logger_level=logging.INFO,
                        skip_pending=True  # Пропускаем pending updates при перезапуске
                    )
                except ConnectionError as e:
                    self.logger.warning(f"📡 Сетевая ошибка: {e}. Перезапуск через 5 секунд...")
                    time.sleep(5)
                except Exception as e:
                    self.logger.error(f"❌ Ошибка при работе бота:  {e}")
                    print(f"❌ Ошибка при работе бота: {e}. Перезапуск через 5 секунд...")
                    time.sleep(5)
            
        except KeyboardInterrupt:
            self.logger.info("⏹️ Бот остановлен пользователем")
            print("Бот остановлен пользователем")   
            
        except Exception as e:
            self.logger.error("❌ Критическая ошибка: %s", e, exc_info=True)
            print(f"❌ Критическая ошибка: {e}")
            
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

if __name__ == "__main__":
    main()