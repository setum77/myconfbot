from telebot import types

def register_main_handlers(bot):
    
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
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