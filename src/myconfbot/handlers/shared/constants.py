# src\myconfbot\handlers\shared\constants.py

class UserStates:
    """Константы состояний пользователя"""
    AWAITING_NAME = 'awaiting_name'
    AWAITING_PHONE = 'awaiting_phone'
    AWAITING_ADDRESS = 'awaiting_address'
    
    ADMIN_ADDING_STATUS = "admin_adding_status"
    ADMIN_ADDING_NOTE = "admin_adding_note"
    ADMIN_ADDING_ORDER_NOTES = "admin_adding_order_notes"
    
    ADMIN_CHANGING_COST = "admin_changing_cost"
    ADMIN_CHANGING_DELIVERY = "admin_changing_delivery" 
    ADMIN_CHANGING_DELIVERY_ADDRESS = "admin_changing_delivery_address"
    ADMIN_CHANGING_READY_DATE = "admin_changing_ready_date"
    ADMIN_CHANGING_QUANTITY = "admin_changing_quantity"
    ADMIN_CHANGING_QUANTITY_VALUE = "admin_changing_quantity_value"
    ADMIN_CHANGING_PAYMENT_STATUS = "admin_changing_payment_status"
    
    EDITING_NAME = 'editing_name'
    EDITING_PHONE = 'editing_phone'
    EDITING_ADDRESS = 'editing_address'
    EDITING_PHOTO = 'editing_photo'

class CallbackTypes:
    """Типы callback данных"""
    # Профиль
    EDIT_PROFILE_NAME = "edit_profile_name"
    EDIT_PROFILE_PHONE = "edit_profile_phone"
    EDIT_PROFILE_ADDRESS = "edit_profile_address"
    EDIT_PROFILE_PHOTO = "edit_profile_photo"

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

class Messages:
    """Тексты сообщений"""
    PROFILE_TITLE = "👤 *Ваш профиль*\n\n"
    PROFILE_NAME = "📛 *Имя:* {}\n"
    PROFILE_USERNAME = "📱 *Username:* @{}\n"
    PROFILE_PHONE = "📞 *Телефон:* {}\n"
    PROFILE_ADDRESS = "📍 *Адрес:* {}\n"
    PROFILE_STATUS = "🎭 *Статус:* {}\n"
    PROFILE_NO_PHOTO = "🖼️ Фотография не добавлена"
    
    PROFILE_EDIT_NAME = "✏️ Введите ваше новое имя:"
    PROFILE_EDIT_PHONE = "📞 Введите ваш новый телефон:"
    PROFILE_EDIT_ADDRESS = "📍 Введите ваш новый адрес:"
    PROFILE_EDIT_PHOTO = "📷 Отправьте ваше новое фото:"
    
    PROFILE_UPDATE_SUCCESS = "✅ {} успешно обновлено!"
    PROFILE_PHOTO_UPDATE_SUCCESS = "✅ Фото профиля обновлено! Размер: {:.1f} KB"
    
    ERROR_PROFILE_NOT_FOUND = "❌ Профиль не найден. Попробуйте /start"
    ERROR_LOADING_PROFILE = "❌ Ошибка при загрузке профиля"
    ERROR_PHOTO_SEND = "❌ Ошибка при отправке фото"
    ERROR_PHOTO_SAVE = "❌ Ошибка при сохранении фото"
    ERROR_FIELD_UPDATE = "❌ Ошибка при обновлении {}"
    
    VALIDATION_NAME_TOO_SHORT = "❌ Имя должно быть не короче 2 символов"
    VALIDATION_PHONE_INVALID = "❌ Введите корректный телефон"
    VALIDATION_ADDRESS_TOO_SHORT = "❌ Адрес должен быть не короче 5 символов"