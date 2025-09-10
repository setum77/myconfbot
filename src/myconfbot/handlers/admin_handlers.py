import telebot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from src.myconfbot.config import Config
from src.myconfbot.utils.database import db_manager
from src.myconfbot.models import OrderStatus

def register_admin_handlers(bot):
    """Регистрация обработчиков для администратора"""

    config = Config.load()
    
    def is_admin(user_id):
        """Проверка, является ли пользователь администратором"""
        return user_id in config.admin_ids
    
    @bot.message_handler(commands=['orders'])
    def show_orders(message: Message):
        """Показать активные заказы"""
        if not is_admin(message.from_user.id):
            return bot.send_message(message.chat.id, "❌ У вас нет прав для этой команды")
        
        orders = db_manager.get_active_orders()
        
        if not orders:
            return bot.send_message(message.chat.id, "📭 Нет активных заказов")
        
        response = "📋 Активные заказы:\n\n"
        for order in orders:
            response += f"🆔 Заказ #{order.id}\n"
            response += f"👤 Клиент: {order.customer.first_name or 'Не указано'}\n"
            response += f"📞 Телефон: {order.customer.phone or 'Не указан'}\n"
            response += f"📊 Статус: {order.status.value}\n"
            response += f"📅 Дата: {order.order_date.strftime('%d.%m.%Y %H:%M')}\n"
            if order.ready_date:
                response += f"✅ Готовность: {order.ready_date.strftime('%d.%m.%Y %H:%M')}\n"
            response += "─" * 20 + "\n"
        
        bot.send_message(message.chat.id, response)
    
    @bot.message_handler(commands=['admin', 'админ'])
    def admin_panel(message: Message):
        """Панель администратора"""
        if not is_admin(message.from_user.id):
            return
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("📋 Активные заказы", callback_data="admin_orders"),
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
        )
        keyboard.add(
            InlineKeyboardButton("🎂 Управление продукцией", callback_data="admin_products"),
            InlineKeyboardButton("📖 Управление рецептами", callback_data="admin_recipes")
        )
        
        bot.send_message(
            message.chat.id,
            "👨‍🍳 Панель администратора кондитера\n\n"
            "Выберите действие:",
            reply_markup=keyboard
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('order_status_'))
    def change_order_status(callback: CallbackQuery):
        """Изменение статуса заказа"""
        if not is_admin(callback.from_user.id):
            return bot.answer_callback_query(callback.id, "❌ Нет прав")
        
        try:
            _, order_id, new_status = callback.data.split('_')
            order_id = int(order_id)
            
            status_enum = OrderStatus(new_status)
            if db_manager.update_order_status(order_id, status_enum):
                bot.answer_callback_query(callback.id, f"✅ Статус обновлен на {new_status}")
                bot.edit_message_text(
                    f"Статус заказа #{order_id} изменен на {new_status}",
                    callback.message.chat.id,
                    callback.message.message_id
                )
            else:
                bot.answer_callback_query(callback.id, "❌ Заказ не найден")
                
        except Exception as e:
            bot.answer_callback_query(callback.id, "❌ Ошибка при обновлении")
    
def notify_admins_new_order(bot, order):
    """Уведомление админов о новом заказе"""
    message = f"🎉 НОВЫЙ ЗАКАЗ #{order.id}\n\n"
    message += f"👤 Клиент: {order.customer.first_name}\n"
    message += f"📞 Телефон: {order.customer.phone}\n"
    message += f"💬 Пожелания: {order.special_requests or 'Не указаны'}\n"
    message += f"💰 Сумма: {order.total_amount} руб.\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("✅ В работе", callback_data=f"order_status_{order.id}_in_progress"),
        InlineKeyboardButton("🚫 Отменить", callback_data=f"order_status_{order.id}_cancelled")
    )
    
    for admin_id in config.admin_ids:
        try:
            bot.send_message(admin_id, message, reply_markup=keyboard)
        except Exception as e:
            print(f"Не удалось отправить уведомление админу {admin_id}: {e}")