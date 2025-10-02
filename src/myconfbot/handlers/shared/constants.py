# src\myconfbot\handlers\shared\constants.py

class UserStates:
    """Константы состояний пользователя"""
    AWAITING_NAME = 'awaiting_name'
    AWAITING_PHONE = 'awaiting_phone'
    AWAITING_ADDRESS = 'awaiting_address'

class CallbackTypes:
    """Типы callback данных"""
    # Админские разделы
    ADMIN_ORDERS_ACTIVE = "admin_orders_active"
    ADMIN_ORDERS_ALL = "admin_orders_all"
    ADMIN_ORDERS_CHANGE_STATUS = "admin_orders_change_status"
    ADMIN_ORDERS_STATS = "admin_orders_stats"
    
    ADMIN_STATS_GENERAL = "admin_stats_general"
    ADMIN_STATS_FINANCIAL = "admin_stats_financial"
    ADMIN_STATS_CLIENTS = "admin_stats_clients"
    ADMIN_STATS_PRODUCTS = "admin_stats_products"
    
    ADMIN_MANAGE_PRODUCTS = "admin_manage_products"
    ADMIN_MANAGE_CONTENT = "admin_manage_content"
    ADMIN_MANAGE_USERS = "admin_manage_users"
    
    # Рецепты
    RECIPES_CAKES = "recipes_cakes"
    RECIPES_CUPCAKES = "recipes_cupcakes"
    RECIPES_COOKIES = "recipes_cookies"
    RECIPES_SEASONAL = "recipes_seasonal"

class ButtonText:
    """Тексты кнопок"""
    # Основные кнопки
    PRODUCTS = '🎂 Продукция'
    MY_ORDERS = '📋 Мои заказы'
    FAVORITES = '⭐ Избранное'
    RECIPES = '📖 Рецепты'
    SERVICES = '💼 Услуги'
    CONTACTS = '📞 Контакты'
    PROFILE = '🐱 Мой профиль'
    
    # Админские кнопки
    ORDERS = '📦 Заказы'
    STATISTICS = '📊 Статистика'
    MANAGEMENT = '🏪 Управление'

class Validation:
    """Константы валидации"""
    MIN_NAME_LENGTH = 2
    MIN_ADDRESS_LENGTH = 5
    MIN_PHONE_DIGITS = 5