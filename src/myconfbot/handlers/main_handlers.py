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
    
    @bot.message_handler(commands=['start', 'help'])   
    def handle_start(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        first_name = message.from_user.first_name
        username = message.from_user.username
        
        try:
            # Сначала проверяем, является ли пользователь администратором
            admin_check = is_user_admin(user_id)
            
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
                        f"Ваши права подтверждены. Доступ к панели управления открыт."
                    )
                    # Показываем меню администратора
                    show_admin_menu(chat_id)
                    return
                except Exception as e:
                    logging.error(f"Ошибка при сохранении администратора: {e}")
                    bot.send_message(chat_id, "Ошибка при активации прав администратора.")
            
            elif admin_check:
                # Пользователь уже администратор
                bot.send_message(
                    chat_id, 
                    f"👑 С возвращением, администратор {first_name}!\n"
                    f"Панель управления готова к работе."
                )
                show_admin_menu(chat_id)
                return
            
            # Если не администратор - проверяем как клиента
            customer = db_manager.get_customer_by_telegram_id(user_id)
            
            if customer:
                # Клиент уже есть в базе
                bot.send_message(chat_id, f"С возвращением, {customer.first_name}! 🎂\nРады снова видеть вас!")
                show_customer_menu(chat_id)
            else:
                # Новый клиент
                bot.send_message(chat_id, "Привет! 👋\nЯ бот кондитерской. Давайте познакомимся!")
                bot.send_message(chat_id, "Как вас зовут?")
                user_states[user_id] = 'awaiting_name'
                
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка. Попробуйте позже.")
            logging.error(f"Ошибка при обработке /start: {e}")
    
    def show_admin_menu(chat_id):
        """Показывает меню администратора"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('📊 Статистика')
        btn2 = types.KeyboardButton('📦 Заказы')
        btn3 = types.KeyboardButton('👥 Клиенты')
        btn4 = types.KeyboardButton('🏪 В меню клиента')
        markup.add(btn1, btn2, btn3, btn4)
        
        admin_text = "👑 Панель администратора\nВыберите действие:"
        bot.send_message(chat_id, admin_text, reply_markup=markup)
    
    def show_customer_menu(chat_id):
        """Показывает меню клиента"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('🎂 Сделать заказ')
        btn2 = types.KeyboardButton('📖 Рецепты')
        btn3 = types.KeyboardButton('💼 Услуги')
        btn4 = types.KeyboardButton('📞 Контакты')
        markup.add(btn1, btn2, btn3, btn4)
        
        welcome_text = "🎂 Добро пожаловать! Выберите действие:"
        bot.send_message(chat_id, welcome_text, reply_markup=markup)
    
    @bot.message_handler(func=lambda message: message.text == '🏪 В меню клиента')
    def switch_to_customer_menu(message):
        """Переключение в меню клиента для администратора"""
        show_customer_menu(message.chat.id)
    
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_name')
    def handle_name_input(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        name = message.text.strip()
        username = message.from_user.username
        
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
            
            bot.send_message(chat_id, f"Приятно познакомиться, {name}! 😊\nТеперь я буду обращаться к вам по имени.")
            show_customer_menu(chat_id)
            
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка при сохранении. Попробуйте еще раз.")
            logging.error(f"Ошибка при сохранении клиента: {e}")
    
    # Обработчики для администратора
    @bot.message_handler(func=lambda message: message.text == '📊 Статистика')
    def handle_admin_stats(message):
        if not is_user_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав администратора.")
            return
        
        # Здесь будет логика для статистики
        bot.send_message(message.chat.id, "📊 Статистика в разработке...")
    
    @bot.message_handler(func=lambda message: message.text == '📦 Заказы')
    def handle_admin_orders(message):
        if not is_user_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав администратора.")
            return
        
        # Здесь будет логика для управления заказами
        bot.send_message(message.chat.id, "📦 Управление заказами в разработке...")
    
    @bot.message_handler(func=lambda message: message.text == '👥 Клиенты')
    def handle_admin_customers(message):
        if not is_user_admin(message.from_user.id):
            bot.send_message(message.chat.id, "⛔ У вас нет прав администратора.")
            return
        
        # Здесь будет логика для управления клиентами
        bot.send_message(message.chat.id, "👥 Управление клиентами в разработке...")
    
    # Старые обработчики (оставляем как есть)
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
    
    @bot.message_handler(commands=['menu'])
    def show_menu(message):
        bot.reply_to(message, "🎂 Наше меню в разработке...")
    
    @bot.message_handler(commands=['myid'])
    def show_my_id(message):
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        username = f"@{message.from_user.username}" if message.from_user.username else "нет"
        
        bot.send_message(
            message.chat.id,
            f"👤 Ваша информация:\n"
            f"🆔 ID: `{user_id}`\n"
            f"📛 Имя: {first_name}\n"
            f"📱 Username: {username}\n\n"
            f"Сообщите этот ID администратору для добавления в админы.",
            parse_mode='Markdown'
        )