from telebot import types
from src.myconfbot.utils.database import db_manager
from src.myconfbot.models import Order, OrderStatus, OrderItem
# from src.myconfbot.handlers.main_handlers import show_customer_menu
from src.myconfbot.handlers.admin_handlers import notify_admins_new_order
from src.myconfbot.config import Config

# В обработчике создания заказа:
def register_order_handlers(bot):

    def is_user_admin(telegram_id):
        """Проверка, является ли пользователь администратором"""
        try:
            config = Config.load()
            if telegram_id in config.admin_ids:
                admin = db_manager.get_admin_by_telegram_id(telegram_id)
                return admin is not None
            return False
        except Exception as e:
            return False
    
    @bot.message_handler(func=lambda message: message.text == '🎂 Сделать заказ')
    def start_order(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('🎂 Торт')
        btn2 = types.KeyboardButton('🧁 Капкейки')
        btn3 = types.KeyboardButton('🍪 Пряники')
        btn4 = types.KeyboardButton('🔙 Назад')
        btn5 = types.KeyboardButton('📃 Главное меню')
        markup.add(btn1, btn2, btn3, btn4, btn5)
        
        bot.send_message(message.chat.id, "Выберите тип десерта:", reply_markup=markup)
    
    @bot.message_handler(func=lambda message: message.text in ['🎂 Торт', '🧁 Капкейки', '🍪 Пряники'])
    def handle_dessert_type(message):
        dessert_type = message.text
        response = f"Отлично! Вы выбрали: {dessert_type}\n\nПожалуйста, опишите ваш заказ:\n• Количество\n• Вкусовые предпочтения\n• Дизайн\n• Дату получения"
        
        bot.send_message(message.chat.id, response)
        bot.register_next_step_handler(message, process_order_description)
    
    def process_order_description(message):
        order_text = f"📝 Ваш заказ:\n{message.text}\n\nСпасибо! Мастер свяжется с вами в течение часа для уточнения деталей."
        bot.send_message(message.chat.id, order_text)
    
    @bot.message_handler(func=lambda message: message.text == '🔙 Назад')
    def back_to_main(message):
        from .main_handlers import show_menu
        show_menu(message)

    @bot.message_handler(func=lambda message: message.text == '📃 Главное меню')
    def handle_main_menu(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Та же логика что и в /menu
        is_admin = is_user_admin(user_id)
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('🎂 Сделать заказ')
        btn2 = types.KeyboardButton('📖 Рецепты')
        btn3 = types.KeyboardButton('💼 Услуги')
        btn4 = types.KeyboardButton('📞 Контакты')
        btn5 = types.KeyboardButton('🐱 Моя информация')
        
        if is_admin:
            btn_admin = types.KeyboardButton('👑 Админ панель')
            markup.add(btn1, btn2, btn3, btn4, btn5, btn_admin)
        else:
            markup.add(btn1, btn2, btn3, btn4, btn5)
        
        welcome_text = "🎂 Главное меню\nВыберите действие:"
        bot.send_message(chat_id, welcome_text, reply_markup=markup)    
    
    # После создания заказа в БД:
    session = db_manager.get_session()
    try:
        customer = db_manager.add_customer(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name
        )
        
        order = Order(
            customer_id=customer.id,
            special_requests=special_requests,
            total_amount=total_amount
        )
        session.add(order)
        session.commit()
        
        # Уведомляем админов
        notify_admins_new_order(bot, order)
        
    except Exception as e:
        session.rollback()
        # Обработка ошибки
    finally:
        db_manager.close_session()
       