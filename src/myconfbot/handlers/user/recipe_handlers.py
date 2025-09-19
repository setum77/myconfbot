import logging
from telebot import types
from telebot.types import Message, CallbackQuery

from src.myconfbot.handlers.user.base_user_handler import BaseUserHandler


class RecipeHandler(BaseUserHandler):
    """Обработчик рецептов"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
        self.logger = logging.getLogger(__name__)
    
    def register_handlers(self):
        """Регистрация обработчиков рецептов"""
        self._register_recipes_handler()
        self._register_recipe_callback_handler()
    
    def _register_recipes_handler(self):
        """Регистрация обработчика кнопки рецептов"""
        @self.bot.message_handler(func=lambda message: message.text == '📖 Рецепты')
        def show_recipes(message: Message):
            self._show_recipes(message)
    
    def _register_recipe_callback_handler(self):
        """Регистрация обработчика callback'ов рецептов"""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('recipe_'))
        def handle_recipe_callback(call: CallbackQuery):
            self._handle_recipe_callback(call)
    
    def _show_recipes(self, message: Message):
        """Показать меню рецептов"""
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('🎂 Торт "Наполеон"', callback_data='recipe_napoleon')
        btn2 = types.InlineKeyboardButton('🧁 Ванильные капкейки', callback_data='recipe_cupcakes')
        btn3 = types.InlineKeyboardButton('🍪 Имбирные пряники', callback_data='recipe_gingerbread')
        markup.add(btn1, btn2, btn3)
        
        self.bot.send_message(
            message.chat.id, 
            "Выберите рецепт:", 
            reply_markup=markup
        )
    
    def _handle_recipe_callback(self, call: CallbackQuery):
        """Обработка выбора рецепта"""
        recipe_type = call.data.split('_')[1]
        
        if recipe_type == 'napoleon':
            recipe_text = self._get_napoleon_recipe()
        elif recipe_type == 'cupcakes':
            recipe_text = self._get_cupcakes_recipe()
        elif recipe_type == 'gingerbread':
            recipe_text = self._get_gingerbread_recipe()
        else:
            recipe_text = "Рецепт не найден."
        
        # Отправляем рецепт
        self.bot.send_message(call.message.chat.id, recipe_text)
        
        # Показываем кнопку для возврата к выбору рецептов
        self._show_back_to_recipes(call.message.chat.id)
    
    def _get_napoleon_recipe(self) -> str:
        """Рецепт торта Наполеон"""
        return """🎂 Рецепт торта "Наполеон":

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
    
    def _get_cupcakes_recipe(self) -> str:
        """Рецепт ванильных капкейков"""
        return """🧁 Рецепт ванильных капкейков:

Ингредиенты:
• Мука - 200г
• Сахар - 150г  
• Масло сливочное - 100г
• Яйца - 2 шт
• Молоко - 100мл
• Ванильный экстракт - 1 ч.л.
• Разрыхлитель - 1 ч.л.

Приготовление:
1. Размягченное масло взбить с сахаром
2. Добавить яйца по одному, продолжая взбивать
3. Добавить муку с разрыхлителем и молоко
4. Разлить по формочкам и выпекать 20 минут при 180°C

Полный рецепт: https://example.com/cupcakes
"""
    
    def _get_gingerbread_recipe(self) -> str:
        """Рецепт имбирных пряников"""
        return """🍪 Рецепт имбирных пряников:

Ингредиенты:
• Мука - 300г
• Мед - 100г
• Сахар - 100г
• Сливочное масло - 50г
• Яйцо - 1 шт
• Имбирь молотый - 1 ст.л.
• Корица - 1 ч.л.
• Сода - 0.5 ч.л.

Приготовление:
1. Растопить мед с маслом и сахаром
2. Добавить яйцо и специи
3. Просеять муку с содой и замесить тесто
4. Раскатать, вырезать фигурки
5. Выпекать 10-12 минут при 180°C

Полный рецепт: https://example.com/gingerbread
"""
    
    def _show_back_to_recipes(self, chat_id: int):
        """Показать кнопку возврата к рецептам"""
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📖 Вернуться к рецептам", callback_data="back_to_recipes"))
        
        self.bot.send_message(
            chat_id,
            "Хотите посмотреть другой рецепт?",
            reply_markup=markup
        )
    
    # Дополнительно можно добавить обработчик для кнопки возврата
    @staticmethod
    def register_back_handler(bot):
        """Статический метод для регистрации обработчика возврата"""
        @bot.callback_query_handler(func=lambda call: call.data == 'back_to_recipes')
        def back_to_recipes(call: CallbackQuery):
            from .recipe_handlers import RecipeHandler
            # Нужно будет передать bot, config, db_manager через замыкание или глобально
            # Пока просто отправляем сообщение
            bot.send_message(call.message.chat.id, "Возврат к выбору рецептов...")
            # Здесь нужно вызвать show_recipes, но требуется экземпляр RecipeHandler