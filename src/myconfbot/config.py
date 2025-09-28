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

class Config:
    def __init__(self, bot_token=None, admin_ids=None):
        self.bot_token = bot_token or self.get_bot_token()
        self.admin_ids = admin_ids or self.get_admin_ids()
        self.db = DatabaseConfig()
    
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
            f"db_url={self.db.url})"
        )