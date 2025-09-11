from telebot import types
import sqlite3
from datetime import datetime
import logging
from src.myconfbot.models import Customer, OrderStatus, CustomerCharacteristic, Admin
from src.myconfbot.utils.database import db_manager
from src.myconfbot.config import Config

def register_main_handlers(bot):

    # Словарь для хранения состояния пользователей
    user_states = {}
    
    def is_user_admin(telegram_id):
        """Проверка, является ли пользователь администратором"""
        try:
            # Сначала проверяем конфигурацию
            config = Config.load()
            if telegram_id in config.admin_ids:
                # Проверяем, есть ли уже в базе
                admin = db_manager.get_admin_by_telegram_id(telegram_id)
                if not admin:
                    # Если нет в базе, но есть в конфиге - добавляем
                    return None  # Вернем None чтобы обработать в основном обработчике
                return True
            return False
        except Exception as e:
            logging.error(f"Ошибка при проверке администратора: {e}")
            return False
    
    def show_customer_menu(chat_id, is_admin=False):
        """Показывает меню клиента с возможностью админ панели"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('💼 Услуги')
        btn2 = types.KeyboardButton('🎂 Сделать заказ')
        btn3 = types.KeyboardButton('📖 Рецепты')
        btn4 = types.KeyboardButton('📞 Контакты')
        btn5 = types.KeyboardButton('🐱 Моя информация')
        
        if is_admin:
            btn_admin = types.KeyboardButton('👑 Админ панель')
            markup.add(btn1, btn2, btn3, btn4, btn5, btn_admin)
        else:
            markup.add(btn1, btn2, btn3, btn4, btn5)
        
        welcome_text = "🎂 Добро пожаловать! Выберите действие:"
        bot.send_message(chat_id, welcome_text, reply_markup=markup)
    
    @bot.message_handler(commands=['start', 'help'])   
    def handle_start(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        first_name = message.from_user.first_name
        username = message.from_user.username
        
        try:
            # Сначала проверяем, является ли пользователь администратором
            admin_check = is_user_admin(user_id)
            is_admin = False
            
            if admin_check is None:
                # Пользователь есть в конфиге, но нет в базе - сохраняем как админа
                try:
                    admin = db_manager.add_admin(
                        telegram_id=user_id,
                        first_name=first_name,
                        username=username
                    )
                    bot.send_message(
                        chat_id, 
                        f"👑 Добро пожаловать, администратор {first_name}!\n"
                        f"Ваши права подтверждены. Доступ к админ панели открыт."
                    )
                    is_admin = True
                except Exception as e:
                    logging.error(f"Ошибка при сохранении администратора: {e}")
                    bot.send_message(chat_id, "Ошибка при активации прав администратора.")
            
            elif admin_check:
                # Пользователь уже администратор
                is_admin = True
                bot.send_message(
                    chat_id, 
                    f"👑 С возвращением, администратор {username}!\n"
                    f"Доступ к админ панели открыт."
                )
            
            # Проверяем как клиента (даже если администратор)
            customer = db_manager.get_customer_by_telegram_id(user_id)
            
            if customer:
                # Клиент уже есть в базе
                bot.send_message(chat_id, f"С возвращением, {customer.first_name}! 🎂\nРады снова видеть вас!")
                show_customer_menu(chat_id, is_admin)
            else:
                # Новый клиент (даже если администратор)
                bot.send_message(chat_id, "Привет! 👋\nЯ бот кондитерской. Давайте познакомимся!")
                bot.send_message(chat_id, "Как вас зовут?")
                # Сохраняем информацию о том, что пользователь админ (если он им является)
                user_states[user_id] = {'state': 'awaiting_name', 'is_admin': is_admin}
                
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка. Попробуйте позже.")
            logging.error(f"Ошибка при обработке /start: {e}")
    
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'awaiting_name')
    def handle_name_input(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        name = message.text.strip()
        username = message.from_user.username
        
        # Получаем информацию о состоянии
        user_state = user_states.get(user_id, {})
        is_admin = user_state.get('is_admin', False)
        
        if len(name) < 2:
            bot.send_message(chat_id, "Пожалуйста, введите настоящее имя (минимум 2 символа).")
            return
        
        try:
            # Сохраняем клиента в базу
            db_manager.add_customer(
                telegram_id=user_id,
                first_name=name,
                username=username
            )
            
            # Убираем состояние ожидания
            user_states.pop(user_id, None)
            
            if is_admin:
                bot.send_message(
                    chat_id, 
                    f"Приятно познакомиться, {name}! 😊\n"
                    f"Как администратор, вы также имеете доступ к админ панели."
                )
            else:
                bot.send_message(chat_id, f"Приятно познакомиться, {name}! 😊\nТеперь я буду обращаться к вам по имени.")
            
            show_customer_menu(chat_id, is_admin)
            
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка при сохранении. Попробуйте еще раз.")
            logging.error(f"Ошибка при сохранении клиента: {e}")
    
    @bot.message_handler(func=lambda message: message.text == '👑 Админ панель')
    def handle_admin_panel(message):
        """Обработка входа в админ панель"""

        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not is_user_admin(user_id):
            bot.send_message(chat_id, "⛔ У вас нет прав администратора.")
            return
        
        # Импортируем и регистрируем админ обработчики
        try:
            from src.myconfbot.handlers.admin_handlers import register_admin_handlers
            # Передаем управление админ обработчикам
            # Для этого нужно создать временный бот или использовать другой подход
            # Вместо этого покажем сообщение о переходе
            bot.send_message(
                chat_id,
                "👑 Переход в админ панель...\n"
                "Используйте команды администрирования:\n"
                "/admin_stats - Статистика\n"
                "/admin_orders - Управление заказами\n"
                "/admin_users - Управление пользователями"
            )
            
        except ImportError as e:
            bot.send_message(chat_id, "⛔ Админ панель временно недоступна.")
            logging.error(f"Ошибка импорта admin_handlers: {e}")
        except Exception as e:
            bot.send_message(chat_id, "⛔ Ошибка при открытии админ панели.")
            logging.error(f"Ошибка при открытии админ панели: {e}")
       
    @bot.message_handler(commands=['menu'])
    def show_menu(message):
        # Показываем меню в зависимости от прав
        user_id = message.from_user.id
        is_admin = is_user_admin(user_id)
        show_customer_menu(message.chat.id, is_admin)
    
    @bot.message_handler(func=lambda message: message.text == '🐱 Моя информация')
    def show_my_id(message):
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        username = f"@{message.from_user.username}" if message.from_user.username else "нет"
        is_admin = is_user_admin(user_id)
        
        admin_status = "👑 Администратор" if is_admin else "👤 Клиент"
        
        bot.send_message(
            message.chat.id,
            f"👤 Ваша информация:\n"
            f"🆔 ID: `{user_id}`\n"
            f"📛 Имя: {first_name}\n"
            f"📱 Username: {username}\n"
            f"🎭 Статус: {admin_status}\n\n",
            # f"Сообщите этот ID администратору для добавления в админы.",
            parse_mode='Markdown'
        )
    
    # Старые обработчики (оставляем пока как есть)
    # нужно переделывать
    @bot.message_handler(commands=['start2'])
    def send_welcome(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        
        
        welcome_text = """
        🎂 Добро пожаловать в кондитерскую мастерскую!

        Я помогу вам:
        • 📋 Сделать заказ тортов и десертов
        • 📖 Посмотреть рецепты
        • 💼 Узнать о наших услугах
        • 📞 Связаться с мастером

        Выберите действие из меню ниже 👇
        """
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('🎂 Сделать заказ')
        btn2 = types.KeyboardButton('📖 Рецепты')
        btn3 = types.KeyboardButton('💼 Услуги')
        btn4 = types.KeyboardButton('📞 Контакты')
        markup.add(btn1, btn2, btn3, btn4)
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
    
    @bot.message_handler(func=lambda message: message.text == '📞 Контакты')
    def send_contacts(message):
        contacts_text = """
        📍 Наш адрес: ул. Кондитерская, 15
        📞 Телефон: +7 (999) 123-45-67
        🕒 Время работы: 9:00 - 21:00
        📧 Email: master@myconfbot.ru
        
        Мы всегда рады вашим вопросам и заказам! 🎂
        """
        bot.send_message(message.chat.id, contacts_text)
    
    @bot.message_handler(func=lambda message: message.text == '💼 Услуги')
    def send_services(message):
        services_text = """
        🎁 Наши услуги:

        • 🎂 Торты на заказ
        • 🧁 Капкейки и маффины
        • 🍪 Пряничные домики
        • 🍫 Шоколадные конфеты ручной работы
        • 🎉 Десерты для мероприятий
        • 👨‍🍳 Мастер-классы по кондитерскому искусству

        Для заказа выберите "🎂 Сделать заказ"
        """
        bot.send_message(message.chat.id, services_text)
    