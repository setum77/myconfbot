# src\myconfbot\handlers\user\base_user_handler.py

import logging
from abc import ABC, abstractmethod
from telebot import TeleBot
from telebot.types import Message

from src.myconfbot.config import Config
from src.myconfbot.utils.database import DatabaseManager
from src.myconfbot.handlers.shared.states_manager import StatesManager
from src.myconfbot.services.user_service import UserService
from src.myconfbot.services.auth_service import AuthService
from src.myconfbot.keyboards.user_keyboards import UserKeyboards


class BaseUserHandler(ABC):
    """Базовый класс для всех пользовательских обработчиков"""
    
    def __init__(self, bot: TeleBot, config: Config, db_manager: DatabaseManager):
        self.bot = bot
        self.config = config
        self.db_manager = db_manager
        self.states_manager = StatesManager()
        self.auth_service = AuthService(db_manager)
        self.user_service = UserService(db_manager)
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def register_handlers(self):
        """Регистрация обработчиков - должен быть реализован в потомках"""
        pass
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        return self.auth_service.is_admin(user_id)
    
    def show_main_menu(self, chat_id: int, is_admin: bool = False):
        """Показать главное меню"""
        markup = UserKeyboards.get_main_menu(is_admin)
        return markup
    
    def send_formatted_message(self, chat_id: int, content: str, parse_mode: str = 'MarkdownV2'):
        """
        Безопасная отправка сообщения с обработкой ошибок форматирования
        
        Args:
            chat_id: ID чата
            content: Текст сообщения
            parse_mode: Режим парсинга
        """
        try:
            self.bot.send_message(chat_id, content, parse_mode=parse_mode)
        except Exception as e:
            if "parse entities" in str(e):
                # Ошибка форматирования - отправляем как plain text
                error_msg = "⚠️ Ошибка форматирования текста. Отображаю как обычный текст."
                self.bot.send_message(chat_id, error_msg)
                self.bot.send_message(chat_id, content)  # plain text
            else:
                raise