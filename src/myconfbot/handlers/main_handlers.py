from telebot import types
from datetime import datetime
import logging
from src.myconfbot.models import Customer, Admin, CustomerCharacteristic
from src.myconfbot.utils.database import db_manager
from src.myconfbot.config import Config
from src.myconfbot.utils.content_manager import content_manager

def register_main_handlers(bot):
    # Словарь для хранения состояния пользователей
    user_states = {}
    
    def is_user_admin(telegram_id):
        """Проверка, является ли пользователь администратором"""
        try:
            config = Config.load()
            return telegram_id in config.admin_ids
        except Exception as e:
            logging.error(f"Ошибка при проверке администратора: {e}")
            return False
    
    def show_main_menu(chat_id, is_admin=False):
        """Показывает главное меню с reply-кнопками"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        
        # Базовые кнопки для всех пользователей
        buttons = [
            '🎂 Сделать заказ',
            '📖 Рецепты', 
            '💼 Услуги',
            '📞 Контакты',
            '🐱 Моя информация'
        ]
        
        # Добавляем кнопки администратора
        if is_admin:
            buttons.extend([
                '📦 Заказы',
                '📊 Статистика',
                '🏪 Управление'
            ])
        
        markup.add(*[types.KeyboardButton(btn) for btn in buttons])
        
        # welcome_text = "🎂 Главное меню\nВыберите действие:" # За не надобностью закоментировал
        # bot.send_message(chat_id, welcome_text, reply_markup=markup)
        bot.send_message(chat_id, "🎂 ", reply_markup=markup)
    
    @bot.message_handler(commands=['start', 'help'])
    def handle_start(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        first_name = message.from_user.first_name
        username = message.from_user.username
        
        try:
            is_admin = is_user_admin(user_id)
            
            # Проверяем, есть ли пользователь в базе
            customer = db_manager.get_customer_by_telegram_id(user_id)
            admin = db_manager.get_admin_by_telegram_id(user_id) if is_admin else None
            
            if customer or admin:
                # Пользователь уже в базе
                name = admin.first_name if admin else customer.first_name
                status = "администратор" if admin else "клиент"
                
                bot.send_message(
                    chat_id, 
                    f"С возвращением, {name}! 👋\n"
                    f"Рады снова видеть. Ваш статус: {status}!"
                )
                show_main_menu(chat_id, is_admin)
            else:
                # Новый пользователь
                bot.send_message(
                    chat_id, 
                    "Привет! 👋\nЯ бот кондитерской. Давайте познакомимся!"
                )
                bot.send_message(chat_id, "Пожалуйста, наберите ваше имя:")
                
                # Сохраняем состояние
                user_states[user_id] = {
                    'state': 'awaiting_name',
                    'is_admin': is_admin,
                    'username': username
                }
            # Загрузка приветственного текста
            welcome_text = content_manager.get_content('welcome.md')
            if not welcome_text:
                welcome_text = "Добро пожаловать\\! Я бот\\-помощник мастера кондитера\\!"
            
            try:
                bot.send_message(chat_id, welcome_text, parse_mode='MarkdownV2')
            except Exception as e:
                if "400" in str(e) and "parse entities" in str(e):
                    # Ошибка форматирования - отправляем как plain text
                    error_msg = "⚠️ Ошибка форматирования текста. Отображаю как обычный текст."
                    bot.send_message(chat_id, error_msg)
                    bot.send_message(chat_id, welcome_text)  # plain text
                    logging.warning(f"Ошибка MarkdownV2 форматирования: {e}")
                else:
                    # Другая ошибка
                    bot.send_message(chat_id, "Произошла ошибка при загрузке приветствия.")
                    logging.error(f"Ошибка отправки сообщения: {e}")
                            
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка. Попробуйте позже.")
            logging.error(f"Ошибка при обработке /start: {e}")
    
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'awaiting_name')
    def handle_name_input(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        name = message.text.strip()
        
        user_state = user_states.get(user_id, {})
        is_admin = user_state.get('is_admin', False)
        username = user_state.get('username')
        
        if len(name) < 2:
            bot.send_message(chat_id, "Пожалуйста, введите настоящее имя (минимум 2 символа).")
            return
        
        try:
            if is_admin:
                # Для администратора запрашиваем дополнительные данные
                db_manager.add_admin(
                    telegram_id=user_id,
                    first_name=name,
                    username=username
                )
                user_states[user_id]['state'] = 'awaiting_phone'
                user_states[user_id]['name'] = name
                bot.send_message(chat_id, "Отлично! Теперь укажите ваш телефонный номер:")
            else:
                # Для клиента просто сохраняем
                db_manager.add_customer(
                    telegram_id=user_id,
                    first_name=name,
                    username=username
                )
                user_states.pop(user_id, None)
                bot.send_message(chat_id, f"Приятно познакомиться, {name}! 😊")
                show_main_menu(chat_id, False)
                
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка при сохранении. Попробуйте еще раз.")
            logging.error(f"Ошибка при сохранении: {e}")
    
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'awaiting_phone')
    def handle_phone_input(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        phone = message.text.strip()
        
        user_state = user_states.get(user_id, {})
        name = user_state.get('name')
        
        # Простая валидация телефона
        if not any(char.isdigit() for char in phone) or len(phone) < 5:
            bot.send_message(chat_id, "Пожалуйста, введите корректный телефонный номер.")
            return
        
        try:
            user_states[user_id]['state'] = 'awaiting_address'
            user_states[user_id]['phone'] = phone
            bot.send_message(chat_id, "Отлично! Теперь укажите ваш адрес:")
                
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка. Попробуйте еще раз.")
            logging.error(f"Ошибка при обработке телефона: {e}")
    
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'awaiting_address')
    def handle_address_input(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        address = message.text.strip()
        
        user_state = user_states.get(user_id, {})
        name = user_state.get('name')
        phone = user_state.get('phone')
        username = user_state.get('username')
        
        if len(address) < 5:
            bot.send_message(chat_id, "Пожалуйста, введите полный адрес.")
            return
        
        try:
            # Обновляем администратора с полными данными
            db_manager.update_admin_info(user_id, phone, address)
            user_states.pop(user_id, None)
            
            bot.send_message(
                chat_id, 
                f"Отлично, {name}! 👑\n"
                f"Ваши данные сохранены. Теперь вы можете управлять кондитерской!"
            )
            show_main_menu(chat_id, True)
                
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка при сохранении. Попробуйте еще раз.")
            logging.error(f"Ошибка при сохранении адреса: {e}")
    
    @bot.message_handler(commands=['menu'])
    def show_menu(message):
        """Показывает главное меню"""
        user_id = message.from_user.id
        is_admin = is_user_admin(user_id)
        show_main_menu(message.chat.id, is_admin)
    
    @bot.message_handler(func=lambda message: message.text == '🐱 Моя информация')
    def show_my_info(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        is_admin = is_user_admin(user_id)
        user_info = None
        
        try:
            if is_admin:
                user_info = db_manager.get_admin_by_telegram_id(user_id)
            else:
                user_info = db_manager.get_customer_by_telegram_id(user_id)
            
            if user_info:
                response = f"👤 Ваша информация:\n"
                response += f"📛 Имя: {user_info.first_name}\n"
                if user_info.username:
                    response += f"📱 Username: @{user_info.username}\n"
                if is_admin and user_info.phone:
                    response += f"📞 Телефон: {user_info.phone}\n"
                if is_admin and user_info.address:
                    response += f"📍 Адрес: {user_info.address}\n"
                response += f"🎭 Статус: {'👑 Администратор' if is_admin else '👤 Клиент'}\n"
                
                bot.send_message(chat_id, response)
            else:
                bot.send_message(chat_id, "❌ Информация не найдена. Попробуйте /start")
                
        except Exception as e:
            bot.send_message(chat_id, "❌ Ошибка при получении информации.")
            logging.error(f"Ошибка при получении информации пользователя: {e}")
    
    # Обработчики для администраторских кнопок
    @bot.message_handler(func=lambda message: message.text in ['📦 Заказы', '📊 Статистика', '🏪 Управление'])
    def handle_admin_buttons(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not is_user_admin(user_id):
            bot.send_message(chat_id, "❌ У вас нет прав администратора.")
            return
        
        # Используем inline-кнопки для административных функций
        if message.text == '📦 Заказы':
            show_orders_management(message)
        elif message.text == '📊 Статистика':
            show_statistics(message)
        elif message.text == '🏪 Управление':
            show_management_panel(message)
    
    def show_orders_management(message):
        """Показывает управление заказами через inline-кнопки"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("📋 Активные заказы", callback_data="admin_orders_active"),
            types.InlineKeyboardButton("📊 Все заказы", callback_data="admin_orders_all")
        )
        keyboard.add(
            types.InlineKeyboardButton("🔄 Изменить статус", callback_data="admin_orders_change_status"),
            types.InlineKeyboardButton("📈 Статистика заказов", callback_data="admin_orders_stats")
        )
        
        bot.send_message(
            message.chat.id,
            "📦 Управление заказами\nВыберите действие:",
            reply_markup=keyboard
        )
    
    def show_statistics(message):
        """Показывает статистику через inline-кнопки"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("📊 Общая статистика", callback_data="admin_stats_general"),
            types.InlineKeyboardButton("💰 Финансовая", callback_data="admin_stats_financial")
        )
        keyboard.add(
            types.InlineKeyboardButton("👥 Клиентская", callback_data="admin_stats_clients"),
            types.InlineKeyboardButton("🎂 Товарная", callback_data="admin_stats_products")
        )
        
        bot.send_message(
            message.chat.id,
            "📊 Статистика\nВыберите раздел:",
            reply_markup=keyboard
        )
    
    def show_management_panel(message):
        """Показывает панель управления через inline-кнопки"""
        keyboard = types.InlineKeyboardMarkup()
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
            types.InlineKeyboardButton("👥 Администраторы", callback_data="admin_manage_admins")
        )
        
        bot.send_message(
            message.chat.id,
            "🏪 Панель управления\nВыберите раздел:",
            reply_markup=keyboard
        )
    
    # Базовые обработчики для клиентов
    @bot.message_handler(func=lambda message: message.text == '📞 Контакты')
    def send_contacts(message):
        # contacts_text = """
        # 📍 Наш адрес: ул. Кондитерская, 15
        # 📞 Телефон: +7 (999) 123-45-67
        # 🕒 Время работы: 9:00 - 21:00
        # 📧 Email: master@myconfbot.ru
        
        # Мы всегда рады вашим вопросам и заказам! 🎂
        # """
        # bot.send_message(message.chat.id, contacts_text)
        contacts_text = content_manager.get_content('contacts.md')
        if not contacts_text:
            contacts_text = "Контактная информация пока не добавлена"
                
        try:
            bot.send_message(message.chat.id, contacts_text, parse_mode='MarkdownV2')
        except Exception as e:
            if "400" in str(e) and "parse entities" in str(e):
                # Ошибка форматирования - отправляем как plain text
                error_msg = "⚠️ Ошибка форматирования текста. Отображаю как обычный текст."
                bot.send_message(message.chat.id, error_msg)
                bot.send_message(message.chat.id, contacts_text)  # plain text
                logging.warning(f"Ошибка MarkdownV2 форматирования: {e}")
            else:
                # Другая ошибка
                bot.send_message(message.chat.id, "Произошла ошибка при загрузке приветствия.")
                logging.error(f"Ошибка отправки сообщения: {e}")
    
    @bot.message_handler(func=lambda message: message.text == '💼 Услуги')
    def send_services(message):
        # Загрузка текста описывающего услуги
        services_text = content_manager.get_content('services.md')
        if not services_text:
            services_text = "🎁 Информация по услугам пока не добавлена"
                
        try:
            bot.send_message(message.chat.id, services_text, parse_mode='MarkdownV2')
        except Exception as e:
            if "400" in str(e) and "parse entities" in str(e):
                # Ошибка форматирования - отправляем как plain text
                error_msg = "⚠️ Ошибка форматирования текста. Отображаю как обычный текст."
                bot.send_message(message.chat.id, error_msg)
                bot.send_message(message.chat.id, services_text)  # plain text
                logging.warning(f"Ошибка MarkdownV2 форматирования: {e}")
            else:
                # Другая ошибка
                bot.send_message(message.chat.id, "Произошла ошибка при загрузке приветствия.")
                logging.error(f"Ошибка отправки сообщения: {e}")
    
    @bot.message_handler(func=lambda message: message.text == '📖 Рецепты')
    def show_recipes(message):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("🍰 Торты", callback_data="recipes_cakes"),
            types.InlineKeyboardButton("🧁 Капкейки", callback_data="recipes_cupcakes")
        )
        keyboard.add(
            types.InlineKeyboardButton("🍪 Печенье", callback_data="recipes_cookies"),
            types.InlineKeyboardButton("🎂 Сезонные", callback_data="recipes_seasonal")
        )
        
        bot.send_message(
            message.chat.id,
            "📖 Наши рецепты\nВыберите категорию:",
            reply_markup=keyboard
        )