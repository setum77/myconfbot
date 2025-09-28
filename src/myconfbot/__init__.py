# src\myconfbot\__init__.py

__version__ = "0.1.0"

# Импорты для удобства
from .bot.confectionery_bot import ConfectioneryBot, create_bot
from .config import Config

__all__ = ['ConfectioneryBot', 'create_bot', 'Config', '__version__']
