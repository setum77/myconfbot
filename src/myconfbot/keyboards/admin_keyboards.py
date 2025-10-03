# src\myconfbot\keyboards\admin_keyboards.py

from telebot import types
from src.myconfbot.handlers.shared.constants import CallbackTypes
from src.myconfbot.handlers.shared.admin_constants import AdminConstants

class AdminKeyboards:
    """Клавиатуры для администратора"""
    
    @staticmethod
    def get_orders_management():
        """Клавиатура управления заказами"""
        return AdminConstants.get_orders_management_keyboard()

    # @staticmethod
    # def get_orders_management() -> types.InlineKeyboardMarkup:
        # """Управление заказами"""
        # keyboard = types.InlineKeyboardMarkup()
        # keyboard.add(
        #     types.InlineKeyboardButton("📋 Активные заказы", callback_data=CallbackTypes.ADMIN_ORDERS_ACTIVE),
        #     types.InlineKeyboardButton("📊 Все заказы", callback_data=CallbackTypes.ADMIN_ORDERS_ALL)
        # )
        # keyboard.add(
        #     types.InlineKeyboardButton("🔄 Изменить статус", callback_data=CallbackTypes.ADMIN_ORDERS_CHANGE_STATUS),
        #     types.InlineKeyboardButton("📈 Статистика заказов", callback_data=CallbackTypes.ADMIN_ORDERS_STATS)
        # )
        # return keyboard
    
    @staticmethod
    def get_statistics_keyboard() -> types.InlineKeyboardMarkup:
        """Статистика"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("📊 Общая статистика", callback_data=CallbackTypes.ADMIN_STATS_GENERAL),
            types.InlineKeyboardButton("💰 Финансовая", callback_data=CallbackTypes.ADMIN_STATS_FINANCIAL)
        )
        keyboard.add(
            types.InlineKeyboardButton("👥 Клиентская", callback_data=CallbackTypes.ADMIN_STATS_CLIENTS),
            types.InlineKeyboardButton("🎂 Товарная", callback_data=CallbackTypes.ADMIN_STATS_PRODUCTS)
        )
        return keyboard
    
    @staticmethod
    def get_management_panel() -> types.InlineKeyboardMarkup:
        """Панель управления"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("🎂 Продукция", callback_data=CallbackTypes.ADMIN_MANAGE_PRODUCTS),
        )
        keyboard.add(
            types.InlineKeyboardButton("📄 Контент", callback_data=CallbackTypes.ADMIN_MANAGE_CONTENT),
            types.InlineKeyboardButton("👥 Пользователи", callback_data=CallbackTypes.ADMIN_MANAGE_USERS)
        )
        return keyboard