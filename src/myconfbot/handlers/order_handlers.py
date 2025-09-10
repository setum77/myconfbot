from telebot import types

def register_order_handlers(bot):
    @bot.message_handler(func=lambda message: message.text == '🎂 Сделать заказ')
    def start_order(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('🎂 Торт')
        btn2 = types.KeyboardButton('🧁 Капкейки')
        btn3 = types.KeyboardButton('🍪 Пряники')
        btn4 = types.KeyboardButton('🔙 Назад')
        markup.add(btn1, btn2, btn3, btn4)
        
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
        from .main_handlers import send_welcome
        send_welcome(message)
        