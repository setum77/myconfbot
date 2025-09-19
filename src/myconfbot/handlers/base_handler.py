from abc import ABC, abstractmethod
from telebot import TeleBot

class BaseHandler(ABC):
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.states_manager = StatesManager()  # Централизованный менеджер состояний
    
    @abstractmethod
    def register_handlers(self):
        pass
    
    def is_admin(self, user_id):
        # Единая реализация проверки прав
        user = db_manager.get_user_by_telegram_id(user_id)
        return user.is_admin if user else False