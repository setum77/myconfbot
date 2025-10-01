# src/myconfbot/handlers/user/my_order_constants.py

from telebot import types

class MyOrderConstants:
    """Константы для модуля Мои заказы"""
    
    # Callback префиксы
    MY_ORDER_PREFIX = "my_order_"
    MY_ORDER_SELECT_PREFIX = "my_order_select_"
    MY_ORDER_STATUS_PREFIX = "my_order_status_"
    MY_ORDER_NOTES_PREFIX = "my_order_notes_"
    MY_ORDER_BACK_PREFIX = "my_order_back_"
    
    @staticmethod
    def create_orders_keyboard(orders):
        """Создание клавиатуры со списком заказов"""
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        
        for order in orders:
            # Используем название продукта вместо даты
            product_name = order['product_name']
            
            # Обрезаем длинное название продукта для кнопки
            if len(product_name) > 10:
                product_name = product_name[:15] + "..."
            
            # Создаем ряд кнопок для каждого заказа
            keyboard.row(
                types.InlineKeyboardButton(
                    f"📦 {product_name}",
                    callback_data=f"my_order_select_{order['id']}"
                ),
                types.InlineKeyboardButton(
                    f"🔄 {order['current_status']}",
                    callback_data=f"my_order_status_{order['id']}"
                ),
                types.InlineKeyboardButton(
                    "💬 Переписка",
                    callback_data=f"my_order_notes_{order['id']}"
                )
            )
        
        # Кнопка назад в главное меню
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Главное меню",
            callback_data="main_menu"
        ))
        
        return keyboard
        
        # Кнопка назад в главное меню
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Главное меню",
            callback_data="main_menu"
        ))
        
        return keyboard
    
    @staticmethod
    def create_back_to_orders_keyboard():
        """Клавиатура для возврата к списку заказов"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к заказам",
            callback_data="my_order_back_to_list"
        ))
        return keyboard
    
    @staticmethod
    def create_order_detail_keyboard(order_id):
        """Клавиатура для детальной информации о заказе"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            types.InlineKeyboardButton(
                "🔄 Статус",
                callback_data=f"my_order_status_{order_id}"
            ),
            types.InlineKeyboardButton(
                "💬 Примечания", 
                callback_data=f"my_order_notes_{order_id}"
            )
        )
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к заказам",
            callback_data="my_order_back_to_list"
        ))
        
        return keyboard