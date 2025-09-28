# src/myconfbot/handlers/user/order_callbacks.py

import logging
from telebot.types import CallbackQuery

logger = logging.getLogger(__name__)

class OrderCallbacks:
    """Дополнительные callback обработчики для заказов"""
    
    def __init__(self, bot, order_handler):
        self.bot = bot
        self.order_handler = order_handler
    
    def register_callbacks(self):
        """Регистрация дополнительных callback'ов"""
        
        @self.bot.callback_query_handler(func=lambda call: call.data == 'order_back_categories')
        def handle_back_to_categories(callback: CallbackQuery):
            self.order_handler.start_order_process(callback.message)
            self.bot.answer_callback_query(callback.id)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_back_to_category_'))
        def handle_back_to_category(callback: CallbackQuery):
            category_id = int(callback.data.replace('order_back_to_category_', ''))
            # TODO: Реализовать возврат к товарам категории
            self.bot.answer_callback_query(callback.id)