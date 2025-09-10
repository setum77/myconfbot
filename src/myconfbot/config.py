import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    # Пути
    LOGS_DIR = Path('logs')
    LOG_FILE = LOGS_DIR / 'bot.log'
    
    @staticmethod
    def get_bot_token():
        """Получить токен бота из environment variables"""
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN not found in environment variables. "
                "Please create .env file with TELEGRAM_BOT_TOKEN=your_token"
            )
        return token
    
    @staticmethod
    def get_log_level():
        """Получить уровень логирования из env"""
        level = os.getenv('LOG_LEVEL', 'INFO').upper()
        return getattr(logging, level, logging.INFO)
    
    @staticmethod
    def setup_logging():
        """Настройка логирования с созданием директорий"""
        # Создаем директорию для логов
        Config.LOGS_DIR.mkdir(exist_ok=True)
        
        # Получаем уровень логирования
        log_level = Config.get_log_level()
        
        # Форматтер с цветами для консоли
        class ColorFormatter(logging.Formatter):
            COLORS = {
                'DEBUG': '\033[94m',    # Синий
                'INFO': '\033[92m',     # Зеленый
                'WARNING': '\033[93m',  # Желтый
                'ERROR': '\033[91m',    # Красный
                'CRITICAL': '\033[95m', # Фиолетовый
                'RESET': '\033[0m'      # Сброс
            }
            
            def format(self, record):
                log_message = super().format(record)
                if record.levelname in self.COLORS:
                    return f"{self.COLORS[record.levelname]}{log_message}{self.COLORS['RESET']}"
                return log_message
        
        # Основной форматтер для файлов
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Форматтер для консоли
        console_formatter = ColorFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Файловый обработчик
        file_handler = logging.FileHandler(
            Config.LOG_FILE,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(log_level)
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(log_level)
        
        # Настройка root logger
        logging.basicConfig(
            level=log_level,
            handlers=[file_handler, console_handler],
            force=True  # Перезаписываем существующие обработчики
        )
        
        # Создаем и возвращаем логгер
        logger = logging.getLogger('ConfectioneryBot')
        logger.info("=" * 50)
        logger.info("Настройка логирования завершена")
        logger.info("Логи будут сохраняться в: %s", Config.LOG_FILE)
        
        return logger
            
    @staticmethod
    def get_database_url():
        """Получить URL базы данных"""
        return os.getenv('DATABASE_URL', 'sqlite:///data/bot.db')
    
    @staticmethod
    def get_admin_id():
        """Получить ID администратора"""
        admin_id = os.getenv('ADMIN_ID')
        return int(admin_id) if admin_id else None