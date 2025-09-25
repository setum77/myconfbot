# src/myconfbot/logging_config.py

import logging
import logging.handlers
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Путь к директории логов (в корне проекта)
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/myconfbot.log")
LOG_FILE_PATH = Path(LOG_FILE_PATH)
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
# LOG_DIR = Path(__file__).parent.parent.parent / "logs"
# LOG_DIR.mkdir(exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Настройки логирования
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # 🔴 ВАЖНО: не отключать существующие логгеры!
    "formatters": {
        "detailed": {
            "format": "[%(asctime)s] %(levelname)-8s %(name)-20s %(filename)s:%(lineno)d | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(levelname)s | %(name)s | %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": LOG_FILE_PATH,
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },
    "root": {
        "level": LOG_LEVEL,
        "handlers": ["console", "file"],
    },
    "loggers": {
        "aiogram": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "sqlalchemy": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": True,
        },
        "httpx": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        # 🔴 ВАЖНО: отключаем DEBUG-логи urllib3 (которые творят беспорядок)
        "urllib3.connectionpool": {
            "level": "WARNING",  # ✅ Только WARNING и выше — больше не видим DEBUG
            "handlers": ["console", "file"],
            "propagate": False,
        },
        # 🔴 Дополнительно: если aiogram использует httpx (в новых версиях), но urllib3 всё равно может быть
        "urllib3.util.retry": {
            "level": "WARNING",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}


def setup_logging():
    """
    Инициализирует логирование на основе конфига.
    Вызывается ОДИН РАЗ при старте приложения.
    """
    logging.config.dictConfig(LOG_CONFIG)


# 🔴 ВАЖНО: если вы используете `uvicorn`, `gunicorn` или другой ASGI-сервер —
# вызывайте setup_logging() в точке входа, а не в модуле, чтобы избежать повторного вызова.