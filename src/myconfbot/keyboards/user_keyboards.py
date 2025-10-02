# src\myconfbot\keyboards\user_keyboards.py

from telebot import types
from src.myconfbot.handlers.shared.constants import ButtonText

class UserKeyboards:
    """Клавиатуры для пользовательского интерфейса"""
    
    @staticmethod
    def get_main_menu(is_admin: bool = False) -> types.ReplyKeyboardMarkup:
        """Главное меню"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        
        buttons = [
            ButtonText.PRODUCTS,
            ButtonText.MY_ORDERS,
            ButtonText.FAVORITES,
            ButtonText.RECIPES,
            ButtonText.SERVICES,
            ButtonText.CONTACTS,
            ButtonText.PROFILE
        ]
        
        if is_admin:
            buttons.extend([
                ButtonText.ORDERS,
                ButtonText.STATISTICS,
                ButtonText.MANAGEMENT
            ])
        
        markup.add(*[types.KeyboardButton(btn) for btn in buttons])
        return markup
    
    @staticmethod
    def get_recipes_keyboard() -> types.InlineKeyboardMarkup:
        """Клавиатура рецептов"""
        from src.myconfbot.handlers.shared.constants import CallbackTypes
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("🍰 Торты", callback_data=CallbackTypes.RECIPES_CAKES),
            types.InlineKeyboardButton("🧁 Капкейки", callback_data=CallbackTypes.RECIPES_CUPCAKES)
        )
        keyboard.add(
            types.InlineKeyboardButton("🍪 Печенье", callback_data=CallbackTypes.RECIPES_COOKIES),
            types.InlineKeyboardButton("🎂 Сезонные", callback_data=CallbackTypes.RECIPES_SEASONAL)
        )
        return keyboard