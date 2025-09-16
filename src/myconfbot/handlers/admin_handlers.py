import os
import telebot
import logging
from telebot import types
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from src.myconfbot.config import Config
from src.myconfbot.utils.database import db_manager
from src.myconfbot.utils.content_manager import content_manager
from src.myconfbot.models import Base, Order, Product, Category, OrderStatus, User


def register_admin_handlers(bot):
    """Регистрация обработчиков для администратора"""
    
    config = Config.load()
    user_states = {}  # Словарь для состояний при редактировании контента
    user_management_states = {}  # Cловарь для состояний управления пользователями
     
    def is_admin(user_id):
        """Проверка, является ли пользователь администратором"""
        user = db_manager.get_user_by_telegram_id(user_id)
        return user.is_admin if user else False
    
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
            elif data == 'admin_manage_users':
                manage_users(callback.message)
                
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
            response += f"👤 {order.user.full_name}\n"
            response += f"📞 {order.user.phone or 'Не указан'}\n"
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
    
    def manage_users(message):
        """Управление пользователями"""
        users = db_manager.get_all_users()
    
        if not users:
            bot.send_message(message.chat.id, "👥 Пользователи не найдены")
            return
        
        # Сортируем: сначала админы, потом клиенты, затем по имени
        users_sorted = sorted(users, key=lambda x: (
            not x.is_admin,  # Админы first (True > False)
            x.full_name.lower() if x.full_name else ''
        ))
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        for user in users_sorted:
            username = user.telegram_username[:8] + '...' if user.telegram_username and len(user.telegram_username) > 8 else user.telegram_username or 'нет'
            status = "👑 Админ" if user.is_admin else "👤 Клиент"
            btn_text = f"{user.full_name or 'Без имени'} | {username} | {status}"
            
            keyboard.add(InlineKeyboardButton(
                btn_text, 
                callback_data=f"user_detail_{user.telegram_id}"
            ))
        
        # Добавляем кнопку возврата
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
        
        bot.send_message(
            message.chat.id,
            "👥 Управление пользователями\nВыберите пользователя для просмотра:",
            reply_markup=keyboard
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('user_detail_'))
    def show_user_detail(callback: CallbackQuery):
        """Показать подробный профиль пользователя с фотографией"""
        if not is_admin(callback.from_user.id):
            return bot.answer_callback_query(callback.id, "❌ Нет прав администратора")
        
        try:
            telegram_id = int(callback.data.replace('user_detail_', ''))
            user = db_manager.get_user_by_telegram_id(telegram_id)
            
            if not user:
                bot.answer_callback_query(callback.id, "❌ Пользователь не найден")
                return
            
            # Формируем информацию о пользователе
            response = f"👤 <b>Профиль пользователя</b>\n\n"
            response += f"🆔 <b>ID:</b> {user.telegram_id}\n"
            response += f"👑 <b>Статус:</b> {'Администратор' if user.is_admin else 'Клиент'}\n"
            response += f"📛 <b>Полное имя:</b> {user.full_name or 'Не указано'}\n"
            response += f"📞 <b>Телефон:</b> {user.phone or 'Не указан'}\n"
            response += f"🔗 <b>Username:</b> @{user.telegram_username or 'Не указан'}\n"
            response += f"📝 <b>Характеристика:</b> {user.characteristics or 'Не указана'}\n"
            response += f"📅 <b>Дата регистрации:</b> {user.created_at.strftime('%d.%m.%Y %H:%M') if user.created_at else 'Неизвестно'}\n"
            
            # Создаем клавиатуру с действиями
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("➕ Изменить характеристику", callback_data=f"user_add_char_{user.telegram_id}"),
                InlineKeyboardButton("📋 Заказы", callback_data=f"user_orders_{user.telegram_id}")
            )
            keyboard.add(InlineKeyboardButton("🔙 Назад к списку", callback_data="admin_manage_users"))
            
            # Сначала отвечаем на callback чтобы убрать "часики"
            bot.answer_callback_query(callback.id)
            
            # Удаляем старое сообщение со списком пользователей
            try:
                bot.delete_message(callback.message.chat.id, callback.message.message_id)
            except Exception as e:
                logging.warning(f"Не удалось удалить сообщение: {e}")
            
            # Проверяем наличие фото
            if user.photo_path and os.path.exists(user.photo_path):
                try:
                    with open(user.photo_path, 'rb') as photo:
                        # Отправляем фото новым сообщением
                        bot.send_photo(
                            callback.message.chat.id,
                            photo,
                            caption=response,
                            reply_markup=keyboard,
                            parse_mode='HTML'
                        )
                        return
                except Exception as e:
                    logging.error(f"Ошибка при отправке фото пользователя: {e}")
            
            # Если фото нет или не удалось отправить, отправляем текстовое сообщение
            bot.send_message(
                callback.message.chat.id,
                response,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logging.error(f"Ошибка в show_user_detail: {e}")
            try:
                bot.answer_callback_query(callback.id, "❌ Ошибка при загрузке профиля")
            except:
                pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith('user_add_char_'))
    def add_characteristic_start(callback: CallbackQuery):
        """Начать добавление/редактирование характеристики пользователя"""
        if not is_admin(callback.from_user.id):
            return bot.answer_callback_query(callback.id, "❌ Нет прав администратора")
        
        try:
            telegram_id = int(callback.data.replace('user_add_char_', ''))
            user = db_manager.get_user_by_telegram_id(telegram_id)
            
            if not user:
                return bot.answer_callback_query(callback.id, "❌ Пользователь не найден")
            
            # Сохраняем состояние
            user_management_states[callback.from_user.id] = {
                'state': 'adding_characteristic',
                'target_user_id': telegram_id,
                'chat_id': callback.message.chat.id,
                'message_id': callback.message.message_id
            }
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data=f"user_cancel_char_{telegram_id}"))

            edit_text = (f"📝 Изменение характеристики для пользователя {user.full_name or 'Без имени'}\n\n"
                    f"Текущая характеристика: {user.characteristics or 'Не указана'}\n\n"
                    f"Отправьте новую характеристику или нажмите 'Отменить':")
            
            # Проверяем тип сообщения (текст или фото с подписью)
            if callback.message.photo:
                # Если это фото с подписью, отправляем новое текстовое сообщение
                bot.edit_message_caption(
                    caption=edit_text,
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    reply_markup=keyboard
                )
            else:
                # Если это текстовое сообщение, редактируем его
                bot.edit_message_text(
                    edit_text,
                    callback.message.chat.id,
                    callback.message.message_id,
                    reply_markup=keyboard
                )
            
            bot.answer_callback_query(callback.id)
            
            # bot.edit_message_text(
            #     f"📝 Добавление характеристики для пользователя {user.full_name or 'Без имени'}\n\n"
            #     f"Текущая характеристика: {user.characteristics or 'Не указана'}\n\n"
            #     f"Отправьте новую характеристику или нажмите 'Отменить':",
            #     callback.message.chat.id,
            #     callback.message.message_id,
            #     reply_markup=keyboard
            # )
            
            # bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logging.error(f"Ошибка в add_characteristic_start: {e}")
            bot.answer_callback_query(callback.id, "❌ Ошибка при начале редактирования")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('user_cancel_char_'))
    def cancel_characteristic(callback: CallbackQuery):
        """Отмена добавления/редактирования характеристики"""
        user_id = callback.from_user.id
        telegram_id = int(callback.data.replace('user_cancel_char_', ''))
        
        # Удаляем состояние
        user_management_states.pop(user_id, None)
        
        # Сначала отвечаем на callback
        bot.answer_callback_query(callback.id, "❌ Изменение характеристики отменено")
        
        # # Удаляем сообщение с редактором характеристики
        # try:
        #     bot.delete_message(callback.message.chat.id, callback.message.message_id)
        # except Exception as e:
        #     logging.warning(f"Не удалось удалить сообщение: {e}")
        
        # Возвращаемся к профилю пользователя через новое сообщение
        show_user_detail_from_message(callback.message, telegram_id)

    @bot.message_handler(func=lambda message: user_management_states.get(message.from_user.id, {}).get('state') == 'adding_characteristic')
    def handle_characteristic_input(message: Message):
        """Обработка ввода характеристики пользователя"""
        user_id = message.from_user.id
        user_state = user_management_states.get(user_id, {})
        target_user_id = user_state.get('target_user_id')
        
        if not target_user_id:
            bot.send_message(message.chat.id, "❌ Ошибка: пользователь не найден")
            user_management_states.pop(user_id, None)
            return
        
        # Проверяем команды отмены
        if message.text.lower() in ['отмена', 'cancel', 'назад', '❌', 'отменить']:
            user_management_states.pop(user_id, None)
            bot.send_message(message.chat.id, "❌ Добавление характеристики отменено.")
            return
        
        try:
            # Обновляем характеристику в базе данных
            if db_manager.update_user_characteristic(target_user_id, message.text):
                user_management_states.pop(user_id, None)
                
                # Получаем обновленные данные пользователя
                user = db_manager.get_user_by_telegram_id(target_user_id)
                
                bot.send_message(
                    message.chat.id,
                    f"✅ Характеристика для пользователя {user.full_name or 'Без имени'} успешно обновлена!\n\n"
                    f"Новая характеристика: {message.text}"
                )
                
                # Показываем обновленный профиль
                show_user_detail_from_message(message, target_user_id)
            else:
                bot.send_message(message.chat.id, "❌ Ошибка при обновлении характеристики")
                
        except Exception as e:
            logging.error(f"Ошибка при обновлении характеристики: {e}")
            bot.send_message(message.chat.id, "❌ Ошибка при обновлении характеристики")

    def show_user_detail_from_message(message, telegram_id):
        """Вспомогательная функция для показа профиля пользователя из message handler"""
        user = db_manager.get_user_by_telegram_id(telegram_id)
        
        if not user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден")
            return
        
        response = f"👤 <b>Профиль пользователя</b>\n\n"
        response += f"🆔 <b>ID:</b> {user.telegram_id}\n"
        response += f"👑 <b>Статус:</b> {'Администратор' if user.is_admin else 'Клиент'}\n"
        response += f"📛 <b>Полное имя:</b> {user.full_name or 'Не указано'}\n"
        response += f"📞 <b>Телефон:</b> {user.phone or 'Не указан'}\n"
        response += f"🔗 <b>Username:</b> @{user.telegram_username or 'Не указан'}\n"
        response += f"📝 <b>Характеристика:</b> {user.characteristics or 'Не указана'}\n"
        response += f"📅 <b>Дата регистрации:</b> {user.created_at.strftime('%d.%m.%Y %H:%M') if user.created_at else 'Неизвестно'}\n"
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("➕ Изменить характеристику", callback_data=f"user_add_char_{user.telegram_id}"),
            InlineKeyboardButton("📋 Заказы", callback_data=f"user_orders_{user.telegram_id}")
        )
        keyboard.add(InlineKeyboardButton("🔙 Назад к списку", callback_data="admin_manage_users"))
        
        # Проверяем наличие фото
        if user.photo_path and os.path.exists(user.photo_path):
            try:
                with open(user.photo_path, 'rb') as photo:
                    bot.send_photo(
                        message.chat.id,
                        photo,
                        caption=response,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                    return
            except Exception as e:
                logging.error(f"Ошибка при отправке фото: {e}")
        
        # Если фото нет или не удалось отправить
        bot.send_message(
            message.chat.id,
            response,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('user_orders_'))
    def show_user_orders(callback: CallbackQuery):
        """Показать заказы пользователя"""
        if not is_admin(callback.from_user.id):
            return bot.answer_callback_query(callback.id, "❌ Нет прав администратора")
        
        telegram_id = int(callback.data.replace('user_orders_', ''))
        user = db_manager.get_user_by_telegram_id(telegram_id)
        
        if not user:
            return bot.answer_callback_query(callback.id, "❌ Пользователь не найден")
        
        # Заглушка - реализуем позже
        bot.answer_callback_query(callback.id, "📋 Функция просмотра заказов пользователя в разработке")

    @bot.callback_query_handler(func=lambda call: call.data == 'admin_back')
    def back_to_admin_main(callback: CallbackQuery):
        """Возврат в главное меню администратора"""
        if not is_admin(callback.from_user.id):
            return bot.answer_callback_query(callback.id, "❌ Нет прав администратора")
        
        try:
            # Удаляем текущее сообщение со списком пользователей
            bot.delete_message(callback.message.chat.id, callback.message.message_id)
        except Exception as e:
            logging.warning(f"Не удалось удалить сообщение: {e}")
    
        # Создаем новое сообщение для вызова функции
        fake_message = type('obj', (object,), {
            'chat': type('obj', (object,), {'id': callback.message.chat.id}),
            'message_id': callback.message.message_id
        })
                
        # Показываем панель управления
        show_management_panel(bot, fake_message)
        
        bot.answer_callback_query(callback.id, "🔙 Возврат в главное меню")

        # try:
        #     # Сначала отвечаем на callback
        #     bot.answer_callback_query(callback.id, "🔙 Возврат в главное меню")
            
        #     # Удаляем текущее сообщение
        #     bot.delete_message(callback.message.chat.id, callback.message.message_id)
            
        #     # Создаем новое сообщение для показа меню управления
        #     keyboard = InlineKeyboardMarkup(row_width=2)
        #     keyboard.add(
        #         InlineKeyboardButton("🎂 Продукция", callback_data="admin_manage_products"),
        #         InlineKeyboardButton("📖 Рецепты", callback_data="admin_manage_recipes")
        #     )
        #     keyboard.add(
        #         InlineKeyboardButton("💼 Услуги", callback_data="admin_manage_services"),
        #         InlineKeyboardButton("📞 Контакты", callback_data="admin_manage_contacts")
        #     )
        #     keyboard.add(
        #         InlineKeyboardButton("📄 Контент", callback_data="admin_manage_content"),
        #         InlineKeyboardButton("👥 Пользователи", callback_data="admin_manage_users")
        #     )
            
        #     # Отправляем новое сообщение с меню управления
        #     bot.send_message(
        #         callback.message.chat.id,
        #         "🏪 Панель управления\nВыберите раздел:",
        #         reply_markup=keyboard,
        #         parse_mode='HTML'
        #     )
                
        # except Exception as e:
        #     logging.error(f"Ошибка при возврате в меню управления: {e}")
        #     bot.answer_callback_query(callback.id, "❌ Ошибка при возврате")

    def show_management_panel(bot, message):
        """Показывает панель управления через inline-кнопки"""
        keyboard = tapes.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🎂 Продукция", callback_data="admin_manage_products"),
            InlineKeyboardButton("📖 Рецепты", callback_data="admin_manage_recipes")
        )
        keyboard.add(
            InlineKeyboardButton("💼 Услуги", callback_data="admin_manage_services"),
            InlineKeyboardButton("📞 Контакты", callback_data="admin_manage_contacts")
        )
        keyboard.add(
            InlineKeyboardButton("📄 Контент", callback_data="admin_manage_content"),
            InlineKeyboardButton("👥 Пользователи", callback_data="admin_manage_users")
        )
        
        bot.send_message(
            message.chat.id,
            "🏪 Панель управления\nВыберите раздел:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
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
        """Визуальный редактор контента для админов"""
        keyboard = InlineKeyboardMarkup()
        
        files = content_manager.get_file_list()
        for filename in files:
            keyboard.add(
                InlineKeyboardButton(f"✏️ {filename}", callback_data=f"content_edit_{filename}"),
                InlineKeyboardButton(f"👀 {filename}", callback_data=f"content_preview_{filename}")
            )
#         help_text = """
# 🎨 **Редактор текста**

# Просто выберите файл для редактирования и напишите текст как в обычном сообщении\\.

# **Доступные оформления:**
# ✅ **Жирный** \\- оберните текст звёздочками \\*\\*\\*жирный текст\\*\\*\\*
# ✅ _Курсив_ \\- оберните текст в \\_\\_курсивный текст\\_\\_
# ✅ `Код` \\- оберните текст в \\`\\. Пример \\`\\`user_states = {}\\`\\`
# ✅ ✦ Списки проще начинать с эмодзи\\. Например \\- ▫️, или ✦
# ✅ Эмодзи 🎂 📞 💼 \\- вставляйте как есть\\. Искать подходящие, например [тут](https://getemoji\\.com/)\\. Находим подходящий, щелкаем по нему, он скопируется в буфер обмена\\. В нужно месте вставляем `Ctrl \\+ V` 

# Важно: если ваш текст содержит символы `_ * [ ] ( ) ~ \\` > # \\+ \\- = | { } . ! `, то эти символы нужно экранировать обратным слэшем \\\\\\ \\.

# Например, чтобы написать `5 * 5 = 25`, нужно ввести 5 \\\\\\* 5 \\\\\\= 25\\.   
# """
        
        help_text = """
    🎨 **Редактор текста**

    Просто выберите файл для редактирования и напишите текст как в обычном сообщении\\.

    **Доступные оформления:**
✅ **Жирный** \\- оберните текст звёздочками \\*\\***жирный текст**\\*\\*
✅ _Курсив_ \\- оберните текст в \\__курсивный текст_\\_
✅ `Код` \\- оберните текст в \\`\\. Пример `\\`user_states = {}\\``
✅ ✦ Списки проще начинать с эмодзи\\. Например \\- ▫️, или ✦
✅ Эмодзи 🎂 📞 💼 \\- вставляйте как есть\\. Искать подходящие, например [тут](https://getemoji.com/)\\. Находим подходящий, щелкаем по нему, он скопируется в буфер обмена\\. В нужно месте вставляем `Ctrl + V` 

Важно: если ваш текст содержит символы `_ * [ ] ( ) ~ ` \\` ` > # + - = | { } . ! `, то эти символы нужно экранировать обратным слэшем \\\ \\.

Например, чтобы написать `5 * 5 = 25`, нужно ввести 5 \\\\\* 5 \\\\\= 25\\.   


    """

        bot.send_message(
            message.chat.id,
            help_text,
            parse_mode='MarkdownV2',
            reply_markup=keyboard
        )
       
    # Обработчик для редактирования контента
    @bot.callback_query_handler(func=lambda call: call.data.startswith('content_edit_'))
    def edit_content_callback(callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return bot.answer_callback_query(callback.id, "❌ Нет прав")
        
        try:
            filename = callback.data.replace('content_edit_', '')
            current_content = content_manager.get_content(filename)
            
            if current_content is None:
                return bot.answer_callback_query(callback.id, "❌ Файл не найден")
            
            # Создаем клавиатуру с кнопками
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton("❌ Отменить редактирование", callback_data=f"cancel_edit_{filename}"),
                InlineKeyboardButton("💾 Сохранить без изменений", callback_data=f"keep_original_{filename}")
            )
            
            # Сохраняем состояние и оригинальный текст
            user_states[callback.from_user.id] = {
                'state': 'editing_content',
                'filename': filename,
                'original_content': current_content,  # Сохраняем оригинальный текст
                'chat_id': callback.message.chat.id,
                'message_id': callback.message.message_id
            }
            
            # # Сохраняем состояние редактирования
            # user_states[callback.from_user.id] = {
            #     'state': 'editing_content',
            #     'filename': filename,
            #     'chat_id': callback.message.chat.id,
            #     'message_id': callback.message.message_id
            # }
            
            # Редактируем сообщение с текущим содержимым
            bot.edit_message_text(
                f"📝 Редактирование {filename}\n\n"
                f"Текущее содержимое:\n\n"
                f"{current_content}\n\n"
                f"Отправьте новый текст или выберите действие:",
                callback.message.chat.id,
                callback.message.message_id,
                reply_markup=keyboard
            )
            
            bot.answer_callback_query(callback.id)
        except Exception as e:
            logging.error(f"Ошибка в edit_content_callback: {e}")
            bot.answer_callback_query(callback.id, "❌ Ошибка при открытии редактора")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('keep_original_'))
    def keep_original_callback(callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return bot.answer_callback_query(callback.id, "❌ Нет прав")
        
        try:
            filename = callback.data.replace('keep_original_', '')
            user_id = callback.from_user.id
            
            # Получаем оригинальный текст из состояния
            user_state = user_states.get(user_id, {})
            original_content = user_state.get('original_content')
            
            if original_content:
                # "Сохраняем" оригинальный текст (фактически ничего не меняем)
                user_states.pop(user_id, None)
                
                bot.edit_message_text(
                    f"✅ Файл '{filename}' сохранен без изменений.",
                    callback.message.chat.id,
                    callback.message.message_id
                )
                bot.answer_callback_query(callback.id, "✅ Сохранено без изменений")
            else:
                bot.answer_callback_query(callback.id, "❌ Ошибка: не найден оригинальный текст")
                
        except Exception as e:
            logging.error(f"Ошибка в keep_original_callback: {e}")
            bot.answer_callback_query(callback.id, "❌ Ошибка при сохранении")
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_edit_'))
    def cancel_editing_callback(callback: CallbackQuery):
        user_id = callback.from_user.id
        filename = callback.data.replace('cancel_edit_', '')
        
        user_states.pop(user_id, None)
        
        bot.edit_message_text(
            f"❌ Редактирование файла '{filename}' отменено.",
            callback.message.chat.id,
            callback.message.message_id
        )
        bot.answer_callback_query(callback.id, "❌ Редактирование отменено")
    
    # Обработчик для предпросмотра контента
    @bot.callback_query_handler(func=lambda call: call.data.startswith('content_preview_'))
    def preview_content_callback(callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return bot.answer_callback_query(callback.id, "❌ Нет прав")
        
        try:
            filename = callback.data.replace('content_preview_', '')
            content = content_manager.get_content(filename)
            
            if content is None:
                return bot.answer_callback_query(callback.id, "❌ Файл не найден")
            
            # Создаем клавиатуру с кнопкой скачивания
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton("📥 Скачать файл", callback_data=f"download_{filename}")
            )

            # Отправляем предпросмотр новым сообщением
            preview_text = f"👀 Предпросмотр {filename}:\n\n{content}"
            
            # Обрезаем если слишком длинное (ограничение Telegram)
            if len(preview_text) > 4000:
                preview_text = preview_text[:4000] + "..."
            
            bot.send_message(callback.message.chat.id, preview_text, reply_markup=keyboard)
            bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logging.error(f"Ошибка в preview_content_callback: {e}")
            bot.answer_callback_query(callback.id, "❌ Ошибка при предпросмотре")
    
    # Обработчик для приема нового контента
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'editing_content')
    def handle_content_edit(message: Message):
        user_id = message.from_user.id
        user_state = user_states.get(user_id, {})
        filename = user_state.get('filename')
        chat_id = user_state.get('chat_id')
        message_id = user_state.get('message_id')
        
        # Проверяем команды отмены
        if message.text.lower() in ['отмена', 'cancel', 'назад', '❌', 'отменить']:
            user_states.pop(user_id, None)
            bot.send_message(message.chat.id, "❌ Редактирование отменено.")
            return
        
        # Проверяем команду сохранения без изменений
        if message.text.lower() in ['без изменений', 'оставить', 'сохранить', '💾']:
            user_states.pop(user_id, None)
            bot.send_message(message.chat.id, f"✅ Файл '{filename}' сохранен без изменений.")
            return

        if not filename:
            bot.send_message(message.chat.id, "❌ Ошибка: не найден файл для редактирования")
            return
        
        try:
            if content_manager.update_content(filename, message.text):
                # Удаляем состояние редактирования
                user_states.pop(user_id, None)
                
                # Отправляем подтверждение
                bot.send_message(message.chat.id, f"✅ Файл `{filename}` успешно обновлен!", parse_mode='Markdown')
                
                # Возвращаемся к управлению контентом
                manage_content(message)
            else:
                bot.send_message(message.chat.id, "❌ Ошибка при сохранении файла")
                
        except Exception as e:
            logging.error(f"Ошибка при сохранении контента: {e}")
            bot.send_message(message.chat.id, "❌ Ошибка при сохранении файла")
    
    # Обработчик для скачивания файла
    @bot.callback_query_handler(func=lambda call: call.data.startswith('download_'))
    def download_file_callback(callback: CallbackQuery):
        if not is_admin(callback.from_user.id):
            return bot.answer_callback_query(callback.id, "❌ Нет прав")
        
        try:
            filename = callback.data.replace('download_', '')
            content = content_manager.get_content(filename)
            
            if content is None:
                return bot.answer_callback_query(callback.id, "❌ Файл не найден")
            
            # Создаем временный файл для отправки
            import tempfile
            import os
            
            # Указываем кодировку UTF-8 и правильный режим записи
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Отправляем файл
            try:
                with open(temp_file_path, 'rb') as file:
                    bot.send_document(
                        callback.message.chat.id, 
                        file, 
                        caption=f"📄 Файл: {filename}"
                    )
                bot.answer_callback_query(callback.id, "✅ Файл отправлен")
            except Exception as e:
                logging.error(f"Ошибка при отправке файла: {e}")
                bot.answer_callback_query(callback.id, "❌ Ошибка при отправке")
            finally:
                # Удаляем временный файл
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logging.error(f"Ошибка при удалении временного файла: {e}")
                
        except Exception as e:
            logging.error(f"Ошибка при скачивании файла: {e}")
            bot.answer_callback_query(callback.id, "❌ Ошибка при скачивании")

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