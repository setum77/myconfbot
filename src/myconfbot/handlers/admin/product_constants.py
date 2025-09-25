# product_constants.py
from telebot import types

class ProductConstants:
    """Константы для управления продукцией"""
    
    # Пути
    PHOTOS_DIR = "data/products/"
    
    # Сообщения
    PRODUCT_MANAGEMENT_TITLE = "🎂 Управление продукцией\nВыберите действие:"
    ADD_PRODUCT_START = "🎂 <b>Добавление нового товара</b>\n\n📝 Введите <b>название</b> товара:"
    ADD_CATEGORY_START = "📁 <b>Добавление новой категории</b>\n\n📝 Введите <b>название</b> категории:"
    
    # Единицы измерения
    MEASUREMENT_UNITS = ['шт', 'кг', 'г', 'грамм', 'л', 'мл', 'уп', 'пачка', 'упаковка', 'набор', 'комплект']
    
    # Условия оплаты
    PREPAYMENT_OPTIONS = ["50% предоплата", "100% предоплата", "Постоплата"]

    @staticmethod
    def create_management_keyboard():
        """Клавиатура управления продукцией"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            types.InlineKeyboardButton("📁 Управление категориями", callback_data="category_manage"),
            types.InlineKeyboardButton("➕ Добавить товар", callback_data="product_add")
        )
        
        
        keyboard.add(
            types.InlineKeyboardButton("✏️ Редак-ть товар", callback_data="product_edit"),
            types.InlineKeyboardButton("👀 Просмотреть", callback_data="product_view")
        )
        keyboard.add(
            types.InlineKeyboardButton("🚫 Удалить", callback_data="product_delete"),
            types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back")
        )
        
        return keyboard

    @staticmethod
    def create_cancel_keyboard():
        """Клавиатура с кнопкой отмены"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard
    
    @staticmethod
    def create_skip_keyboard():
        """Клавиатура с кнопкой пропуска"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("⏭️ Пропустить"))
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard

    @staticmethod
    def create_yes_no_keyboard():
        """Клавиатура Да/Нет"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("✅ Да"))
        keyboard.add(types.KeyboardButton("❌ Нет"))
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard

    @staticmethod
    def create_availability_keyboard():
        """Клавиатура для выбора доступности"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("✅ Да"))
        keyboard.add(types.KeyboardButton("❌ Нет"))
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard

    @staticmethod
    def create_measurement_units_keyboard():
        """Клавиатура с единицами измерения"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        unit_buttons = [types.KeyboardButton(unit) for unit in ProductConstants.MEASUREMENT_UNITS]
        for i in range(0, len(unit_buttons), 3):
            row_buttons = unit_buttons[i:i+3]
            keyboard.add(*row_buttons)
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard

    @staticmethod
    def create_prepayment_keyboard():
        """Клавиатура для выбора оплаты"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for option in ProductConstants.PREPAYMENT_OPTIONS:
            keyboard.add(types.KeyboardButton(option))
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard

    @staticmethod
    def create_confirmation_keyboard():
        """Клавиатура для подтверждения"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("✅ Сохранить"))
        keyboard.add(types.KeyboardButton("✏️ Редактировать"))
        keyboard.add(types.KeyboardButton("❌ Отменить"))
        return keyboard
    
    @staticmethod
    def create_photo_question_keyboard():
        """Клавиатура вопроса о фото после создания"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("✅ Да, добавить фото"))
        keyboard.add(types.KeyboardButton("⏭️ Пропустить"))
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard
    
    @staticmethod
    def create_photos_done_keyboard():
        """Клавиатура для завершения добавления фото"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("✅ Готово"))
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard
    