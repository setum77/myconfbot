# src\myconfbot\bot\confectionery_bot.py

import logging
logger = logging.getLogger(__name__)

import os
from typing import Optional

import telebot
from dotenv import load_dotenv

from src.myconfbot.config import Config
logger = logging.getLogger(__name__)

from src.myconfbot.utils.database import db_manager
from src.myconfbot.handlers import HandlerFactory
from src.myconfbot.handlers.user.order_handler import OrderHandler
from src.myconfbot.handlers.user.my_order_handler import MyOrderHandler
from src.myconfbot.handlers.admin.order_admin_handler import OrderAdminHandler


# Загрузка переменных окружения
load_dotenv()




class ConfectioneryBot:
    def __init__(self, token: str, config: Config):
        self.bot = telebot.TeleBot(token)
        self.config = config
        self.handler_factory = HandlerFactory(self.bot, self.config, db_manager)
        self.setup_handlers()
        order_handler = OrderHandler(self.bot, self.config, db_manager)
        order_handler.register_handlers()
        my_order_handler = MyOrderHandler(self.bot, config, db_manager)
        my_order_handler.register_handlers()
        order_admin_handler = OrderAdminHandler(self.bot, config, db_manager)
        order_admin_handler.register_handlers()
        
        logger.info("Бот инициализирован")

    def setup_handlers(self):
        """Настройка обработчиков через фабрику"""
        self.handler_factory.register_all_handlers()
        logger.info("Все обработчики зарегистрированы")

    def run(self):
        """Запуск бота"""
        logger.info("Запуск бота...")
        self.bot.infinity_polling()


def create_bot() -> ConfectioneryBot:
    """Фабричная функция для создания бота"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
    
    config = Config()
    return ConfectioneryBot(token, config)


def main():
    """Основная функция запуска бота"""
    
    try:
        # Инициализация базы данных
        db_manager.init_db()
        logger.info("База данных инициализирована")
        
        # Создание и запуск бота
        bot = create_bot()
        bot.run()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise


if __name__ == "__main__":
    main()