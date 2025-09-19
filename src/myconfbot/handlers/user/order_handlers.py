import logging
from telebot import types
from telebot.types import Message, CallbackQuery

from src.myconfbot.handlers.user.base_user_handler import BaseUserHandler
from src.myconfbot.config import Config
from src.myconfbot.utils.database import DatabaseManager


class OrderHandler(BaseUserHandler):
    """Обработчик создания и управления заказами"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
        self.logger = logging.getLogger(__name__)
    
    def register_handlers(self):
        """Регистрация обработчиков заказов"""
        self._register_order_start_handler()
        self._register_dessert_type_handler()
        self._register_main_menu_handler()
    
    def _register_order_start_handler(self):
        """Регистрация обработчика начала заказа"""
        @self.bot.message_handler(func=lambda message: message.text == '🎂 Сделать заказ')
        def start_order(message: Message):
            self._start_order(message)
    
    def _register_dessert_type_handler(self):
        """Регистрация обработчика выбора типа десерта"""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_'))
        def handle_dessert_type(call: CallbackQuery):
            self._handle_dessert_type(call)
    
    def _register_main_menu_handler(self):
        """Регистрация обработчика главного меню"""
        @self.bot.message_handler(func=lambda message: message.text == '📃 Главное меню')
        def handle_main_menu(message: Message):
            self._handle_main_menu(message)
    
    def _start_order(self, message: Message):
        """Начало процесса заказа"""
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('🎂 Торт', callback_data='order_cake')
        btn2 = types.InlineKeyboardButton('🧁 Капкейки', callback_data='order_cupcakes')
        btn3 = types.InlineKeyboardButton('🍪 Пряники', callback_data='order_cookies')
        btn5 = types.InlineKeyboardButton('📃 Главное меню', callback_data='main_menu')
        
        markup.add(btn1, btn2, btn3)
        markup.add(btn5)
        
        self.bot.send_message(
            message.chat.id, 
            "Выберите тип десерта:", 
            reply_markup=markup
        )
    
    def _handle_dessert_type(self, call: CallbackQuery):
        """Обработка выбора типа десерта"""
        dessert_types = {
            'order_cake': '🎂 Торт',
            'order_cupcakes': '🧁 Капкейки', 
            'order_cookies': '🍪 Пряники'
        }
        
        dessert_type = dessert_types.get(call.data)
        if dessert_type:
            response = (
                f"Отлично! Вы выбрали: {dessert_type}\n\n"
                f"Пожалуйста, опишите ваш заказ:\n"
                f"• Количество\n• Вкусовые предпочтения\n• Дизайн\n• Дату получения"
            )
            
            self.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=response
            )
            
            # Сохраняем состояние для следующего шага
            self.states_manager.set_user_state(call.from_user.id, {
                'state': 'awaiting_order_description',
                'dessert_type': dessert_type,
                'message_id': call.message.message_id
            })
            
            # Устанавливаем следующий обработчик
            self.bot.register_next_step_handler(call.message, self._process_order_description, dessert_type)
        else:
            self.bot.answer_callback_query(call.id, "Неизвестный тип десерта")
    
    def _process_order_description(self, message: Message, dessert_type: str):
        """Обработка описания заказа"""
        user_id = message.from_user.id
        
        # Проверяем, не отменил ли пользователь
        if message.text.lower() in ['отмена', 'cancel', 'назад', '❌']:
            self.states_manager.clear_user_state(user_id)
            self.bot.send_message(message.chat.id, "❌ Создание заказа отменено.")
            return
        
        order_text = (
            f"📝 Ваш заказ:\n"
            f"Тип: {dessert_type}\n"
            f"Описание: {message.text}\n\n"
            f"Спасибо! Мастер свяжется с вами в течение часа для уточнения деталей."
        )
        
        self.bot.send_message(message.chat.id, order_text)
        
        # Очищаем состояние
        self.states_manager.clear_user_state(user_id)
        
        # Здесь можно добавить сохранение заказа в БД
        # self._save_order_to_db(message, dessert_type, message.text)
        
        # Показываем главное меню
        self._show_main_menu(message.chat.id, message.from_user.id)
    
    def _handle_main_menu(self, message: Message):
        """Обработка кнопки главного меню"""
        self._show_main_menu(message.chat.id, message.from_user.id)
    
    def _show_main_menu(self, chat_id: int, user_id: int):
        """Показать главное меню"""
        is_admin = self.is_admin(user_id)
        markup = self.show_main_menu(chat_id, is_admin)
        self.bot.send_message(chat_id, "Главное меню", reply_markup=markup)
    
    def _save_order_to_db(self, message: Message, dessert_type: str, description: str):
        """Сохранение заказа в базу данных (заглушка)"""
        try:
            # Здесь будет логика сохранения заказа
            # Пока просто логируем
            self.logger.info(
                f"Новый заказ от пользователя {message.from_user.id}: "
                f"{dessert_type} - {description}"
            )
            
            # Пример реализации:
            # order_data = {
            #     'user_id': message.from_user.id,
            #     'dessert_type': dessert_type,
            #     'description': description,
            #     'status': 'new'
            # }
            # self.db_manager.create_order(order_data)
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении заказа: {e}", exc_info=True)
            # Можно отправить сообщение об ошибке пользователю