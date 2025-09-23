from typing import Optional, List
from src.myconfbot.utils.database import DatabaseManager
from src.myconfbot.utils.models import User

class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        return self.db_manager.get_user_by_telegram_id(telegram_id)
    
    def get_all_users(self) -> List[User]:
        """Получить всех пользователей"""
        return self.db_manager.get_all_users()
    
    def create_user(self, telegram_id: int, full_name: str, 
                   telegram_username: Optional[str] = None, 
                   is_admin: bool = False) -> bool:
        """Создать нового пользователя"""
        return self.db_manager.add_user(
            telegram_id=telegram_id,
            full_name=full_name,
            telegram_username=telegram_username,
            is_admin=is_admin
        )
    
    def update_user_info(self, user_id: int, **kwargs) -> bool:
        """Обновить информацию о пользователе"""
        return self.db_manager.update_user_info(user_id, **kwargs)
    
    def update_user_characteristic(self, user_id: int, characteristic: str) -> bool:
        """Обновить характеристику пользователя"""
        return self.db_manager.update_user_characteristic(user_id, characteristic)
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        user = self.get_user_by_telegram_id(user_id)
        return user.is_admin if user else False