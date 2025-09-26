# product_management.py (основной класс)
import logging
logger = logging.getLogger(__name__)

import os
from telebot import types
from telebot.types import Message, CallbackQuery

from .admin_base import BaseAdminHandler
from .product_states import ProductState
from .product_constants import ProductConstants
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
        
        # Обработчик добавления фото
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_product_state(message.from_user.id) == ProductState.ADDING_PHOTOS and
                message.content_type == 'photo'
            )
        )
        def handle_photo_add(message: Message):
            user_data = self.states_manager.get_product_data(message.from_user.id)
            product_id = user_data.get('id')
            if product_id:
                logger.info(f"Начало добавления фото для товара {product_id}")
                success = self.photo_manager.handle_photo_addition(message, product_id)
                if success:
                    self.bot.send_message(message.chat.id, "✅ Фото добавлено!")
                    photos = self.db_manager.get_product_photos(product_id)
                    logger.info(f"После добавления - фото в базе: {len(photos)} шт.")
                else:
                    self.bot.send_message(message.chat.id, "❌ Ошибка при добавлении фото")
            else:
                self.bot.send_message(message.chat.id, "❌ Ошибка: товар не найден")
        
        # Обработчик завершения добавления фото
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_product_state(message.from_user.id) == ProductState.ADDING_PHOTOS and
                message.text == "✅ Готово"
            )
        )
        def handle_photos_done(message: Message):
            self.photo_manager.handle_photos_done(message)
        
        # # Обработчик вопроса о фото
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_product_state(message.from_user.id) == ProductState.PHOTO_QUESTION
            )
        )
        def handle_photo_question(message: Message):
            self._handle_photo_question(message)  #


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
            self._handle_confirmation(message)

        # Обработка вопроса о фото
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.PHOTO_QUESTION
        )
        def handle_photo_question(message: Message):
            self._handle_photo_question(message)

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

    def _handle_confirmation(self, message: Message):
        """Обработка подтверждения сохранения товара"""
        user_id = message.from_user.id
        
        if message.text == "✅ Сохранить":
            product_data = self.states_manager.get_product_data(user_id)
            product_id = self.db_manager.add_product_returning_id(product_data)
            
            if product_id:
                # Обновляем данные продукта с ID
                product_data['id'] = product_id
                self.states_manager.update_product_data(user_id, product_data)
                
                # Спрашиваем про фото
                self.bot.send_message(
                    message.chat.id,
                    f"✅ Товар <b>'{product_data['name']}'</b> успешно сохранен!\n\n"
                    "📸 Хотите добавить фотографии товара?",
                    parse_mode='HTML',
                    reply_markup=ProductConstants.create_photo_question_keyboard()
                )
                
                # Устанавливаем состояние для обработки ответа о фото
                self.states_manager.set_product_state(user_id, {
                    'state': ProductState.PHOTO_QUESTION,
                    'product_data': product_data
                })
            else:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Ошибка при сохранении товара.",
                    reply_markup=ProductConstants.create_confirmation_keyboard()
                )
        
        elif message.text == "✏️ Редактировать":
            # Возврат к началу редактирования
            self.states_manager.set_product_state(user_id, {
                'state': ProductState.WAITING_BASIC_INFO,
                'product_data': self.states_manager.get_product_data(user_id)
            })
            
            self.bot.send_message(
                message.chat.id,
                "📝 Введите <b>название</b> товара:",
                parse_mode='HTML',
                reply_markup=ProductConstants.create_cancel_keyboard()
            )
        
        elif message.text == "❌ Отменить":
            self._cancel_creation(message)

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
        """Обработка вопроса о добавлении фото после создания товара"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        product_id = product_data.get('id')
        
        if message.text == "✅ Да, добавить фото":
            # ✅ Правильно - используем метод из photo_manager
            self.photo_manager.start_photo_addition_after_creation(message, product_id)
            
        elif message.text == "⏭️ Пропустить":
            # Завершаем без фото
            self.states_manager.clear_product_state(user_id)
            product = self.db_manager.get_product_by_id(product_id)
            
            self.bot.send_message(
                message.chat.id,
                f"✅ Товар '{product['name']}' готов! Можете добавить фото позже через редактирование.",
                parse_mode='HTML',
                reply_markup=types.ReplyKeyboardRemove()
            )
            
            # Показываем итоговую информацию о товаре
            self.viewer.show_product_summary(message, product_id)
            
        else:
            self.bot.send_message(
                message.chat.id,
                "Пожалуйста, выберите вариант:",
                reply_markup=ProductConstants.create_photo_question_keyboard()
            )