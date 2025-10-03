from telebot import types

class AdminConstants:
    """Константы для админского функционала"""
    
    # Callback префиксы
    ORDER_ADMIN_PREFIX = "orderadm_"
    
    # Тексты кнопок
    ACTIVE_ORDERS = "📋 Активные заказы"
    ALL_ORDERS = "📚 Все заказы" 
    ORDERS_STATISTICS = "📊 Статистика заказов"
    
    ORDER_DETAILS = "📋 Подробнее"
    CHANGE_STATUS = "🔄 Изменить статус"
    ORDER_CONVERSATION = "💬 Переписка"
    
    CHANGE_COST = "💰 Изменить стоимость"
    CHANGE_DELIVERY = "🚚 Изменить доставку"
    CHANGE_READY_DATE = "⏰ Изменить дату готовности"
    CHANGE_QUANTITY = "⚖️ Изменить количество"
    CHANGE_PAYMENT_STATUS = "💳 Изменить статус оплаты"
    ADD_ADMIN_NOTES = "📝 Добавить примечание админа"
    BACK_TO_ORDERS = "🔙 Назад к заказам"
    
    ADD_STATUS = "➕ Добавить статус"
    BACK_TO_ORDER = "🔙 Назад к заказу"
    
    @staticmethod
    def get_orders_management_keyboard():
        """Клавиатура управления заказами"""
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        keyboard.add(
            types.InlineKeyboardButton(
                AdminConstants.ACTIVE_ORDERS,
                callback_data="orderadm_active_orders"
            ),
            types.InlineKeyboardButton(
                AdminConstants.ALL_ORDERS,
                callback_data="orderadm_all_orders"
            ),
            types.InlineKeyboardButton(
                AdminConstants.ORDERS_STATISTICS,
                callback_data="orderadm_statistics"
            )
        )
        
        return keyboard
    
    @staticmethod
    def create_active_orders_keyboard(orders):
        """Клавиатура со списком активных заказов"""
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        for order in orders:
            # Краткая информация для кнопки
            order_info = f"🆔{order['id']} | {order['product_name']} "
            order_info += f"| {order['user_name']} "
            order_info += f"| {order['ready_at'].strftime('%d.%m.%Y %H:%M')}"
            if len(order_info) > 56:
                order_info = order_info[:53] + "..."
                
            keyboard.add(
                types.InlineKeyboardButton(
                    order_info,
                    callback_data=f"orderadm_order_{order['id']}"
                )
            )
        
        keyboard.add(
            types.InlineKeyboardButton(
                "🔙 Назад",
                callback_data="orderadm_back_management"
            )
        )
        
        return keyboard
    
    
    @staticmethod
    def create_order_detail_keyboard(order_id):
        """Клавиатура для детальной информации о заказе"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        # Первый ряд
        keyboard.add(
            types.InlineKeyboardButton(
                AdminConstants.CHANGE_STATUS,
                callback_data=f"orderadm_change_status_{order_id}"
            ),
            types.InlineKeyboardButton(
                AdminConstants.CHANGE_COST,
                callback_data=f"orderadm_change_cost_{order_id}"
            )
        )
        
        # Второй ряд
        keyboard.add(
            types.InlineKeyboardButton(
                AdminConstants.CHANGE_DELIVERY,
                callback_data=f"orderadm_change_delivery_{order_id}"
            ),
            types.InlineKeyboardButton(
                AdminConstants.CHANGE_READY_DATE,
                callback_data=f"orderadm_change_ready_date_{order_id}"
            )
        )
        
        # Третий ряд
        keyboard.add(
            types.InlineKeyboardButton(
                AdminConstants.CHANGE_QUANTITY,
                callback_data=f"orderadm_change_quantity_{order_id}"
            ),
            types.InlineKeyboardButton(
                AdminConstants.CHANGE_PAYMENT_STATUS,
                callback_data=f"orderadm_change_payment_status_{order_id}"
            )
        )
        
        # Четвертый ряд
        keyboard.add(
            types.InlineKeyboardButton(
                AdminConstants.ADD_ADMIN_NOTES,
                callback_data=f"orderadm_add_admin_notes_{order_id}"
            ),
            types.InlineKeyboardButton(
                AdminConstants.ORDER_CONVERSATION,
                callback_data=f"orderadm_notes_{order_id}"
            )
        )
        
        # Кнопка назад
        keyboard.add(
            types.InlineKeyboardButton(
                AdminConstants.BACK_TO_ORDERS,
                callback_data="orderadm_back_active_orders"
            )
        )
        
        return keyboard
    
    
    @staticmethod
    def create_status_history_keyboard(order_id):
        """Клавиатура для истории статусов"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            types.InlineKeyboardButton(
                AdminConstants.ADD_STATUS,
                callback_data=f"orderadm_add_status_{order_id}"
            ),
            types.InlineKeyboardButton(
                AdminConstants.BACK_TO_ORDER,
                callback_data=f"orderadm_order_{order_id}"  # Используем исходный формат
            )
        )
        
        return keyboard
    
    @staticmethod
    def create_order_notes_keyboard(order_id: int):
        """Клавиатура для примечаний к заказу с кнопкой добавления сообщения"""
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        keyboard.add(
            types.InlineKeyboardButton(
                "➕ Добавить сообщение",
                callback_data=f"orderadm_add_note_{order_id}"
            ),
            types.InlineKeyboardButton(
                "🔙 Назад к заказу",
                callback_data=f"orderadm_order_{order_id}"
            )
        )
        
        return keyboard

    
    