from .main_handlers import register_main_handlers
from .order_handlers import register_order_handlers
from .recipe_handlers import register_recipe_handlers

def register_handlers(bot):
    register_main_handlers(bot)
    register_order_handlers(bot)
    register_recipe_handlers(bot)

__all__ = ['register_handlers']