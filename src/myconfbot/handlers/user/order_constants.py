# src/myconfbot/handlers/user/order_constants.py

from telebot import types
from src.myconfbot.utils.database import db_manager

class OrderConstants:
    """Константы для модуля заказов"""

    # Пути
    PHOTOS_DIR = "data/order/"
    
    # Callback префиксы
    ORDER_PREFIX = "order_"
    ORDER_CATEGORY_PREFIX = "order_category_"
    ORDER_PRODUCT_PREFIX = "order_product_"
    ORDER_ACTION_PREFIX = "order_action_"
    ORDER_STEP_PREFIX = "order_step_"
    
    # Состояния оформления заказа
    ORDER_STATES = {
        'SELECTING_QUANTITY': 'order_quantity',
        'SELECTING_DATE': 'order_date', 
        'SELECTING_DELIVERY': 'order_delivery',
        'SELECTING_PAYMENT': 'order_payment',
        'ADDING_NOTES': 'order_notes',
        'CONFIRMING': 'order_confirm'
    }
    
    @staticmethod
    def create_categories_keyboard(categories, back_callback="main_menu"):
        """Создание клавиатуры для выбора категории"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        buttons = []
        for category in categories:
            # Получаем количество товаров в категории
            products_count = len(db_manager.get_products_by_category(category['id']))
            button_text = f"📁 {category['name']} ({products_count})"
            buttons.append(types.InlineKeyboardButton(
                button_text,
                callback_data=f"order_category_{category['id']}"
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
        
        
        # # Добавляем кнопки категорий в два ряда
        # buttons = []
        # for category in categories:
        #     button = types.InlineKeyboardButton(
        #         f"📁 {category['name']}",
        #         callback_data=f"order_category_{category['id']}"
        #     )
        #     buttons.append(button)
        
        # # Распределяем по два в ряд
        # for i in range(0, len(buttons), 2):
        #     if i + 1 < len(buttons):
        #         keyboard.add(buttons[i], buttons[i + 1])
        #     else:
        #         keyboard.add(buttons[i])
        
        # # Кнопка назад
        # keyboard.add(types.InlineKeyboardButton(
        #     "🔙 Назад",
        #     callback_data=back_callback
        # ))
        
        # return keyboard
    
    @staticmethod
    def create_products_keyboard(products, back_callback):
        """Создание клавиатуры для выбора товара"""
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        for product in products:
            # Обрезаем описание до 25 символов
            short_desc = product['short_description'] or ''
            if len(short_desc) > 25:
                short_desc = short_desc[:25] + "..."
            
            button_text = f"🎂 {product['name']} - {short_desc}"
            keyboard.add(types.InlineKeyboardButton(
                button_text,
                callback_data=f"order_product_{product['id']}"
            ))
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к категориям",
            callback_data=back_callback
        ))
        
        return keyboard
    
    @staticmethod
    def create_product_actions_keyboard(product_id, back_callback):
        """Клавиатура действий с товаром"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            types.InlineKeyboardButton(
                "⭐ В избранное",
                callback_data=f"order_favorite_{product_id}"
            ),
            types.InlineKeyboardButton(
                "🛒 Заказать",
                callback_data=f"order_start_{product_id}"
            )
        )
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к товарам",
            callback_data=back_callback
        ))
        
        return keyboard
    
    @staticmethod
    def create_order_confirmation_keyboard(order_data_id):
        """Клавиатура подтверждения заказа"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            types.InlineKeyboardButton(
                "✅ Подтвердить",
                callback_data=f"order_confirm_{order_data_id}"
            ),
            types.InlineKeyboardButton(
                "❌ Отменить",
                callback_data=f"order_cancel_{order_data_id}"
            )
        )
        
        return keyboard
    
    @staticmethod
    def create_back_keyboard(back_callback):
        """Простая кнопка назад"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад",
            callback_data=back_callback
        ))
        return keyboard