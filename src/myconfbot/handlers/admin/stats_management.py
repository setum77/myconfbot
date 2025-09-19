from telebot.types import Message

from .admin_base import BaseAdminHandler


class StatsHandler(BaseAdminHandler):
    """Обработчик статистики"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
    
    def register_handlers(self):
        """Регистрация обработчиков статистики"""
        # Будут добавлены позже
        pass
    
    def show_orders_stats(self, message: Message):
        """Показать статистику заказов"""
        if not self._check_admin_access(message=message):
            return
        
        stats = self.db_manager.get_orders_statistics()
        
        response = "📈 Статистика заказов:\n\n"
        response += f"📊 Всего заказов: {stats['total']}\n"
        response += f"✅ Выполнено: {stats['completed']}\n"
        response += f"🔄 В работе: {stats['in_progress']}\n"
        response += f"🆕 Новые: {stats['new']}\n"
        response += f"💰 Общая сумма: {stats['total_amount']} руб.\n"
        
        self.bot.send_message(message.chat.id, response)