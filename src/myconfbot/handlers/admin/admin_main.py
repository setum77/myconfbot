import logging
from telebot import types
from telebot.types import Message, CallbackQuery
from .admin_base import BaseAdminHandler

logger = logging.getLogger(__name__)

class AdminMainHandler(BaseAdminHandler):
    """Обработчик главного меню администратора"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
        self.logger = logging.getLogger(__name__)
    
    def register_handlers(self):
        """Регистрация обработчиков главного меню"""
        self._register_admin_callbacks()
        self._register_back_handler()
        self._register_admin_commands()

    def _register_admin_commands(self):
        """Регистрация команд админки"""
        @self.bot.message_handler(commands=['admin'])
        def handle_admin(message: Message):
            self.handle_admin_panel(message)
    
    def _register_admin_callbacks(self):
        """Регистрация callback'ов админского меню"""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
        def handle_admin_callbacks(callback: CallbackQuery):
            self._handle_admin_callbacks(callback)
    
    def _register_back_handler(self):
        """Регистрация обработчика кнопки 'Назад'"""
        @self.bot.callback_query_handler(func=lambda call: call.data == 'admin_back')
        def back_to_admin_main(callback: CallbackQuery):
            self._back_to_admin_main(callback)
    
    def _handle_admin_callbacks(self, callback: CallbackQuery):
        """Обработка callback'ов админского меню"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            data = callback.data
            
            if data == 'admin_orders_active':
                self._show_active_orders(callback.message)
            elif data == 'admin_orders_all':
                self._show_all_orders(callback.message)
            elif data == 'admin_orders_change_status':
                self._show_change_status(callback.message)
            elif data == 'admin_orders_stats':
                self._show_orders_stats(callback.message)
            elif data == 'admin_stats_general':
                self._show_general_stats(callback.message)
            elif data == 'admin_stats_financial':
                self._show_financial_stats(callback.message)
            elif data == 'admin_stats_clients':
                self._show_clients_stats(callback.message)
            elif data == 'admin_stats_products':
                self._show_products_stats(callback.message)
            elif data == 'admin_manage_products':
                self._manage_products(callback.message)
            elif data == 'admin_manage_recipes':
                self._manage_recipes(callback.message)
            elif data == 'admin_manage_services':
                self._manage_services(callback.message)
            elif data == 'admin_manage_contacts':
                self._manage_contacts(callback.message)
            elif data == 'admin_manage_content':
                self._manage_content(callback.message)
            elif data == 'admin_manage_users':
                self._manage_users(callback.message)
            elif data == 'admin_back':
                self._back_to_admin_main(callback)
                
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            self.logger.error(f"Ошибка в admin callback: {e}", exc_info=True)
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при обработке")
    
    def _show_active_orders(self, message: Message):
        """Показать активные заказы"""
        from .order_management import OrderManagementHandler
        order_handler = OrderManagementHandler(self.bot, self.config, self.db_manager)
        order_handler.show_active_orders(message)
    
    def _show_all_orders(self, message: Message):
        """Показать все заказы"""
        self.bot.send_message(message.chat.id, "📋 Функция показа всех заказов в разработке")
    
    def _show_change_status(self, message: Message):
        """Показать интерфейс изменения статуса"""
        self.bot.send_message(message.chat.id, "🔄 Функция изменения статуса в разработке")
    
    def _show_orders_stats(self, message: Message):
        """Показать статистику заказов"""
        from .stats_management import StatsHandler
        stats_handler = StatsHandler(self.bot, self.config, self.db_manager)
        stats_handler.show_orders_stats(message)
    
    def _show_general_stats(self, message: Message):
        """Общая статистика"""
        self.bot.send_message(message.chat.id, "📊 Общая статистика в разработке")
    
    def _show_financial_stats(self, message: Message):
        """Финансовая статистика"""
        self.bot.send_message(message.chat.id, "💰 Финансовая статистика в разработке")
    
    def _show_clients_stats(self, message: Message):
        """Статистика по клиентам"""
        self.bot.send_message(message.chat.id, "👥 Статистика клиентов в разработке")
    
    def _show_products_stats(self, message: Message):
        """Статистика по товарам"""
        self.bot.send_message(message.chat.id, "🎂 Статистика товаров в разработке")
    
    def _manage_products(self, message: Message):
        """Управление продукцией"""
        from .product_management import ProductManagementHandler
        product_handler = ProductManagementHandler(self.bot, self.config, self.db_manager)
        product_handler.manage_products(message)
    
    def _manage_recipes(self, message: Message):
        """Управление рецептами"""
        self.bot.send_message(message.chat.id, "📖 Управление рецептами в разработке")
    
    def _manage_services(self, message: Message):
        """Управление услугами"""
        self.bot.send_message(message.chat.id, "💼 Управление услугами в разработке")
    
    def _manage_contacts(self, message: Message):
        """Управление контактами"""
        self.bot.send_message(message.chat.id, "📞 Управление контактами в разработке")
    
    def _manage_content(self, message: Message):
        """Управление контентом"""
        from .content_management import ContentManagementHandler
        content_handler = ContentManagementHandler(self.bot, self.config, self.db_manager)
        content_handler.manage_content(message)
    
    def _manage_users(self, message: Message):
        """Управление пользователями"""
        from .user_management import UserManagementHandler
        user_handler = UserManagementHandler(self.bot, self.config, self.db_manager)
        user_handler.manage_users(message)
    
    def _back_to_admin_main(self, callback: CallbackQuery):
        """Возврат в главное меню администратора"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            # Удаляем текущее сообщение
            self.bot.delete_message(callback.message.chat.id, callback.message.message_id)
            
            # Показываем панель управления
            self._show_management_panel(callback.message)
            
            self.bot.answer_callback_query(callback.id, "🔙 Возврат в главное меню")
                
        except Exception as e:
            self.logger.error(f"Ошибка при возврате в меню управления: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при возврате")
    
    def _show_management_panel(self, message: Message):
        """Показ панели управления"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("🎂 Продукция", callback_data="admin_manage_products"),
            types.InlineKeyboardButton("📖 Рецепты", callback_data="admin_manage_recipes")
        )
        keyboard.add(
            types.InlineKeyboardButton("💼 Услуги", callback_data="admin_manage_services"),
            types.InlineKeyboardButton("📞 Контакты", callback_data="admin_manage_contacts")
        )
        keyboard.add(
            types.InlineKeyboardButton("📄 Контент", callback_data="admin_manage_content"),
            types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_manage_users")
        )
        
        self.bot.send_message(
            message.chat.id,
            "🏪 Панель управления\nВыберите раздел:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )