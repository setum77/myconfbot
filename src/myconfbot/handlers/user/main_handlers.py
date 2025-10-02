# src\myconfbot\handlers\user\main_handlers.py

import logging
logger = logging.getLogger(__name__)

from telebot.types import Message
from src.myconfbot.utils.content_manager import ContentManager
from src.myconfbot.handlers.user.base_user_handler import BaseUserHandler
from src.myconfbot.handlers.shared.constants import UserStates, ButtonText, Validation
from src.myconfbot.keyboards.user_keyboards import UserKeyboards
from src.myconfbot.keyboards.admin_keyboards import AdminKeyboards


class MainHandler(BaseUserHandler):
    """Обработчик основных команд и меню"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
        self.content_manager = ContentManager()
    
    def register_handlers(self):
        """Регистрация всех обработчиков"""
        self._register_start_handlers()
        self._register_menu_handlers()
        self._register_admin_buttons_handlers()
        self._register_content_handlers()
        self._register_state_handlers()
    
    def _register_start_handlers(self):
        """Регистрация обработчиков /start и /help"""
        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start(message: Message):
            self._handle_start_command(message)
    
    def _register_menu_handlers(self):
        """Регистрация обработчиков меню"""
        @self.bot.message_handler(commands=['menu'])
        def show_menu(message: Message):
            self._show_menu_command(message)
        
        @self.bot.message_handler(func=lambda message: message.text == ButtonText.PROFILE)
        def show_my_profile(message: Message):
            self._show_my_profile(message)

        @self.bot.message_handler(func=lambda message: message.text == ButtonText.PRODUCTS)
        def show_products(message: Message):
            self._show_products(message)
        
        @self.bot.message_handler(func=lambda message: message.text == ButtonText.MY_ORDERS)
        def show_my_orders(message: Message):
            self._show_my_orders(message)
        
        @self.bot.message_handler(func=lambda message: message.text == ButtonText.FAVORITES)
        def handle_favorites_message(message: Message):
            self._show_favorites(message)

    def _register_admin_buttons_handlers(self):
        """Регистрация обработчиков админских кнопок"""
        admin_buttons = [ButtonText.ORDERS, ButtonText.STATISTICS, ButtonText.MANAGEMENT]
        
        @self.bot.message_handler(func=lambda message: message.text in admin_buttons)
        def handle_admin_buttons(message: Message):
            self._handle_admin_buttons(message)

    def _register_content_handlers(self):
        """Регистрация обработчиков контента"""
        @self.bot.message_handler(func=lambda message: message.text == ButtonText.CONTACTS)
        def send_contacts(message: Message):
            self._send_contacts(message)
        
        @self.bot.message_handler(func=lambda message: message.text == ButtonText.SERVICES)
        def send_services(message: Message):
            self._send_services(message)
        
        @self.bot.message_handler(func=lambda message: message.text == ButtonText.RECIPES)
        def show_recipes(message: Message):
            self._show_recipes(message)
    
    def _register_state_handlers(self):
        """Регистрация обработчиков состояний"""
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_user_state(message.from_user.id) is not None
        )
        def handle_state_message(message: Message):
            self._handle_user_state(message)
    
    # Обработчики команд

    def _show_menu_command(self, message: Message):
        """Показ главного меню"""
        user_id = message.from_user.id
        is_admin = self.is_admin(user_id)
        markup = self.show_main_menu(message.chat.id, is_admin)
        self.bot.send_message(message.chat.id, "Главное меню", reply_markup=markup)

    def _show_products(self, message: Message):
        """Показать продукцию"""
        from .order_handler import OrderHandler
        order_handler = OrderHandler(self.bot, self.config, self.db_manager)
        order_handler.start_order_process(message)

    def _show_my_orders(self, message: Message):
        """Показать мои заказы"""
        try:
            from .my_order_handler import MyOrderHandler
            my_order_handler = MyOrderHandler(self.bot, self.config, self.db_manager)
            my_order_handler.show_user_orders(message)
        except Exception as e:
            logger.error(f"⛔️ Ошибка при показе заказов: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Произошла ошибка при загрузке заказов. Попробуйте позже."
            )

    def _show_favorites(self, message: Message):
        """Показать избранное"""
        from .order_handler import OrderHandler
        order_handler = OrderHandler(self.bot, self.config, self.db_manager)
        order_handler.show_favorites(message)

    def _show_my_profile(self, message: Message):
        """Показ профиля пользователя"""
        from .profile_handlers import ProfileHandler
        profile_handler = ProfileHandler(self.bot, self.config, self.db_manager)
        profile_handler.show_my_profile(message)
    
    def _handle_start_command(self, message: Message):
        """Обработка команд /start и /help"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        full_name = message.from_user.first_name
        username = message.from_user.username
        
        try:
            user_info = self.db_manager.get_user_info(user_id)
            
            if user_info:
                # Пользователь уже существует
                status = "администратор" if user_info['is_admin'] else "клиент"
                welcome_msg = f"С возвращением, {user_info['full_name']}! 👋\nРады снова видеть. Ваш статус: {status}!"
                self.bot.send_message(chat_id, welcome_msg)
                
                # Показываем главное меню
                markup = self.show_main_menu(chat_id, user_info['is_admin'])
                self.bot.send_message(chat_id, "Главное меню", reply_markup=markup)
            else:
                # Создаем нового пользователя
                is_admin = user_id in self.config.admin_ids
                success = self.db_manager.add_user(
                    telegram_id=user_id,
                    full_name=full_name,
                    telegram_username=username,
                    is_admin=is_admin
                )
                
                if success:
                    if is_admin:
                        self.bot.send_message(chat_id, "Добро пожаловать, администратор! 👑")
                        # Устанавливаем состояние для запроса телефона
                        self.states_manager.set_user_state(user_id, {'state': UserStates.AWAITING_PHONE})
                        self.bot.send_message(chat_id, "Пожалуйста, укажите ваш телефонный номер:")
                    else:
                        welcome_msg = f"Приятно познакомиться, {full_name}! 😊"
                        self.bot.send_message(chat_id, welcome_msg)
                        markup = self.show_main_menu(chat_id, False)
                        self.bot.send_message(chat_id, "Главное меню", reply_markup=markup)
                else:
                    self.bot.send_message(chat_id, "Произошла ошибка при создании пользователя. Попробуйте позже.")
                    return
            
            # Отправляем приветственный текст
            welcome_text = self.content_manager.get_content('welcome.md')
            if not welcome_text:
                welcome_text = "Добро пожаловать! Я бот-помощник мастера кондитера!"
            
            self.send_formatted_message(chat_id, welcome_text)
            
        except Exception as e:
            logger.error(f"⛔️ Ошибка при обработке /start: {e}", exc_info=True)
            self.bot.send_message(chat_id, "Произошла ошибка. Попробуйте позже.")
    
    def _handle_admin_buttons(self, message: Message):
        """Обработка админских кнопок"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not self.is_admin(user_id):
            self.bot.send_message(chat_id, "❌ У вас нет прав администратора.")
            return
        
        if message.text == ButtonText.ORDERS:
            self._show_orders_management(message)
        elif message.text == ButtonText.STATISTICS:
            self._show_statistics(message)
        elif message.text == ButtonText.MANAGEMENT:
            self._show_management_panel(message)
    
    def _show_orders_management(self, message: Message):
        """Показ управления заказами"""
        keyboard = AdminKeyboards.get_orders_management()
        self.bot.send_message(message.chat.id, "📦 Управление заказами\nВыберите действие:", reply_markup=keyboard)
    
    def _show_statistics(self, message: Message):
        """Показ статистики"""
        keyboard = AdminKeyboards.get_statistics_keyboard()
        self.bot.send_message(message.chat.id, "📊 Статистика\nВыберите раздел:", reply_markup=keyboard)
    
    def _show_management_panel(self, message: Message):
        """Показ панели управления"""
        keyboard = AdminKeyboards.get_management_panel()
        self.bot.send_message(message.chat.id, "🏪 Панель управления\nВыберите раздел:", reply_markup=keyboard)
    
    def _send_contacts(self, message: Message):
        """Отправка контактов"""
        contacts_text = self.content_manager.get_content('contacts.md')
        if not contacts_text:
            contacts_text = "Контактная информация пока не добавлена"
        self.send_formatted_message(message.chat.id, contacts_text)
    
    def _send_services(self, message: Message):
        """Отправка информации об услугах"""
        services_text = self.content_manager.get_content('services.md')
        if not services_text:
            services_text = "🎁 Информация по услугам пока не добавлена"
        self.send_formatted_message(message.chat.id, services_text)
    
    def _show_recipes(self, message: Message):
        """Показ рецептов"""
        keyboard = UserKeyboards.get_recipes_keyboard()
        self.bot.send_message(message.chat.id, "📖 Наши рецепты\nВыберите категорию:", reply_markup=keyboard)
    
    def _handle_user_state(self, message: Message):
        """Обработка сообщений в состоянии"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_user_state(user_id)
        
        if not user_state:
            return
        
        state = user_state.get('state')
        
        if state == UserStates.AWAITING_PHONE:
            self._handle_phone_input(message, user_state)
        elif state == UserStates.AWAITING_ADDRESS:
            self._handle_address_input(message, user_state)
    
    def _handle_phone_input(self, message: Message, user_state: dict):
        """Обработка ввода телефона"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        phone = message.text.strip()
        
        # Простая валидация телефона
        if not any(char.isdigit() for char in phone) or len(phone) < Validation.MIN_PHONE_DIGITS:
            self.bot.send_message(chat_id, "Пожалуйста, введите корректный телефонный номер.")
            return
        
        # Обновляем состояние
        user_state['phone'] = phone
        user_state['state'] = UserStates.AWAITING_ADDRESS
        self.states_manager.set_user_state(user_id, user_state)
        
        self.bot.send_message(chat_id, "Отлично! Теперь укажите ваш адрес:")
    
    def _handle_address_input(self, message: Message, user_state: dict):
        """Обработка ввода адреса"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        address = message.text.strip()
        
        if len(address) < Validation.MIN_ADDRESS_LENGTH:
            self.bot.send_message(chat_id, "Пожалуйста, введите полный адрес.")
            return
        
        try:
            # Обновляем информацию пользователя
            success = self.db_manager.update_user_info(
                user_id, 
                phone=user_state.get('phone'), 
                address=address
            )
            
            if success:
                # Очищаем состояние
                self.states_manager.clear_user_state(user_id)
                
                success_msg = (
                    f"Отлично! 👑\n"
                    f"Ваши данные сохранены. Теперь вы можете управлять кондитерской!"
                )
                self.bot.send_message(chat_id, success_msg)
                
                # Показываем главное меню
                markup = self.show_main_menu(chat_id, True)
                self.bot.send_message(chat_id, "Главное меню", reply_markup=markup)
            else:
                self.bot.send_message(chat_id, "Произошла ошибка при сохранении данных. Попробуйте еще раз.")
            
        except Exception as e:
            logger.error(f"⛔️ Ошибка при сохранении адреса: {e}", exc_info=True)
            self.bot.send_message(chat_id, "Произошла ошибка при сохранении. Попробуйте еще раз.")