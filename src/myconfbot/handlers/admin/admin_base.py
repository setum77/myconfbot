# src\myconfbot\handlers\admin\admin_base.py

import logging
logger = logging.getLogger(__name__)

from abc import ABC, abstractmethod
from telebot import TeleBot
from telebot.types import Message, CallbackQuery

from src.myconfbot.config import Config
from src.myconfbot.utils.database import DatabaseManager
from src.myconfbot.handlers.shared.states_manager import StatesManager
from src.myconfbot.services.auth_service import AuthService


class BaseAdminHandler(ABC):
    """
    Базовый класс для административных обработчиков
    
    Args:
        bot: Экземпляр телеграм бота
        config: Конфигурация приложения  
        db_manager: Менеджер базы данных
    """    
    def __init__(self, bot: TeleBot, config: Config, db_manager: DatabaseManager) -> None:
        self.bot = bot
        self.config = config
        self.db_manager = db_manager
        self.states_manager = StatesManager()
        self.auth_service = AuthService(db_manager)
    
    @abstractmethod
    def register_handlers(self):
        """Регистрация обработчиков - должен быть реализован в потомках"""
        pass
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        return self.auth_service.is_admin(user_id)
    
    def _check_admin_access(self, callback: CallbackQuery = None, message: Message = None) -> bool:
        """Проверка прав администратора с отправкой сообщения об ошибке"""
        
        # Определяем, откуда пришел запрос
        if callback:
            user_id = callback.from_user.id  # Пользователь, который нажал кнопку
            request_type = "CALLBACK"
            chat_id = callback.message.chat.id if callback.message else callback.from_user.id
        else:
            user_id = message.from_user.id  # Пользователь, который отправил сообщение
            request_type = "MESSAGE"
            chat_id = message.chat.id if message else user_id
        
        # Отладочная информация
        print(f"Checking admin access for user_id: {user_id} (Type: {request_type})")
        
        # Пропускаем проверку для сообщений от самого бота
        if user_id == self.bot.get_me().id:
            print("Skipping admin check for bot itself")
            return True
        
        is_admin_result = self.is_admin(user_id)
        # Отладочная информация
        print(f"Is admin: {is_admin_result}")
        
        # Если пользователь не найден в базе, автоматически нет прав
        if is_admin_result is None:
            print(f"User {user_id} not found in database - access denied") # Отладочная информация
            is_admin_result = False
        
        if not is_admin_result:
            error_msg = "❌ Нет прав администратора"
            if callback:
                self.bot.answer_callback_query(callback.id, error_msg)
            else:
                self.bot.send_message(chat_id, error_msg)
            return False
        
        return True