import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Импортируем модели для создания таблиц
from src.myconfbot.models import Base
from src.myconfbot.config import Config


class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # Создаем папку data если её нет
            os.makedirs('data', exist_ok=True)
            
            # Используем фиксированный путь к БД
            self.engine = create_engine('sqlite:///data/confbot.db')
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            self._initialized = True
    
    def init_db(self):
        """Инициализация базы данных"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Получение сессии БД"""
        return self.Session()
    
    def close_session(self):
        """Закрытие сессии"""
        self.Session.remove()

# Глобальный экземпляр менеджера БД
db_manager = DatabaseManager()