from telebot import types

def register_recipe_handlers(bot):
    @bot.message_handler(func=lambda message: message.text == '📖 Рецепты')
    def show_recipes(message):
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('🎂 Торт "Наполеон"', callback_data='recipe_napoleon')
        btn2 = types.InlineKeyboardButton('🧁 Ванильные капкейки', callback_data='recipe_cupcakes')
        btn3 = types.InlineKeyboardButton('🍪 Имбирные пряники', callback_data='recipe_gingerbread')
        markup.add(btn1, btn2, btn3)
        
        bot.send_message(message.chat.id, "Выберите рецепт:", reply_markup=markup)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('recipe_'))
    def handle_recipe_callback(call):
        recipe_type = call.data.split('_')[1]
        
        if recipe_type == 'napoleon':
            recipe_text = """
            🎂 Рецепт торта "Наполеон":

            Ингредиенты для теста:
            • Мука - 500г
            • Масло сливочное - 400г
            • Вода холодная - 200мл
            • Соль - щепотка

            Ингредиенты для крема:
            • Молоко - 1л
            • Яйца - 4 шт
            • Сахар - 300г
            • Мука - 100г
            • Ванилин

            Полный рецепт: https://example.com/napoleon
            """
        elif recipe_type == 'cupcakes':
            recipe_text = "🧁 Рецепт ванильных капкейков..."
        else:
            recipe_text = "🍪 Рецепт имбирных пряников..."
        
        bot.send_message(call.message.chat.id, recipe_text)