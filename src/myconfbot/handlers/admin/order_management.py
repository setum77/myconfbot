import logging
from telebot import types
from telebot.types import Message, CallbackQuery

from .admin_base import BaseAdminHandler
from src.myconfbot.models import OrderStatus


class OrderManagementHandler(BaseAdminHandler):
    """Обработчик управления заказами"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
        self.logger = logging.getLogger(__name__)
    
    def register_handlers(self):
        """Регистрация обработчиков управления заказами"""
        self._register_order_status_handlers()
    
    def _register_order_status_handlers(self):
        """Регистрация обработчиков изменения статуса заказов"""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('status_'))
        def change_order_status(callback: CallbackQuery):
            self._change_order_status(callback)
    
    def show_active_orders(self, message: Message):
        """Показать активные заказы"""
        if not self._check_admin_access(message=message):
            return
        
        orders = self.db_manager.get_orders_by_status([OrderStatus.NEW, OrderStatus.IN_PROGRESS])
        
        if not orders:
            self.bot.send_message(message.chat.id, "📭 Нет активных заказов")
            return
        
        response = "📋 Активные заказы:\n\n"
        for order in orders:
            response += f"🆔 #{order.id} | {order.status.value}\n"
            response += f"👤 {order.user.full_name}\n"
            response += f"📞 {order.user.phone or 'Не указан'}\n"
            response += f"📅 {order.order_date.strftime('%d.%m.%Y %H:%M')}\n"
            response += f"💰 {order.total_amount} руб.\n"
            
            # Кнопки для управления статусом
            keyboard = types.InlineKeyboardMarkup()
            if order.status == OrderStatus.NEW:
                keyboard.add(types.InlineKeyboardButton("✅ В работу", callback_data=f"status_{order.id}_in_progress"))
            elif order.status == OrderStatus.IN_PROGRESS:
                keyboard.add(types.InlineKeyboardButton("✅ Готово", callback_data=f"status_{order.id}_ready"))
            keyboard.add(types.InlineKeyboardButton("🚫 Отменить", callback_data=f"status_{order.id}_cancelled"))
            
            self.bot.send_message(message.chat.id, response, reply_markup=keyboard)
            response = ""
    
    def _change_order_status(self, callback: CallbackQuery):
        """Изменение статуса заказа"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            _, order_id, new_status = callback.data.split('_')
            order_id = int(order_id)
            
            status_enum = OrderStatus(new_status)
            if self.db_manager.update_order_status(order_id, status_enum):
                self.bot.answer_callback_query(callback.id, f"✅ Статус обновлен")
                self.bot.edit_message_text(
                    f"Статус заказа #{order_id} изменен на {new_status}",
                    callback.message.chat.id,
                    callback.message.message_id
                )
            else:
                self.bot.answer_callback_query(callback.id, "❌ Заказ не найден")
                
        except Exception as e:
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при обновлении")
            self.logger.error(f"Ошибка изменения статуса: {e}", exc_info=True)