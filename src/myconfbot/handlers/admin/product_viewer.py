import logging
import os
import uuid
from telebot import types
from telebot.types import Message, CallbackQuery
from .product_constants import ProductConstants
from .product_states import ProductState

logger = logging.getLogger(__name__)

class ProductViewerProductCreator:
    """Класс для просмотра товаров товаров"""
    
    def __init__(self, bot, db_manager, states_manager, photos_dir):
        self.bot = bot
        self.db_manager = db_manager
        self.states_manager = states_manager
        self.photos_dir = photos_dir