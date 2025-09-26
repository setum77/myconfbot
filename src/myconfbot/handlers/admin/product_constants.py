# product_constants.py
import logging
from telebot import types
from src.myconfbot.utils.database import db_manager

logger = logging.getLogger(__name__)
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
    def create_categories_keyboard_reply(row_width: int = 2):
        """
        Создает репли клавиатуру с категориями из базы данных
        
        Args:
            include_cancel: Добавлять ли кнопку отмены
            row_width: Количество кнопок в строке
        """     
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=row_width)  
        try:     
            categories = db_manager.get_all_categories()
            if not categories:
                # Если категорий нет, добавляем информационную кнопку
                keyboard.add(types.KeyboardButton("📭 Нет категорий"))
            else:
                buttons = []
                for category in categories:
                    category_name = category['name']
                    products_count = len(db_manager.get_products_by_category(category['id']))
                    button_text = f"📁 {category_name} ({products_count})"
                    buttons.append(types.KeyboardButton(button_text))
                for i in range(0, len(buttons), row_width):
                    row_buttons = buttons[i:i + row_width]
                    keyboard.add(*row_buttons)
        except Exception as e:
            logger.error(f"Ошибка при создании клавиатуры категорий: {e}")
            keyboard.add(types.KeyboardButton("❌ Ошибка загрузки категорий"))
       
        return keyboard

    @staticmethod
    def create_categories_keyboard_inline(categories, db_manager, back_callback="view_back_products"):
        """
        Создает inline клавиатуру с категориями для просмотра товаров
        использовать для вывода информации
        
        Args:
            categories: список категорий из БД
            db_manager: менеджер БД для получения количества товаров
            back_callback: callback_data для кнопки "Назад"
        """
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        if not categories:
            keyboard.add(types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data=back_callback
            ))
            return keyboard
        
        buttons = []
        for category in categories:
            # Получаем количество товаров в категории
            products_count = len(db_manager.get_products_by_category(category['id']))
            button_text = f"📁 {category['name']} ({products_count})"
            buttons.append(types.InlineKeyboardButton(
                button_text,
                callback_data=f"view_category_{category['id']}"
            ))
        
        # Добавляем кнопки по 2 в ряд
        for i in range(0, len(buttons), 2):
            row_buttons = buttons[i:i + 2]
            keyboard.add(*row_buttons)
        
        # Добавляем кнопку "Назад"
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад",
            callback_data=back_callback
        ))
        
        return keyboard
    
    @staticmethod
    def create_product_details_keyboard_inline(product, back_to_category=True):
        """
        Создает inline клавиатуру для детального просмотра товара
        """
        keyboard = types.InlineKeyboardMarkup()
        
        if back_to_category:
            keyboard.add(types.InlineKeyboardButton(
                "🔙 Назад к товарам",
                callback_data=f"view_back_to_category_{product['category_id']}"
            ))
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 В меню",
            callback_data="view_back_products"
        ))
        
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
    def create_availability_keyboard():
        """Клавиатура для выбора доступности"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("✅ Да"))
        keyboard.add(types.KeyboardButton("❌ Нет"))
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
    