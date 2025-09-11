import telebot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from src.myconfbot.config import Config
from src.myconfbot.utils.database import db_manager
from src.myconfbot.models import OrderStatus
from src.myconfbot.utils.content_manager import content_manager

def register_admin_handlers(bot):
    """Регистрация обработчиков для администратора"""
    
    config = Config.load()
    
    def is_admin(user_id):
        """Проверка, является ли пользователь администратором"""
        return user_id in config.admin_ids
    
    # Обработчики callback-запросов для inline-кнопок
    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
    def handle_admin_callbacks(callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return bot.answer_callback_query(callback.id, "❌ Нет прав администратора")
        
        try:
            data = callback.data
            
            if data == 'admin_orders_active':
                show_active_orders(callback.message)
            elif data == 'admin_orders_all':
                show_all_orders(callback.message)
            elif data == 'admin_orders_change_status':
                show_change_status(callback.message)
            elif data == 'admin_orders_stats':
                show_orders_stats(callback.message)
            elif data == 'admin_stats_general':
                show_general_stats(callback.message)
            elif data == 'admin_stats_financial':
                show_financial_stats(callback.message)
            elif data == 'admin_stats_clients':
                show_clients_stats(callback.message)
            elif data == 'admin_stats_products':
                show_products_stats(callback.message)
            elif data == 'admin_manage_products':
                manage_products(callback.message)
            elif data == 'admin_manage_recipes':
                manage_recipes(callback.message)
            elif data == 'admin_manage_services':
                manage_services(callback.message)
            elif data == 'admin_manage_contacts':
                manage_contacts(callback.message)
            elif data == 'admin_manage_content':
                manage_content(callback.message)    
            elif data == 'admin_manage_admins':
                manage_admins(callback.message)
                
            bot.answer_callback_query(callback.id)
            
        except Exception as e:
            bot.answer_callback_query(callback.id, "❌ Ошибка при обработке")
            logging.error(f"Ошибка в admin callback: {e}")
    
    def show_active_orders(message):
        """Показать активные заказы"""
        orders = db_manager.get_orders_by_status([OrderStatus.NEW, OrderStatus.IN_PROGRESS])
        
        if not orders:
            bot.send_message(message.chat.id, "📭 Нет активных заказов")
            return
        
        response = "📋 Активные заказы:\n\n"
        for order in orders:
            response += f"🆔 #{order.id} | {order.status.value}\n"
            response += f"👤 {order.customer.first_name}\n"
            response += f"📞 {order.customer.phone or 'Не указан'}\n"
            response += f"📅 {order.order_date.strftime('%d.%m.%Y %H:%M')}\n"
            response += f"💰 {order.total_amount} руб.\n"
            
            # Кнопки для управления статусом
            keyboard = InlineKeyboardMarkup()
            if order.status == OrderStatus.NEW:
                keyboard.add(InlineKeyboardButton("✅ В работу", callback_data=f"status_{order.id}_in_progress"))
            elif order.status == OrderStatus.IN_PROGRESS:
                keyboard.add(InlineKeyboardButton("✅ Готово", callback_data=f"status_{order.id}_ready"))
            keyboard.add(InlineKeyboardButton("🚫 Отменить", callback_data=f"status_{order.id}_cancelled"))
            
            bot.send_message(message.chat.id, response, reply_markup=keyboard)
            response = ""
    
    def show_all_orders(message):
        """Показать все заказы"""
        # Реализация показа всех заказов
        bot.send_message(message.chat.id, "📋 Функция показа всех заказов в разработке")
    
    def show_change_status(message):
        """Показать интерфейс изменения статуса"""
        bot.send_message(message.chat.id, "🔄 Функция изменения статуса в разработке")
    
    def show_orders_stats(message):
        """Показать статистику заказов"""
        # Реализация статистики
        stats = db_manager.get_orders_statistics()
        
        response = "📈 Статистика заказов:\n\n"
        response += f"📊 Всего заказов: {stats['total']}\n"
        response += f"✅ Выполнено: {stats['completed']}\n"
        response += f"🔄 В работе: {stats['in_progress']}\n"
        response += f"🆕 Новые: {stats['new']}\n"
        response += f"💰 Общая сумма: {stats['total_amount']} руб.\n"
        
        bot.send_message(message.chat.id, response)
    
    def show_general_stats(message):
        """Общая статистика"""
        bot.send_message(message.chat.id, "📊 Общая статистика в разработке")
    
    def show_financial_stats(message):
        """Финансовая статистика"""
        bot.send_message(message.chat.id, "💰 Финансовая статистика в разработке")
    
    def show_clients_stats(message):
        """Статистика по клиентам"""
        bot.send_message(message.chat.id, "👥 Статистика клиентов в разработке")
    
    def show_products_stats(message):
        """Статистика по товарам"""
        bot.send_message(message.chat.id, "🎂 Статистика товаров в разработке")
    
    def manage_products(message):
        """Управление продукцией"""
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("➕ Добавить товар", callback_data="product_add"),
            InlineKeyboardButton("✏️ Редактировать", callback_data="product_edit")
        )
        keyboard.add(
            InlineKeyboardButton("👀 Просмотреть", callback_data="product_view"),
            InlineKeyboardButton("🚫 Удалить", callback_data="product_delete")
        )
        
        bot.send_message(
            message.chat.id,
            "🎂 Управление продукцией\nВыберите действие:",
            reply_markup=keyboard
        )
    
    def manage_recipes(message):
        """Управление рецептами"""
        bot.send_message(message.chat.id, "📖 Управление рецептами в разработке")
    
    def manage_services(message):
        """Управление услугами"""
        bot.send_message(message.chat.id, "💼 Управление услугами в разработке")
    
    def manage_contacts(message):
        """Управление контактами"""
        bot.send_message(message.chat.id, "📞 Управление контактами в разработке")
    
    def manage_admins(message):
        """Управление администраторами"""
        bot.send_message(message.chat.id, "👥 Управление администраторами в разработке")
    
    # Обработчики изменения статуса заказов
    @bot.callback_query_handler(func=lambda call: call.data.startswith('status_'))
    def change_order_status(callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return bot.answer_callback_query(callback.id, "❌ Нет прав")
        
        try:
            _, order_id, new_status = callback.data.split('_')
            order_id = int(order_id)
            
            status_enum = OrderStatus(new_status)
            if db_manager.update_order_status(order_id, status_enum):
                bot.answer_callback_query(callback.id, f"✅ Статус обновлен")
                bot.edit_message_text(
                    f"Статус заказа #{order_id} изменен на {new_status}",
                    callback.message.chat.id,
                    callback.message.message_id
                )
            else:
                bot.answer_callback_query(callback.id, "❌ Заказ не найден")
                
        except Exception as e:
            bot.answer_callback_query(callback.id, "❌ Ошибка при обновлении")
            logging.error(f"Ошибка изменения статуса: {e}")
    
    
    # Управление контентом (приветственный текст, контакты и т.д.)
    def manage_content(message):
        """Управление контентом"""
        keyboard = InlineKeyboardMarkup()
        
        files = content_manager.get_file_list()
        for filename in files:
            keyboard.add(InlineKeyboardButton(
                f"📝 {filename}", 
                callback_data=f"edit_content_{filename}"
            ))
        
        bot.send_message(
            message.chat.id,
            "📄 Управление контентом\nВыберите файл для редактирования:",
            reply_markup=keyboard
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('edit_content_'))
    def edit_content_callback(callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return bot.answer_callback_query(callback.id, "❌ Нет прав")
        
        filename = callback.data.replace('edit_content_', '')
        current_content = content_manager.get_content(filename)
        
        # Сохраняем состояние редактирования
        user_states[callback.from_user.id] = {
            'state': 'editing_content',
            'filename': filename,
            'message_id': callback.message.message_id
        }
        
        bot.edit_message_text(
            f"📝 Редактирование {filename}\n\nТекущее содержимое:\n\n{current_content}\n\nОтправьте новый текст:",
            callback.message.chat.id,
            callback.message.message_id
        )
    
    # Обработчик для приема нового контента
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'editing_content')
    def handle_content_edit(message):
        user_id = message.from_user.id
        user_state = user_states.get(user_id, {})
        filename = user_state.get('filename')
        
        if filename and content_manager.update_content(filename, message.text):
            bot.send_message(message.chat.id, f"✅ Файл {filename} успешно обновлен!")
            
            # Удаляем состояние редактирования
            user_states.pop(user_id, None)
            
            # Возвращаемся к управлению контентом
            manage_content(message)
        else:
            bot.send_message(message.chat.id, "❌ Ошибка при сохранении файла")
    
    # Можно добавить предпросмотр
    @bot.callback_query_handler(func=lambda call: call.data.startswith('preview_content_'))
    def preview_content(callback: CallbackQuery):
        filename = callback.data.replace('preview_content_', '')
        content = content_manager.get_content(filename)
        
        bot.send_message(
            callback.message.chat.id,
            f"👀 Предпросмотр {filename}:\n\n{content}",
            parse_mode='Markdown'  # Если поддерживается
        )

def notify_admins_new_order(bot, order):
    """Уведомление админов о новом заказе"""
    config = Config.load()
    
    message = f"🎉 НОВЫЙ ЗАКАЗ #{order.id}\n\n"
    message += f"👤 Клиент: {order.customer.first_name}\n"
    message += f"📞 Телефон: {order.customer.phone}\n"
    message += f"💬 Пожелания: {order.special_requests or 'Не указаны'}\n"
    message += f"💰 Сумма: {order.total_amount} руб.\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("✅ В работу", callback_data=f"status_{order.id}_in_progress"),
        InlineKeyboardButton("🚫 Отменить", callback_data=f"status_{order.id}_cancelled")
    )
    
    for admin_id in config.admin_ids:
        try:
            bot.send_message(admin_id, message, reply_markup=keyboard)
        except Exception as e:
            print(f"Не удалось отправить уведомление админу {admin_id}: {e}")