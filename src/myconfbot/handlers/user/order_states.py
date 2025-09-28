# src/myconfbot/handlers/user/order_states.py

from typing import Dict, Any, Optional
from datetime import datetime

class OrderStatesManager:
    """Менеджер состояний оформления заказа"""
    
    def __init__(self, states_manager):
        self.states_manager = states_manager
    
    def start_order(self, user_id: int, product_id: int) -> None:
        """Начало оформления заказа"""
        order_data = {
            'state': 'order_quantity',
            'product_id': product_id,
            'step': 1,
            'created_at': datetime.now().isoformat()
        }
        self.states_manager.set_user_state(user_id, order_data)
    
    def get_order_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные текущего заказа"""
        return self.states_manager.get_user_state(user_id)
    
    def update_order_data(self, user_id: int, **kwargs) -> None:
        """Обновить данные заказа"""
        order_data = self.get_order_data(user_id)
        if order_data:
            order_data.update(kwargs)
            self.states_manager.set_user_state(user_id, order_data)
    
    def set_order_step(self, user_id: int, step: str) -> None:
        """Установить текущий шаг заказа"""
        self.update_order_data(user_id, state=step)
    
    def complete_order(self, user_id: int) -> Dict[str, Any]:
        """Завершить заказ и вернуть данные"""
        order_data = self.get_order_data(user_id)
        if order_data:
            self.states_manager.clear_user_state(user_id)
        return order_data or {}
    
    def cancel_order(self, user_id: int) -> None:
        """Отменить заказ"""
        self.states_manager.clear_user_state(user_id)
    
    def is_in_order_process(self, user_id: int) -> bool:
        """Проверка, находится ли пользователь в процессе оформления заказа"""
        order_data = self.get_order_data(user_id)
        return order_data is not None and order_data.get('state', '').startswith('order_')