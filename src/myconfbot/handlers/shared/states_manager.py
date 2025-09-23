
from typing import Dict, Any, Optional

class StatesManager:
    """Централизованный менеджер состояний пользователей для бота."""
    def __init__(self):
        self.user_states: Dict[int, Dict[str, Any]] = {}
        self.user_management_states: Dict[int, Dict[str, Any]] = {}
        self.product_states = {}
    
    def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить состояние пользователя"""
        return self.user_states.get(user_id)
    
    def set_user_state(self, user_id: int, state_data: Dict[str, Any]) -> None:
        """Установить состояние пользователя"""
        self.user_states[user_id] = state_data
    
    def clear_user_state(self, user_id: int) -> None:
        """Очистить состояние пользователя"""
        self.user_states.pop(user_id, None)
    
    def get_management_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить состояние управления"""
        return self.user_management_states.get(user_id)
    
    def set_management_state(self, user_id: int, state_data: Dict[str, Any]) -> None:
        """Установить состояние управления"""
        self.user_management_states[user_id] = state_data
    
    def clear_management_state(self, user_id: int) -> None:
        """Очистить состояние управления"""
        self.user_management_states.pop(user_id, None)
    
    # Методы для управления товарами
    def set_product_state(self, user_id: int, state_data: dict):
        """Установить состояние для добавления товара"""
        print(f"DEBUG: Установка состояния для user_id={user_id}: {state_data}")
        self.product_states[user_id] = state_data
    
    def get_product_state(self, user_id: int) -> str:
        """Получить состояние добавления товара"""
        state_data = self.product_states.get(user_id)
        print(f"DEBUG: Получение состояния для user_id={user_id}: {state_data}")
        return state_data.get('state') if state_data else None
    
    def get_product_data(self, user_id: int) -> dict:
        """Получить данные товара"""
        state_data = self.product_states.get(user_id)
        return state_data.get('product_data', {}) if state_data else {}
    
    def update_product_data(self, user_id: int, product_data: dict):
        """Обновить данные товара"""
        if user_id in self.product_states:
            self.product_states[user_id]['product_data'] = product_data
    
    def clear_product_state(self, user_id: int):
        """Очистить состояние добавления товара"""
        if user_id in self.product_states:
            del self.product_states[user_id]