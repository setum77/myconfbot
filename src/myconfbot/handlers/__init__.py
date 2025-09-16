from .admin_handlers import register_admin_handlers
from .main_handlers import register_main_handlers
from .order_handlers import register_order_handlers
from .recipe_handlers import register_recipe_handlers

__all__ = [
    'register_admin_handlers',
    'register_main_handlers', 
    'register_order_handlers',
    'register_recipe_handlers'
]



# from . import main_handlers
# from . import order_handlers
# from . import recipe_handlers
# from . import admin_handlers

# def register_handlers(bot):
#     """Регистрация всех обработчиков"""
#     main_handlers.register_main_handlers(bot)
#     order_handlers.register_order_handlers(bot)
#     recipe_handlers.register_recipe_handlers(bot)
#     admin_handlers.register_admin_handlers(bot)

# __all__ = ['register_handlers']