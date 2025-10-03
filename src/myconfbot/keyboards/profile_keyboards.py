# src/myconfbot/keyboards/profile_keyboards.py

from telebot import types
from src.myconfbot.handlers.shared.constants import CallbackTypes

def create_profile_keyboard() -> types.InlineKeyboardMarkup:
    """Создание клавиатуры для профиля"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("✏️ Изменить имя", callback_data="edit_profile_name"),
        types.InlineKeyboardButton("📞 Изменить телефон", callback_data="edit_profile_phone")
    )
    keyboard.add(
        types.InlineKeyboardButton("📍 Изменить адрес", callback_data="edit_profile_address"),
        types.InlineKeyboardButton("📷 Изменить фото", callback_data="edit_profile_photo")
    )
    return keyboard