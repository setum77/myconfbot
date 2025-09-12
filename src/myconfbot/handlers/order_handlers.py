import logging
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
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('🎂 Торт', callback_data='order_cake')
        btn2 = types.InlineKeyboardButton('🧁 Капкейки', callback_data='order_cupcakes')
        btn3 = types.InlineKeyboardButton('🍪 Пряники', callback_data='order_cookies')
        btn4 = types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_main')
        btn5 = types.InlineKeyboardButton('📃 Главное меню', callback_data='main_menu')
        markup.add(btn1, btn2, btn3)
        markup.add(btn5)
        
        bot.send_message(message.chat.id, "Выберите тип десерта:", reply_markup=markup)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('order_'))
    def handle_dessert_type(call):
        dessert_types = {
            'order_cake': '🎂 Торт',
            'order_cupcakes': '🧁 Капкейки', 
            'order_cookies': '🍪 Пряники'
        }
        
        dessert_type = dessert_types.get(call.data)
        if dessert_type:
            response = f"Отлично! Вы выбрали: {dessert_type}\n\nПожалуйста, опишите ваш заказ:\n• Количество\n• Вкусовые предпочтения\n• Дизайн\n• Дату получения"
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=response
            )
            bot.register_next_step_handler(call.message, process_order_description, dessert_type)
        else:
            bot.answer_callback_query(call.id, "Неизвестный тип десерта")
    
    def process_order_description(message, dessert_type):
        order_text = f"📝 Ваш заказ:\nТип: {dessert_type}\nОписание: {message.text}\n\nСпасибо! Мастер свяжется с вами в течение часа для уточнения деталей."
        bot.send_message(message.chat.id, order_text)
        
        # Здесь можно добавить логику сохранения заказа в БД
        # save_order_to_db(message, dessert_type, message.text)
    
    # Пока закоментировал, чтобы не было конфликтов с main_handlers
    # @bot.callback_query_handler(func=lambda call: call.data == 'back_to_main')
    # def back_to_main(call):
    #     from .main_handlers import show_menu
    #     bot.delete_message(call.message.chat.id, call.message.message_id)
    #     show_menu(call.message)
    
    @bot.message_handler(func=lambda message: message.text == '📃 Главное меню')
    def handle_main_menu(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Та же логика что и в /menu
        is_admin = is_user_admin(user_id)
        
        # Используем функцию show_main_menu из main_handlers
        from .main_handlers import show_main_menu
        show_main_menu(chat_id, is_admin)
    
    # После создания заказа в БД:
    # session = db_manager.get_session()
    # try:
    #     customer = db_manager.add_customer(
    #         message.from_user.id,
    #         message.from_user.username,
    #         message.from_user.first_name
    #     )
    #     
    #     order = Order(
    #         customer_id=customer.id,
    #         special_requests=special_requests,
    #         total_amount=total_amount
    #     )
    #     session.add(order)
    #     session.commit()
    #     
    #     # Уведомляем админов
    #     notify_admins_new_order(bot, order)
    #     
    # except Exception as e:
    #     session.rollback()
    #     # Обработка ошибки
    # finally:
    #     db_manager.close_session()