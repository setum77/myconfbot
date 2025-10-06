# product_management.py (основной класс)
import logging
logger = logging.getLogger(__name__)

import os
from telebot import types
from telebot.types import Message, CallbackQuery

from .admin_base import BaseAdminHandler
from .product_states import ProductState
from ..shared.product_constants import ProductConstants
from .product_creator import ProductCreator
from .product_editor import ProductEditor
from .product_viewer import ProductViewer
from .photo_manager import PhotoManager
from .category_manager import CategoryManager
from src.myconfbot.services.auth_service import AuthService

class ProductManagementHandler(BaseAdminHandler):
    """Упрощенный обработчик управления продукцией"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
        self.photos_dir = ProductConstants.PHOTOS_DIR
        auth_service = AuthService(db_manager)
        # Инициализация компонентов
        self.photo_manager = PhotoManager(bot, db_manager, self.states_manager, self.photos_dir)
        self.creator = ProductCreator(bot, db_manager, self.states_manager, self.photos_dir, self.photo_manager)
        self.product_editor = ProductEditor(bot, db_manager, self.states_manager, self.photos_dir)
        self.viewer = ProductViewer(bot, db_manager, self.photos_dir)
        self.category_manager = CategoryManager(bot, db_manager, self.states_manager, auth_service)
        
        # Создаем директорию для фото
        try:
            os.makedirs(self.photos_dir, exist_ok=True)
            logger.info(f"✓ Директория {self.photos_dir} доступна для записи")
        except Exception as e:
            logger.error(f"❌ Ошибка доступа к директории {self.photos_dir}: {e}")

    def register_handlers(self):
        """Регистрация обработчиков"""
        self._register_callbacks()
        self._register_state_handlers()
        self._register_photo_handlers()
        self._register_category_handlers()
        self.photo_manager.register_photo_handlers() 
    
    def _register_photo_handlers(self):
        """Регистрация обработчиков фото"""
        # Callback'и для управления фото
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('photo_'))
        def handle_photo_callbacks(callback: CallbackQuery):
            self.photo_manager.handle_photo_callbacks(callback)
        
        # # Обработчик добавления фото
        # @self.bot.message_handler(
        #     func=lambda message: (
        #         self.states_manager.get_product_state(message.from_user.id) == ProductState.ADDING_PHOTOS and
        #         message.content_type == 'photo'
        #     )
        # )
        # def handle_photo_add(message: Message):
        #     user_data = self.states_manager.get_product_data(message.from_user.id)
        #     product_id = user_data.get('id')
        #     if product_id:
        #         logger.info(f"Начало добавления фото для товара {product_id}")
        #         success = self.photo_manager.handle_photo_addition(message, product_id)
        #         if success:
        #             self.bot.send_message(message.chat.id, "✅ Фото добавлено!")
        #             photos = self.db_manager.get_product_photos(product_id)
        #             logger.info(f"После добавления - фото в базе: {len(photos)} шт.")
        #         else:
        #             self.bot.send_message(message.chat.id, "❌ Ошибка при добавлении фото")
        #     else:
        #         self.bot.send_message(message.chat.id, "❌ Ошибка: товар не найден")
        
        # Обработчик завершения добавления фото
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_product_state(message.from_user.id) == ProductState.ADDING_PHOTOS and
                message.text == "✅ Готово"
            )
        )
        def handle_photos_done(message: Message):
            product_id = self.photo_manager.handle_photos_done(message)
            if product_id:
                # После завершения добавления фото показываем итоговую информацию
                self.viewer.show_product_summary(message, product_id)
                self.states_manager.clear_product_state(message.from_user.id)
        
        # # # Обработчик вопроса о фото
        # @self.bot.message_handler(
        #     func=lambda message: (
        #         self.states_manager.get_product_state(message.from_user.id) == ProductState.PHOTO_QUESTION
        #     )
        # )
        # def handle_photo_question(message: Message):
        #     self._handle_photo_question(message)  #
        
        # Обработчик выбора фото для установки основного
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_management_state(message.from_user.id) is not None and
                self.states_manager.get_management_state(message.from_user.id).get('state') == 'editing_main_photo'
            )
        )
        def handle_edit_main_photo_selection(message: Message):
            self._handle_edit_main_photo_selection(message)
        
        # Обработчик выбора фото для удаления
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_management_state(message.from_user.id) is not None and
                self.states_manager.get_management_state(message.from_user.id).get('state') == 'editing_delete_photo'
            )
        )
        def handle_edit_photo_deletion(message: Message):
            self._handle_edit_photo_deletion(message)

        # Обработчик выбора основного фото
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_management_state(message.from_user.id) is not None and
                self.states_manager.get_management_state(message.from_user.id).get('state') == 'selecting_main_photo'
            )
        )
        def handle_main_photo_selection(message: Message):
            self.photo_manager.handle_main_photo_selection(message)

        # Обработчик удаления фото
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_management_state(message.from_user.id) is not None and
                self.states_manager.get_management_state(message.from_user.id).get('state') == 'deleting_photo'
            )
        )
        def handle_photo_deletion(message: Message):
            self.photo_manager.handle_photo_deletion(message)


    def _register_category_handlers(self):
        """Регистрация обработчиков категорий"""
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_management_state(message.from_user.id) is not None
            )
        )
        def handle_category_states(message: Message):
            self.category_manager.handle_category_states(message)
    
    def _register_callbacks(self):
        """Регистрация callback'ов"""
        # обработчик callback'ов продукции
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
        def handle_product_callbacks(callback: CallbackQuery):
            self._handle_main_callbacks(callback)
        
        # обработчик callback'ов категорий товаров
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('category_'))
        def handle_category_callbacks(callback: CallbackQuery):
            self.category_manager.handle_category_callbacks(callback)

        # обработчик callback'ов просмотра
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('view_'))
        def handle_view_callbacks(callback: CallbackQuery):
            self.viewer.handle_view_callbacks(callback)
        
        # обработчик callback'ов редактирования
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('edit_'))
        def handle_edit_callbacks(callback: CallbackQuery):
            self.product_editor.handle_edit_callbacks(callback)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('photo_'))
        def handle_photo_callbacks(callback: CallbackQuery):
            # Определяем контекст (создание или редактирование)
            user_state = self.states_manager.get_product_state(callback.from_user.id)
            if user_state and user_state == 'photo_management':
                self.photo_manager.handle_photo_callbacks_after_creation(callback)
            else:
                self.photo_manager.handle_photo_callbacks(callback)

    def _register_state_handlers(self):
        """Регистрация обработчиков состояний"""
        # Обработка основной информации
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.WAITING_BASIC_INFO
        )
        def handle_basic_info(message: Message):
            self.creator.handle_basic_info(message)

        # Обработка детальной информации
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.WAITING_DETAILS
        )
        def handle_details(message: Message):
            self.creator.handle_details(message)

        # Обработка подтверждения
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.CONFIRMATION
        )
        def handle_confirmation(message: Message):
            self.creator._handle_confirmation(message)

        # Обработка вопроса о фото 
        @self.bot.message_handler(
            func=lambda message: 
                self.states_manager.get_product_state(message.from_user.id) == ProductState.PHOTO_QUESTION
        )
        def handle_photo_question(message: Message):
            self._handle_photo_question(message)

        # Обработчик добавления фото в режиме редактирования
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_management_state(message.from_user.id) is not None and
                self.states_manager.get_management_state(message.from_user.id).get('state') == 'editing_add_photo'
            )
        )
        def handle_edit_photo_addition(message: Message):
            self._handle_edit_photo_addition(message)


        # Обработчик отмены
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_product_state(message.from_user.id) is not None and
                message.text == "❌ Отмена"
            )
        )
        def handle_cancel(message: Message):
            self._cancel_creation(message)

        # Обработчик состояний редактирования
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_management_state(message.from_user.id) is not None and
                self.states_manager.get_management_state(message.from_user.id).get('state', '').startswith('editing_')
            )
        )
        def handle_edit_states(message: Message):
            self.product_editor.handle_edit_states(message)

    def _handle_main_callbacks(self, callback: CallbackQuery):
        """Обработка основных callback'ов"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            data = callback.data
            
            if data == 'product_add':
                self.creator.start_creation(callback)
            elif data == 'product_edit':
                self.product_editor.start_editing(callback)
            elif data == 'product_view':
                self.viewer.start_viewing(callback.message)
            elif data == 'product_delete':
                self._delete_products(callback.message)
            # elif data.startswith('edit_'):
            #     self.product_editor.handle_edit_callbacks(callback)
                
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка в product callback: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при обработке")

    def manage_products(self, message: Message):
        """Управление продукцией"""
        if not self._check_admin_access(message=message):
            return
        
        self.bot.send_message(
            message.chat.id,
            ProductConstants.PRODUCT_MANAGEMENT_TITLE,
            reply_markup=ProductConstants.create_management_keyboard(),
            parse_mode='HTML'
        )

    def _cancel_creation(self, message: Message):
        """Отмена создания"""
        user_id = message.from_user.id
        self.states_manager.clear_product_state(user_id)
        
        self.bot.send_message(
            message.chat.id,
            "❌ Создание товара отменено.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        self.manage_products(message)

    
    # def _show_category_management(self, callback: CallbackQuery):
    #     """Показать меню управления категориями"""
    #     keyboard = self.category_manager.create_management_keyboard()
        
    #     # Статистика категорий
    #     categories = self.db_manager.get_all_categories()
    #     stats_text = f"📊 <b>Статистика категорий</b>\n\n📁 Всего категорий: {len(categories)}\n"
        
    #     for category in categories:
    #         product_count = len(self.db_manager.get_products_by_category(category['id']))
    #         stats_text += f"• {category['name']}: {product_count} товаров\n"
        
    #     try:
    #         self.bot.edit_message_text(
    #             chat_id=callback.message.chat.id,
    #             message_id=callback.message.message_id,
    #             text=stats_text,
    #             parse_mode='HTML',
    #             reply_markup=keyboard
    #         )
    #     except:
    #         self.bot.send_message(
    #             callback.message.chat.id,
    #             stats_text,
    #             parse_mode='HTML',
    #             reply_markup=keyboard
    #         )

    # Старые методы (упрощенные)

    def _delete_products(self, message: Message):
        """Удаление товаров"""
        self.bot.send_message(message.chat.id, "🚫 Функция удаления товаров в разработке")

    # метод для обработки вопроса о фото
    def _handle_photo_question(self, message: Message):
        """Обработка вопроса о работе с фото после создания товара"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        product_id = product_data.get('id')
        
        if message.text == "📸 Работа с фото":
            # Переходим к управлению фото через photo_manager
            self.photo_manager.show_photo_management(message, product_id)
            
        elif message.text == "🏠 В меню продукции":
            # Завершаем и возвращаем в меню продукции
            self.states_manager.clear_product_state(user_id)
            self._back_to_product_management(message.chat.id)
            
        else:
            self.bot.send_message(
                message.chat.id,
                "Пожалуйста, выберите действие:",
                reply_markup=ProductConstants.create_photo_management_question_keyboard()
            )


    def _handle_edit_photo_addition(self, message: Message):
        """Обработка добавления фото в режиме редактирования"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_management_state(user_id)
        
        if not user_state or user_state.get('state') != 'editing_add_photo':
            return
        
        product_id = user_state.get('product_id')
        
        if message.text == "✅ Завершить добавление":
            # Завершаем добавление фото
            self.states_manager.clear_management_state(user_id)
            self.bot.send_message(
                message.chat.id,
                "✅ Добавление фото завершено!",
                reply_markup=types.ReplyKeyboardRemove()
            )
            # Возвращаем к управлению фото
            self.photo_manager.show_photo_management_edit(message, product_id)
            
        elif message.text == "❌ Отмена":
            # Отмена добавления фото
            self.states_manager.clear_management_state(user_id)
            self.bot.send_message(
                message.chat.id,
                "❌ Добавление фото отменено",
                reply_markup=types.ReplyKeyboardRemove()
            )
            # Возвращаем к управлению фото
            self.photo_manager.show_photo_management_edit(message, product_id)
            
        elif message.content_type == 'photo':
            # Обрабатываем добавление фото
            success = self.photo_manager.handle_photo_addition(message, product_id)
            if success:
                self.bot.send_message(message.chat.id, "✅ Фото добавлено! Продолжайте отправлять фото или нажмите '✅ Завершить добавление'")
            else:
                self.bot.send_message(message.chat.id, "❌ Ошибка при добавлении фото")
        
        else:
            self.bot.send_message(
                message.chat.id,
                "📸 Отправьте фото или нажмите '✅ Завершить добавление'",
                reply_markup=self.photo_manager._create_photos_done_edit_keyboard()
            )
    
    def _handle_edit_main_photo_selection(self, message: Message):
        """Обработка выбора основного фото в редактировании"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_management_state(user_id)
        
        if not user_state:
            return
        
        product_id = user_state.get('product_id')
        
        if message.text == "🔙 К управлению фото":
            self.states_manager.clear_management_state(user_id)
            # self.photo_manager.show_photo_management_edit(message, product_id)
            # return
            self.bot.send_message(
                message.chat.id,
                "🔙 Возврат к управлению фото",
                reply_markup=types.ReplyKeyboardRemove()  # Очищаем клавиатуру
            )
            self.photo_manager.show_photo_management_edit(message, product_id)
            return
            
        if message.text == "❌ Отмена":
            self.states_manager.clear_management_state(user_id)
            self.bot.send_message(
                message.chat.id,
                "❌ Выбор основного фото отменен",
                reply_markup=types.ReplyKeyboardRemove()
            )
            self.photo_manager.show_photo_management_edit(message, product_id)
            return
        
        try:
            photo_number = int(message.text)
            success = self.photo_manager.set_main_photo(product_id, photo_number)
            
            if success:
                self.states_manager.clear_management_state(user_id)
                self.bot.send_message(
                    message.chat.id,
                    "✅ Основное фото установлено!",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                self.photo_manager.show_photo_management_edit(message, product_id)
            else:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Ошибка при установке основного фото. Попробуйте снова:"
                )
                
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, введите номер фото:"
            )

    def _handle_edit_photo_deletion(self, message: Message):
        """Обработка удаления фото в редактировании"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_management_state(user_id)
        
        if not user_state:
            return
        
        product_id = user_state.get('product_id')
        
        if message.text == "❌ Отмена удаления":
            self.states_manager.clear_management_state(user_id)
            self.bot.send_message(
                message.chat.id,
                "❌ Удаление фото отменено",
                reply_markup=types.ReplyKeyboardRemove()  # Очищаем клавиатуру
            )
            self.photo_manager.show_photo_management_edit(message, product_id)
            return
            
        if message.text == "❌ Отмена":
            self.states_manager.clear_management_state(user_id)
            self.bot.send_message(
                message.chat.id,
                "❌ Удаление фото отменено",
                reply_markup=types.ReplyKeyboardRemove()
            )
            self.photo_manager.show_photo_management_edit(message, product_id)
            return
        
        try:
            photo_number = int(message.text)
            success = self.photo_manager.delete_photo(product_id, photo_number)
            
            if success:
                self.states_manager.clear_management_state(user_id)
                self.bot.send_message(
                    message.chat.id,
                    "✅ Фото удалено!",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                self.photo_manager.show_photo_management_edit(message, product_id)
            else:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Ошибка при удалении фото. Попробуйте снова:"
                )
                
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, введите номер фото:"
            )