# src/myconfbot/handlers/user/order_states.py

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)
class OrderStatesManager:
    """Менеджер состояний оформления заказа"""
    
    def __init__(self, states_manager, bot=None):
        self.states_manager = states_manager
        self.bot = bot

    def _is_bot_user(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь ботом"""
        if self.bot and user_id == self.bot.get_me().id:
            return True
        return False
    
    def start_order(self, user_id: int, product_id: int) -> None:
        """Начало оформления заказа"""
        if self._is_bot_user(user_id):
            logger.warning(f"⚠️ Пропускаем начало заказа для бота: {user_id}")
            return

        logger.info(f"🔍 Начало заказа для пользователя {user_id}, товар {product_id}")

        order_data = {
            'state': 'order_quantity',  # Начинаем с шага ввода количества
            'product_id': product_id,
            'step': 2, # Шаг 2, т.к. шаг 1 (проверка доступности) уже пройден
            'created_at': datetime.now().isoformat(),
            'notes': []  # Временное хранение примечаний до подтверждения

        }
        self.states_manager.set_user_state(user_id, order_data)
        logger.info(f"✅ Состояние заказа установлено: order_quantity")
    
    def get_order_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные текущего заказа"""
        if self._is_bot_user(user_id):
            return None
    
        data = self.states_manager.get_user_state(user_id)
        logger.info(f"🔍 Получены данные заказа для {user_id}: {data}")

        # Проверяем структуру данных
        if data and isinstance(data, dict) and data.get('state', '').startswith('order_'):
            logger.info(f"✅ Valid order data found")
            return data
        elif data:
            logger.warning(f"⚠️ Invalid order data structure: {data}")
            return None
        else:
            logger.info(f"🔍 No order data found")
            return None
        return data
    
    def update_order_data(self, user_id: int, **kwargs) -> None:
        """Обновить данные заказа"""
        if self._is_bot_user(user_id):
            logger.warning(f"⚠️ Пропускаем обновление данных для бота: {user_id}")
            return
        
        logger.info(f"🔍 Обновление данных заказа для {user_id}: {kwargs}")
        order_data = self.get_order_data(user_id)
        if order_data:
            order_data.update(kwargs)
            self.states_manager.set_user_state(user_id, order_data)
            logger.info(f"✅ Данные заказа обновлены")
        else:
            logger.warning(f"⚠️ Нет данных заказа для обновления у пользователя {user_id}")

    def add_order_note(self, user_id: int, note_text: str, is_admin: bool = False) -> None:
        """Добавить примечание к заказу (временное)"""
        if self._is_bot_user(user_id):
            return

        order_data = self.get_order_data(user_id)
        if order_data:
            if 'notes' not in order_data:
                order_data['notes'] = []
            
            order_data['notes'].append({
                'text': note_text,
                'is_admin': is_admin,
                'created_at': datetime.now().isoformat()
            })
            self.states_manager.set_user_state(user_id, order_data)
    
    def set_order_step(self, user_id: int, step: str) -> None:
        """Установить текущий шаг заказа"""
        if self._is_bot_user(user_id):
            return
        
        self.update_order_data(user_id, state=step)
    
    def complete_order(self, user_id: int) -> Dict[str, Any]:
        """Завершить заказ и вернуть данные"""
        if self._is_bot_user(user_id):
            return
        
        order_data = self.get_order_data(user_id)
        if order_data:
            self.states_manager.clear_user_state(user_id)
        return order_data or {}
    
    def cancel_order(self, user_id: int) -> None:
        """Отменить заказ"""
        if self._is_bot_user(user_id):
            return
        
        self.states_manager.clear_user_state(user_id)
    
    def is_in_order_process(self, user_id: int) -> bool:
        """Проверка, находится ли пользователь в процессе оформления заказа"""
        if self._is_bot_user(user_id):
            return False
        
        order_data = self.get_order_data(user_id)
        result = order_data is not None and order_data.get('state', '').startswith('order_')
        
        logger.info(f"🔍 DEBUG is_in_order_process: user_id={user_id}, result={result}")
        logger.info(f"🔍 DEBUG order_data: {order_data}")
        if order_data:
            logger.info(f"🔍 DEBUG state: {order_data.get('state')}")
        
        return result