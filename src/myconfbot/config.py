# src\myconfbot\config.py

import logging
logger = logging.getLogger(__name__)

import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class DatabaseConfig:
    def __init__(self):
        self.use_postgres = os.getenv('USE_POSTGRES', 'false').lower() == 'true'
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.name = os.getenv('DB_NAME', 'confectioner_bot')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', '')
        
        # Для PostgreSQL используем полный URL из env или собираем его
        if self.use_postgres:
            self.url = os.getenv('DATABASE_URL') or f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        else:
            self.url = os.getenv('DATABASE_URL', 'sqlite:///data/confbot.db')

class FileStorageConfig:
    def __init__(self):
        # Базовая директория для всех файлов
        self.base_dir = Path(os.getenv('FILE_STORAGE_BASE_DIR', 'data'))
        
        # Поддиректории для разных типов файлов
        self.orders_dir = self.base_dir / 'orders'
        self.products_dir = self.base_dir / 'products' 
        self.users_dir = self.base_dir / 'users'
        self.temp_dir = self.base_dir / 'temp'
        
        # Создаем директории при инициализации
        self._create_directories()
    
    def _create_directories(self):
        """Создание необходимых директорий"""
        try:
            self.base_dir.mkdir(exist_ok=True)
            self.orders_dir.mkdir(exist_ok=True)
            self.products_dir.mkdir(exist_ok=True)
            self.users_dir.mkdir(exist_ok=True)
            self.temp_dir.mkdir(exist_ok=True)
            logger.info(f"Директории файлового хранилища созданы в: {self.base_dir}")
        except Exception as e:
            logger.error(f"Ошибка при создании директорий: {e}")
    
    def get_order_path(self, order_id: int, filename: str = None) -> Path:
        """Получить путь к файлам заказа"""
        order_dir = self.orders_dir / f"order_{order_id}"
        order_dir.mkdir(exist_ok=True)
        
        if filename:
            return order_dir / filename
        return order_dir
    
    def get_order_status_photos_path(self, order_id: int, filename: str = None) -> Path:
        """Получить путь к фото статусов заказа"""
        status_dir = self.get_order_path(order_id) / "status_photos"
        status_dir.mkdir(exist_ok=True)
        
        if filename:
            return status_dir / filename
        return status_dir
    
    def get_product_path(self, product_id: int, filename: str = None) -> Path:
        """Получить путь к файлам продукта"""
        product_dir = self.products_dir / str(product_id)
        product_dir.mkdir(exist_ok=True)
        
        if filename:
            return product_dir / filename
        return product_dir
    
    def get_user_path(self, telegram_id: int, filename: str = None) -> Path:
        """Получить путь к файлам пользователя"""
        user_dir = self.users_dir / str(telegram_id)
        user_dir.mkdir(exist_ok=True, parents=True)
        
        if filename:
            return user_dir / filename
        return user_dir
    
    def get_temp_path(self, filename: str = None) -> Path:
        """Получить путь к временным файлам"""
        if filename:
            return self.temp_dir / filename
        return self.temp_dir
    
    def resolve_relative_path(self, relative_path: str) -> Path:
        """Преобразовать относительный путь в абсолютный"""
        if not relative_path:
            return None
        
        # Если путь уже абсолютный, возвращаем как есть
        if os.path.isabs(relative_path):
            return Path(relative_path)
        
        # Иначе считаем, что путь относительный от base_dir
        return self.base_dir / relative_path

class Config:
    def __init__(self, bot_token=None, admin_ids=None):
        self.bot_token = bot_token or self.get_bot_token()
        self.admin_ids = admin_ids or self.get_admin_ids()
        self.db = DatabaseConfig()
        self.files = FileStorageConfig()
    
    @staticmethod
    def get_bot_token():
        """Получить токен бота из environment variables"""
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN not found. Set it in environment variables or .env file"
            )
        return token
    
    @staticmethod
    def get_admin_ids():
        """Получение ID администраторов"""
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        if not admin_ids_str:
            return []
        
        try:
            return [int(id_str.strip()) for id_str in admin_ids_str.split(',') if id_str.strip()]
        except ValueError as e:
            logging.error(f"Ошибка парсинга ADMIN_IDS: {e}")
            return []
    
    @classmethod
    def load(cls):
        """Загрузка конфигурации"""
        return cls()
    
    def __str__(self):
        """Строковое представление конфига для отладки"""
        return (
            f"Config(bot_token={self.bot_token[:10]}..., "
            f"admin_ids={self.admin_ids}, "
            f"db_url={self.db.url})",
            f"files_base_dir={self.files.base_dir})"
        )