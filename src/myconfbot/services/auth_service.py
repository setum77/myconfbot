from typing import Optional, Dict   
from src.myconfbot.utils.database import DatabaseManager
from src.myconfbot.models import User

class AuthService:
    """Сервис для работы с аутентификацией и правами"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        # user = self.db_manager.get_user_by_telegram_id(user_id)
        #user_info = self.db_manager.get_user_info(user_id)
        user_info = self.get_user_info(user_id)

        # Отладлочная информация
        # print(f"User info for {user_id}: {user_info}")

        return bool(user_info and user_info.get('is_admin'))

    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Получить информацию о пользователе"""
        return self.db_manager.get_user_info(user_id)
    
    def create_user(self, telegram_id: int, full_name: str, 
                   username: Optional[str] = None, is_admin: bool = False) -> bool:
        """Создать нового пользователя"""
        return self.db_manager.add_user(
            telegram_id=telegram_id,
            full_name=full_name,
            telegram_username=username,
            is_admin=is_admin
        )
    
    def update_user_info(self, user_id: int, **kwargs) -> bool:
        """Обновить информацию о пользователе"""
        return self.db_manager.update_user_info(user_id, **kwargs)