from telebot import TeleBot
from src.myconfbot.config import Config
from src.myconfbot.utils.database import DatabaseManager

class HandlerFactory:
    """Фабрика для регистрации всех обработчиков"""
    
    def __init__(self, bot: TeleBot, config: Config, db_manager: DatabaseManager):
        self.bot = bot
        self.config = config
        self.db_manager = db_manager
        self._handlers = []
    
    def register_all_handlers(self):
        """Регистрация всех обработчиков"""
        # Будем реализовывать постепенно
        self._register_user_handlers()
        self._register_admin_handlers()
        self._register_order_handlers()
        self._register_recipe_handlers()
    
    def _register_user_handlers(self):
        """Регистрация пользовательских обработчиков"""
        from .user.main_handlers import MainHandler
        from .user.profile_handlers import ProfileHandler
        from .user.auth_handlers import AuthHandler
        
        handlers = [
            MainHandler(self.bot, self.config, self.db_manager),
            ProfileHandler(self.bot, self.config, self.db_manager),
            AuthHandler(self.bot, self.config, self.db_manager)
        ]
        
        for handler in handlers:
            handler.register_handlers()
            self._handlers.append(handler)
    
    def _register_admin_handlers(self):
        """Регистрация административных обработчиков"""
        from .admin.admin_main import AdminMainHandler
        from .admin.user_management import UserManagementHandler
        from .admin.order_management import OrderManagementHandler
        from .admin.content_management import ContentManagementHandler
        from .admin.product_management import ProductManagementHandler
        from .admin.stats_management import StatsHandler
    
        handlers = [
            AdminMainHandler(self.bot, self.config, self.db_manager),
            UserManagementHandler(self.bot, self.config, self.db_manager),
            OrderManagementHandler(self.bot, self.config, self.db_manager),
            ContentManagementHandler(self.bot, self.config, self.db_manager),
            ProductManagementHandler(self.bot, self.config, self.db_manager),
            StatsHandler(self.bot, self.config, self.db_manager)
        ]
    
        for handler in handlers:
            handler.register_handlers()
            self._handlers.append(handler)
    
    def _register_order_handlers(self):
        """Регистрация обработчиков заказов"""
        from .user.order_handlers import OrderHandler
        handler = OrderHandler(self.bot, self.config, self.db_manager)
        handler.register_handlers()
        self._handlers.append(handler)

    def _register_recipe_handlers(self):
        """Регистрация обработчиков рецептов"""
        from .user.recipe_handlers import RecipeHandler
        handler = RecipeHandler(self.bot, self.config, self.db_manager)
        handler.register_handlers()
        self._handlers.append(handler)    
            
    def get_handlers(self):
        """Получить все зарегистрированные обработчики"""
        return self._handlers