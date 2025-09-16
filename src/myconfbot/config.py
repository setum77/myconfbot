import os
import logging
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
        
        if self.use_postgres:
            self.url = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        else:
            self.url = os.getenv('DATABASE_URL', 'sqlite:///data/confbot.db')

class Config:
    # Константы
    LOGS_DIR = Path('logs')
    LOG_FILE = LOGS_DIR / 'bot.log'
    
    def __init__(self, bot_token=None, admin_ids=None):
        self.bot_token = bot_token or self.get_bot_token()
        self.admin_ids = admin_ids or self.get_admin_ids()
        self.db = DatabaseConfig()
    
    @staticmethod
    def get_bot_token():
        """Получить токен бота из environment variables"""
        token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
        if not token:
            # Попробуем прочитать из файла .env вручную
            try:
                if os.path.exists('.env'):
                    with open('.env', 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.startswith('TELEGRAM_BOT_TOKEN=') or line.startswith('BOT_TOKEN='):
                                token = line.split('=', 1)[1].strip()
                                break
            except Exception as e:
                logging.error(f"Ошибка чтения .env: {e}")
                pass
            
            if not token:
                raise ValueError(
                    "TELEGRAM_BOT_TOKEN not found. Create .env file with: "
                    "TELEGRAM_BOT_TOKEN=your_token_here"
                )
        return token
    
    @staticmethod
    def get_log_level():
        """Получить уровень логирования из env"""
        level = os.getenv('LOG_LEVEL', 'INFO').upper()
        return getattr(logging, level, logging.INFO)
    
    @classmethod
    def setup_logging(cls):
        """Настройка логирования с созданием директорий"""
        # Создаем директорию для логов
        cls.LOGS_DIR.mkdir(exist_ok=True)
        
        # Получаем уровень логирования
        log_level = cls.get_log_level()
        
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
            cls.LOG_FILE,
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
            force=True
        )
        
        logger = logging.getLogger('ConfectioneryBot')
        logger.info("Настройка логирования завершена")
        return logger

    @staticmethod
    def get_admin_ids():
        """Получение ID администраторов"""
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        if not admin_ids_str:
            # Попробуем прочитать из файла .env вручную
            try:
                if os.path.exists('.env'):
                    with open('.env', 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.startswith('ADMIN_IDS='):
                                admin_ids_str = line.split('=', 1)[1].strip()
                                break
            except Exception as e:
                logging.error(f"Ошибка чтения ADMIN_IDS: {e}")
                pass
        
        if not admin_ids_str:
            return []  # Пустой список вместо ошибки
        
        try:
            return [int(id_str.strip()) for id_str in admin_ids_str.split(',') if id_str.strip()]
        except ValueError as e:
            logging.error(f"Ошибка парсинга ADMIN_IDS: {e}")
            return []
    
    @classmethod
    def load(cls):
        """Альтернативный метод загрузки конфига"""
        return cls()  # Просто создаем экземпляр с дефолтными значениями
    
    def print_config(self):
        """Вывод конфигурации для отладки"""
        print(f"Bot token: {self.bot_token[:10]}...")
        print(f"Admin IDs: {self.admin_ids}")
        print(f"Use PostgreSQL: {self.db.use_postgres}")
        if self.db.use_postgres:
            print(f"DB Host: {self.db.host}")
            print(f"DB Name: {self.db.name}")
            print(f"DB User: {self.db.user}")