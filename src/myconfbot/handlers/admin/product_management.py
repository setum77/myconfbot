import logging
logger = logging.getLogger(__name__)

import os
import uuid
from datetime import datetime
from telebot import types
from telebot.types import Message, CallbackQuery
from PIL import Image
from src.myconfbot.config import Config

from .admin_base import BaseAdminHandler
from .product_states import ProductState

# Config.setup_logging()
class ProductManagementHandler(BaseAdminHandler):
    """Обработчик управления продукцией"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
        self.photos_dir = "data/products/"
        # os.makedirs(self.photos_dir, exist_ok=True)

        # Проверяем и создаем директорию с правами
        try:
            os.makedirs(self.photos_dir, exist_ok=True)
            # Проверяем права на запись
            test_file = os.path.join(self.photos_dir, 'test_write.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            logger.info(f"✓ Директория {self.photos_dir} доступна для записи")
        except Exception as e:
            logger.error(f"❌ Ошибка доступа к директории {self.photos_dir}: {e}")
            # Пробуем создать в текущей директории
            self.photos_dir = "products_photos/"
            os.makedirs(self.photos_dir, exist_ok=True)
            logger.error(f"Используем альтернативную директорию: {self.photos_dir}")
    
    def register_handlers(self):
        """Регистрация обработчиков управления продукцией"""
        self._register_product_callbacks()
        self._register_product_states()
        self._register_category_states()
        self._register_edit_handlers() 

    
    def _register_product_callbacks(self):
        """Регистрация callback'ов управления продукцией"""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
        def handle_product_callbacks(callback: CallbackQuery):
            self._handle_product_callbacks(callback)
        
        # Обработчики для просмотра
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('view_category_'))
        def handle_view_category(callback: CallbackQuery):
            self._handle_view_category(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('view_product_'))
        def handle_view_product(callback: CallbackQuery):
            self._handle_view_product(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('view_back_'))
        def handle_view_back(callback: CallbackQuery):
            self._handle_view_back(callback)
        
        # Обработчики для редактирования
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('edit_'))
        def handle_edit_callbacks(callback: CallbackQuery):
            self._handle_edit_callbacks(callback)
    
    def _register_product_states(self):
        """Регистрация обработчиков состояний товаров"""

        # 12.1 Дополнительные фото
        @self.bot.message_handler(
            content_types=['photo'],
            func=lambda message: (
                self.states_manager.get_product_state(message.from_user.id) == ProductState.WAITING_ADDITIONAL_PHOTOS
            )
        )
        def handle_additional_photos(message: Message):
            print("DEBUG: Additional photos handler triggered!")
            self._handle_additional_photos(message)


        # 12.2 Дополнительные фото (кнопка "Готово")
        @self.bot.message_handler(func=lambda message: message.text == "✅ Готово")
        def handle_photos_done(message: Message):
            user_id = message.from_user.id
            current_state = self.states_manager.get_product_state(user_id)
            
            # Проверяем состояние в теле функции
            if current_state == ProductState.WAITING_ADDITIONAL_PHOTOS:
                print("DEBUG: Photos done handler called!")
                self._handle_photos_done(message)
            else:
                print(f"DEBUG: 'Готово' received but state is {current_state}")

        # 13.1 Выбор главного фото
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.SELECTING_MAIN_PHOTO
        )
        def handle_selecting_main_photo(message: Message):
            self._handle_selecting_main_photo(message)


        # 10.1 Спросить про фото
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.ASKING_FOR_PHOTOS
        )
        def handle_asking_for_photos(message: Message):
            self._handle_asking_for_photos(message)
        
        # Обработчик отмены
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_product_state(message.from_user.id) is not None and
                message.text == "❌ Отмена"
            )
        )
        def handle_product_cancel(message: Message):
            self._cancel_product_creation_message(message)

        # 1. Название
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.WAITING_NAME
        )
        def handle_product_name(message: Message):
            self._handle_product_name(message)
        
        # 2. Категория
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.WAITING_CATEGORY
        )
        def handle_product_category(message: Message):
            self._handle_product_category(message)
        
        # 3. Доступность
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.WAITING_AVAILABILITY
        )
        def handle_product_availability(message: Message):
            self._handle_product_availability(message)
        
        # 4.1 Описание
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.WAITING_DESCRIPTION
        )
        def handle_product_description(message: Message):
            self._handle_product_description(message)
        
        # 5.1 Единица измерения
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.WAITING_MEASUREMENT_UNIT
        )
        def handle_product_measurement_unit(message: Message):
            self._handle_product_measurement_unit(message)
        
        # 6.1 Количество
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.WAITING_QUANTITY
        )
        def handle_product_quantity(message: Message):
            self._handle_product_quantity(message)
        
        # 7.1 Цена
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.WAITING_PRICE
        )
        def handle_product_price(message: Message):
            self._handle_product_price(message)
        
        # 8.1 Оплата
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.WAITING_PREPAYMENT
        )
        def handle_product_prepayment(message: Message):
            self._handle_product_prepayment(message)
        
        # 9.1 Подтверждение
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.CONFIRMATION
        )
        def handle_product_confirmation(message: Message):
            self._handle_product_confirmation(message)

   
    def _register_category_states(self):
        """Регистрация обработчиков состояний категорий"""
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_management_state(message.from_user.id) is not None and
            self.states_manager.get_management_state(message.from_user.id).get('state') == 'adding_category_name'
        )
        def handle_category_name(message: Message):
            self._handle_category_name(message)
        
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_management_state(message.from_user.id) is not None and
            self.states_manager.get_management_state(message.from_user.id).get('state') == 'adding_category_description'
        )
        def handle_category_description(message: Message):
            self._handle_category_description(message)

    def _register_edit_handlers(self):
        """Регистрация обработчиков для редактирования"""
        # Обработчики callback'ов для редактирования
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('edit_'))
        def handle_edit_callbacks(callback: CallbackQuery):
            self._handle_edit_callbacks(callback)
        
        # Обработчики состояний редактирования
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_management_state(message.from_user.id) is not None and
            self.states_manager.get_management_state(message.from_user.id).get('state', '').startswith('editing_')
        )
        def handle_edit_states(message: Message):
            self._handle_edit_states(message)
    
    
    def _handle_product_callbacks(self, callback: CallbackQuery):
        """Обработка callback'ов продукции"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            data = callback.data
            
            if data == 'product_add':
                self._add_product_start(callback)
            elif data == 'product_add_category':
                self._add_category_start(callback)
            elif data == 'product_edit':
                self._edit_products_start(callback) # self._edit_products(callback.message)
            elif data == 'product_view':
                self._view_products(callback.message)
            elif data == 'product_delete':
                self._delete_products(callback.message)
            elif data == 'product_cancel':
                self._cancel_product_creation(callback)
            elif data == 'category_cancel': 
                self._cancel_category_creation(callback)
            elif data == 'product_edit_back':
                self.manage_products(callback.message)
            # elif data == 'product_confirm':
            #     self._confirm_product_creation(callback)
                
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка в product callback: {e}", exc_info=True)
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при обработке")
    
    def manage_products(self, message: Message):
        """Управление продукцией"""
        if not self._check_admin_access(message=message):
            return
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("➕ Добавить товар", callback_data="product_add"),
            types.InlineKeyboardButton("📁 Добавить категорию", callback_data="product_add_category")
        )
        keyboard.add(
            types.InlineKeyboardButton("✏️ Редактировать", callback_data="product_edit"),
            types.InlineKeyboardButton("👀 Просмотреть", callback_data="product_view")
        )
        keyboard.add(
            types.InlineKeyboardButton("🚫 Удалить", callback_data="product_delete"),
            types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back")
        )
        
        self.bot.send_message(
            message.chat.id,
            "🎂 Управление продукцией\nВыберите действие:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    def _add_product_start(self, callback: CallbackQuery):
        """1. Начало добавления товара"""
        print(f'\n === 1. Начало добавления товара ===\n')
        # Инициализируем состояние
        self.states_manager.set_product_state(callback.from_user.id, {
            'state': ProductState.WAITING_NAME,
            'product_data': {
                'additional_photos': []
            }
        })
        
        # Удаляем предыдущее сообщение
        try:
            self.bot.delete_message(callback.message.chat.id, callback.message.message_id)
        except:
            pass
        
        # Отправляем первое сообщение
        self.bot.send_message(
            callback.message.chat.id,
            "🎂 <b>Добавление нового товара</b>\n\n"
            "📝 Введите <b>название</b> товара:",
            parse_mode='HTML',
            reply_markup=self._create_cancel_keyboard()
        )
        self.bot.answer_callback_query(callback.id)
    
    def _handle_product_name(self, message: Message):
        """Обработка названия товара"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        product_data['name'] = message.text
        self.states_manager.update_product_data(user_id, product_data)
        self.states_manager.set_product_state(user_id, {
            'state': ProductState.WAITING_CATEGORY,
            'product_data': product_data
        })
        
        # Показываем клавиатуру с категориями
        keyboard = self._create_categories_keyboard()
        
        self.bot.send_message(
            message.chat.id,
            "📁 Выберите <b>категорию</b> товара:",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    def _handle_product_category(self, message: Message):
        """Обработка категории товара"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        # Получаем категории из базы
        categories = self.db_manager.get_all_categories()
        category_names = [cat['name'].lower() for cat in categories]
        
        if message.text.lower() not in category_names:
            self.bot.send_message(
                message.chat.id,
                "❌ Категория не найдена. Выберите из предложенных:",
                reply_markup=self._create_categories_keyboard()
            )
            return
        
        # Находим ID категории
        category_id = next((cat['id'] for cat in categories if cat['name'].lower() == message.text.lower()), None)
        
        product_data['category_id'] = category_id
        self.states_manager.update_product_data(user_id, product_data)
        self.states_manager.set_product_state(user_id, {
            'state': ProductState.WAITING_AVAILABILITY,  # 3. Доступность
            'product_data': product_data
        })
        
        # Клавиатура для выбора доступности
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("✅ Да"))
        keyboard.add(types.KeyboardButton("❌ Нет"))
        keyboard.add(types.KeyboardButton("❌ Отмена"))

        self.bot.send_message(
            message.chat.id,
            "🔄 <b>Товар доступен для заказа?</b>",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    def _handle_product_availability(self, message: Message):
        """Обработка доступности товара"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        if message.text == "✅ Да":
            product_data['is_available'] = True
        elif message.text == "❌ Нет":
            product_data['is_available'] = False
        else:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, выберите вариант:",
                reply_markup=self._create_availability_keyboard()
            )
            return
        
        self.states_manager.update_product_data(user_id, product_data)
        self.states_manager.set_product_state(user_id, {
            'state': ProductState.WAITING_DESCRIPTION,  # 4.1 Описание
            'product_data': product_data
        })
            
        self.bot.send_message(
            message.chat.id,
            "📝 Введите <b>краткое описание</b> товара (или нажмите 'Пропустить'):",
            parse_mode='HTML',
            reply_markup=self._create_skip_keyboard()
        )

    def _handle_asking_for_photos(self, message: Message):
        """Обработка ответа на вопрос о фотографиях"""
        print(f'\n == Обработка вопроса о фото {message.text=}')
        
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)

        if message.text == "✅ Да":
            # Удаляем предыдущее сообщение с кнопками
            try:
                self.bot.delete_message(message.chat.id, message.message_id)
            except Exception as e:
                print(f"Не удалось удалить сообщение: {e}")
            
            # Переходим к добавлению дополнительных фото
            new_state = ProductState.WAITING_ADDITIONAL_PHOTOS
            print(f'Устанавливаем новое состояние: {new_state}')
            self.states_manager.set_product_state(user_id, {
                'state': new_state,
                'product_data': product_data
            })

            self.bot.send_message(
                message.chat.id,
                "📸 Отправьте <b>фотографии</b> товара (можно несколько):\n\n"
                "После добавления всех фото нажмите '✅ Готово'",
                parse_mode='HTML',
                reply_markup=self._create_photos_done_keyboard()
            )
        
        elif message.text == "❌ Нет":
            # Завершаем процесс без фото
            self.states_manager.clear_product_state(user_id)
            
            self.bot.send_message(
                message.chat.id,
                f"✅ Товар <b>'{product_data['name']}'</b> успешно добавлен без фотографий!",
                parse_mode='HTML',
                reply_markup=types.ReplyKeyboardRemove()
            )
            self.manage_products(message)
        
        else:
            self.bot.send_message(
                message.chat.id,
                "Пожалуйста, выберите вариант:",
                reply_markup=self._create_yes_no_keyboard()
            )
    
    
    # def _handle_main_photo(self, message: Message):
    #     """Обработка основного фото"""
    #     print('Обработка основного фото')
    #     user_id = message.from_user.id
    #     product_data = self.states_manager.get_product_data(user_id)
        
    #     try:
    #         # Сохраняем основное фото
    #         photo_id = message.photo[-1].file_id
    #         photo_path = self._save_photo(photo_id, product_data['id'])  # Сохраняем сразу в папку товара
            
    #         if photo_path:
    #             # Сохраняем фото в базу
    #             self.db_manager.add_product_photo(product_data['id'], photo_path, is_main=True)
                
    #             # Обновляем данные
    #             product_data['cover_photo_path'] = photo_path
    #             self.db_manager.update_product_cover_photo(product_data['id'], photo_path)
    #             self.states_manager.update_product_data(user_id, product_data)
                
    #             # Переходим к дополнительным фото
    #             self.states_manager.set_product_state(user_id, {
    #                 'state': ProductState.WAITING_ADDITIONAL_PHOTOS,
    #                 'product_data': product_data
    #             })
                
    #             self.bot.send_message(
    #                 message.chat.id,
    #                 "✅ Основное фото сохранено!\n\n"
    #                 "📸 Теперь можете отправить <b>дополнительные фото</b> "
    #                 "или нажмите '✅ Готово' чтобы завершить:",
    #                 parse_mode='HTML',
    #                 reply_markup=self._create_photos_done_keyboard()
    #             )
    
    #     except Exception as e:
    #         logger.error(f"Ошибка при обработке основного фото: {e}")
    #         self.bot.send_message(
    #             message.chat.id,
    #             "❌ Ошибка при сохранении фото. Попробуйте еще раз.",
    #             reply_markup=self._create_cancel_keyboard()
    #         )
    
    
    def _handle_additional_photos(self, message: Message):
        """Обработка дополнительных фотографий"""
        print(f'\n == обработка доп. фото {message=}, {message.photo=}\n')
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        print(f'Handling additional photo for product ID: {product_data.get("id")}')
        
        try:
            # Сохраняем фото
            photo_id = message.photo[-1].file_id
            print(f'Photo file ID: {photo_id}')
            photo_path = self._save_photo(photo_id, product_data['id'])
            print(f'Saved photo path: {photo_path}')
            
            if photo_path:
                # Сохраняем фото в базу (пока не как основное)
                success = self.db_manager.add_product_photo(product_data['id'], photo_path, is_main=False)
                print(f'Photo added to DB: {success}')
                
                if success:
                    # Добавляем путь к фото в данные продукта
                    if 'additional_photos' not in product_data:
                        product_data['additional_photos'] = []
                    product_data['additional_photos'].append(photo_path)
                    self.states_manager.update_product_data(user_id, product_data)
                    
                    # Получаем обновленный список фото из БД
                    photos = self.db_manager.get_product_photos(product_data['id'])
                    print(f'Total photos in DB: {len(photos)}')
                    
                    self.bot.send_message(
                        message.chat.id,
                        f"✅ Фото добавлено! Всего фото: {len(photos)}\n"
                        "Можете отправить еще фото или нажмите '✅ Готово' чтобы завершить",
                        reply_markup=self._create_photos_done_keyboard()
                    )
                else:
                    self.bot.send_message(
                        message.chat.id,
                        "❌ Ошибка при сохранении фото в базу данных.",
                        reply_markup=self._create_photos_done_keyboard()
                    )
            else:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Ошибка при сохранении фото на диск.",
                    reply_markup=self._create_photos_done_keyboard()
                )
        
        except Exception as e:
            logger.error(f"Ошибка при обработке дополнительного фото: {e}")
            import traceback
            traceback.print_exc()
            self.bot.send_message(
                message.chat.id,
                "❌ Произошла ошибка при обработке фото. Попробуйте еще раз.",
                reply_markup=self._create_photos_done_keyboard()
            )
    
    def _handle_selecting_main_photo(self, message: Message):
        """Обработка выбора главного фото"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        try:
            # Проверяем, что введен номер фото
            photo_number = int(message.text)
            photos = self.db_manager.get_product_photos(product_data['id'])
            
            if 1 <= photo_number <= len(photos):
                # Устанавливаем выбранное фото как основное
                selected_photo = photos[photo_number - 1]
                self.db_manager.set_main_photo(product_data['id'], selected_photo['photo_path'])
                
                # Обновляем cover_photo_path в продукте
                product_data['cover_photo_path'] = selected_photo['photo_path']
                self.db_manager.update_product_cover_photo(product_data['id'], selected_photo['photo_path'])
                
                self.states_manager.clear_product_state(user_id)
                
                self.bot.send_message(
                    message.chat.id,
                    f"✅ Главное фото установлено! Товар полностью готов.\n\n"
                    f"🎂 <b>{product_data['name']}</b> успешно добавлен!",
                    parse_mode='HTML',
                    reply_markup=types.ReplyKeyboardRemove()
                )
                
                # Возвращаемся к управлению продукцией
                self.manage_products(message)
            else:
                self.bot.send_message(
                    message.chat.id,
                    f"❌ Неверный номер. Введите число от 1 до {len(photos)}:",
                    reply_markup=self._create_photo_selection_keyboard(photos)
                )
        
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, введите номер фото:",
                reply_markup=self._create_photo_selection_keyboard(
                    self.db_manager.get_product_photos(product_data['id'])
                )
            )
    
    def _handle_photos_done(self, message: Message):
        """Обработка завершения добавления фото"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        photos = self.db_manager.get_product_photos(product_data['id'])
        
        if len(photos) == 0:
            # Если нет фото, просто завершаем
            self.states_manager.clear_product_state(user_id)
            self.bot.send_message(
                message.chat.id,
                f"✅ Товар <b>'{product_data['name']}'</b> успешно добавлен без фотографий!",
                parse_mode='HTML',
                reply_markup=types.ReplyKeyboardRemove()
            )
            self.manage_products(message)
        
        elif len(photos) == 1:
            # Если только одно фото, устанавливаем его как основное
            photo = photos[0]
            self.db_manager.set_main_photo(product_data['id'], photo['photo_path'])
            self.db_manager.update_product_cover_photo(product_data['id'], photo['photo_path'])
            
            self.states_manager.clear_product_state(user_id)
            self.bot.send_message(
                message.chat.id,
                f"✅ Товар <b>'{product_data['name']}'</b> успешно добавлен с 1 фотографией!",
                parse_mode='HTML',
                reply_markup=types.ReplyKeyboardRemove()
            )
            self.manage_products(message)
        
        else:
            # Если несколько фото, предлагаем выбрать главное
            self.states_manager.set_product_state(user_id, {
                'state': ProductState.SELECTING_MAIN_PHOTO,
                'product_data': product_data
            })
            
            # Показываем список фото для выбора
            photos_text = "\n".join([f"{i}. 📸 Фото {i}" for i in range(1, len(photos) + 1)])
            
            self.bot.send_message(
                message.chat.id,
                f"📸 У вас {len(photos)} фотографий. Выберите <b>главное фото</b>:\n\n{photos_text}",
                parse_mode='HTML',
                reply_markup=self._create_photo_selection_keyboard(photos)
            )

    def _handle_product_description(self, message: Message):
        """Обработка описания товара"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        if message.text.lower() == '⏭️ пропустить':
            product_data['short_description'] = ''
        else:
            product_data['short_description'] = message.text
        
        self.states_manager.update_product_data(user_id, product_data)
        self.states_manager.set_product_state(user_id, {
            'state': ProductState.WAITING_MEASUREMENT_UNIT,  # 7. Единица измерения
            'product_data': product_data
        })
        
        # Показываем клавиатуру с единицами измерения
        keyboard = self._create_measurement_units_keyboard()
        
        self.bot.send_message(
            message.chat.id,
            "📏 Выберите <b>единицу измерения</b> для товара:",
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def _handle_product_measurement_unit(self, message: Message):
        """Обработка выбора единицы измерения"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        valid_units = ['шт', 'кг', 'г', 'грамм', 'л', 'мл', 'уп', 'пачка', 'упаковка', 'набор', 'комплект']

        # Отладочная информация
        logger.info(f"Выбрана единица измерения: {message.text}")
        logger.info(f"Допустимые единицы: {valid_units}")
        
        if message.text not in valid_units:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, выберите единицу измерения из предложенных:",
                reply_markup=self._create_measurement_units_keyboard()
            )
            return
        
        product_data['measurement_unit'] = message.text
        self.states_manager.update_product_data(user_id, product_data)

        # Отладочная информация
        logger.info(f"Сохраненная единица измерения: {product_data['measurement_unit']}")

        self.states_manager.set_product_state(user_id, {
            'state': ProductState.WAITING_QUANTITY,  # 8. Количество
            'product_data': product_data
        })
        
        self.bot.send_message(
            message.chat.id,
            "⚖️ Введите <b>количество</b> товара:",
            parse_mode='HTML',
            reply_markup=self._create_cancel_keyboard()
        )

    def _handle_product_quantity(self, message: Message):
        """Обработка количества товара"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        try:
            quantity = float(message.text)
            product_data['quantity'] = quantity
            self.states_manager.update_product_data(user_id, product_data)
            self.states_manager.set_product_state(user_id, {
                'state': ProductState.WAITING_PRICE,  # 9. Цена
                'product_data': product_data
            })
            
            self.bot.send_message(
                message.chat.id,
                "💰 Введите <b>цену</b> товара:",
                parse_mode='HTML',
                reply_markup=self._create_cancel_keyboard()
            )
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, введите число:",
                reply_markup=self._create_cancel_keyboard()
            )

    def _handle_product_price(self, message: Message):
        """Обработка цены товара"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        try:
            price = float(message.text)
            product_data['price'] = price
            self.states_manager.update_product_data(user_id, product_data)
            self.states_manager.set_product_state(user_id, {
                'state': ProductState.WAITING_PREPAYMENT,  # 10. Оплата
                'product_data': product_data
            })
            
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(types.KeyboardButton("50% предоплата"))
            keyboard.add(types.KeyboardButton("100% предоплата"))
            keyboard.add(types.KeyboardButton("Постоплата"))
            keyboard.add(types.KeyboardButton("❌ Отмена"))
            
            self.bot.send_message(
                message.chat.id,
                "💳 Выберите <b>условия оплаты</b>:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, введите число:",
                reply_markup=self._create_cancel_keyboard()
            )

    def _handle_product_prepayment(self, message: Message):
        """Обработка условий оплаты"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        product_data['prepayment_conditions'] = message.text
        self.states_manager.update_product_data(user_id, product_data)
        self.states_manager.set_product_state(user_id, {
            'state': ProductState.CONFIRMATION,  # 9.1 Переходим к подтверждению
            'product_data': product_data
        })
        
        # Показываем подтверждение
        self._show_product_confirmation(message, product_data)

    # Новые вспомогательные методы для клавиатур

    def _create_yes_no_keyboard(self):
        """Клавиатура Да/Нет"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("✅ Да"))
        keyboard.add(types.KeyboardButton("❌ Нет"))
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard

    def _create_photo_selection_keyboard(self, photos: list):
        """Клавиатура для выбора фото"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        
        # Добавляем кнопки с номерами фото
        row = []
        for i in range(1, len(photos) + 1):
            row.append(types.KeyboardButton(f"{i}"))
            if len(row) == 3:  # 3 кнопки в строке
                keyboard.add(*row)
                row = []
        
        if row:  # Добавляем оставшиеся кнопки
            keyboard.add(*row)
        
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard

    def _create_availability_keyboard(self):
        """Клавиатура для выбора доступности"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("✅ Да"))
        keyboard.add(types.KeyboardButton("❌ Нет"))
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard

    def _create_photos_keyboard(self):
        """Клавиатура для работы с фото"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("✅ Готово"))
        keyboard.add(types.KeyboardButton("⏭️ Пропустить"))
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard

    def _create_photos_done_keyboard(self):
        """Клавиатура когда фото добавлены"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("✅ Готово"))
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard
    
    def _save_photo(self, photo_file_id: str, product_id: int = None) -> str:
        """Сохранение фото на диск и возвращение пути"""
        print(f'\n== _save_photo called with product_id: {product_id}\n')
        try:
            # Скачиваем фото
            file_info = self.bot.get_file(photo_file_id)
            print(f'File info: {file_info.file_path}')
            downloaded_file = self.bot.download_file(file_info.file_path)
            print(f'Downloaded file size: {len(downloaded_file)} bytes')
            
            # Создаем уникальное имя файла
            file_extension = os.path.splitext(file_info.file_path)[1] or '.jpg'
            
            filename = f"{uuid.uuid4().hex}{file_extension}"
            
            # Всегда сохраняем в папку товара (product_id обязателен)
            if not product_id:
                raise ValueError("product_id required for photo saving")
            
            product_dir = os.path.join(self.photos_dir, str(product_id))
            print(f'Product directory: {product_dir}')
            os.makedirs(product_dir, exist_ok=True)
            filepath = os.path.join(product_dir, filename)
            print(f'Full file path: {filepath}')
            
            # Сохраняем файл
            with open(filepath, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении фото: {e}")
            return None
    
    def _cleanup_temp_photos(self, temp_photos: list):
        """Очистка временных фото"""
        for photo_path in temp_photos:
            try:
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            except Exception as e:
                logger.error(f"Ошибка при удалении временного фото: {e}")


#### !!!!
    
    def _create_measurement_units_keyboard(self):
        """Создание клавиатуры с допустимыми единицами измерения"""
        valid_units = ['шт', 'кг', 'г', 'грамм', 'л', 'мл', 'уп', 'пачка', 'упаковка', 'набор', 'комплект']
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        
        for unit in valid_units:
            keyboard.add(types.KeyboardButton(unit))
        
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        
        return keyboard
    
    # def _get_default_measurement_unit(self) -> str:
    #     """Создание клавиатуры с допустимыми единицами измерения"""
    #     valid_units = self._get_valid_measurement_units()
        
    #     keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        
    #     for unit in valid_units:
    #         keyboard.add(types.KeyboardButton(unit))
        
    #     keyboard.add(types.KeyboardButton("❌ Отмена"))
        
    #     return keyboard
    
    def _show_product_confirmation(self, message: Message, product_data: dict):
        """Показ подтверждения перед сохранением"""
        confirmation_text = self._format_product_confirmation(product_data)
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("✅ Сохранить"))
        keyboard.add(types.KeyboardButton("✏️ Редактировать"))
        keyboard.add(types.KeyboardButton("❌ Отменить"))
        
        self.bot.send_message(
            message.chat.id,
            confirmation_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        self.states_manager.set_product_state(message.from_user.id, {
            'state': ProductState.CONFIRMATION,
            'product_data': product_data
        })
    
    def _format_product_confirmation(self, product_data: dict) -> str:
        """Форматирование текста подтверждения"""
        text = "🎂 <b>Подтверждение данных товара</b>\n\n"
        text += f"📝 <b>Название:</b> {product_data.get('name', 'Не указано')}\n"
        text += f"📁 <b>Категория ID:</b> {product_data.get('category_id', 'Не указана')}\n"
        text += f"📄 <b>Описание:</b> {product_data.get('short_description', 'Не указано')}\n"
        text += f"⚖️ <b>Количество:</b> {product_data.get('quantity', 0)}\n"
        text += f"💰 <b>Цена:</b> {product_data.get('price', 0)} руб.\n"
        text += f"💳 <b>Оплата:</b> {product_data.get('prepayment_conditions', 'Не указано')}\n"
        text += f"🔄 <b>Доступен:</b> {'Да' if product_data.get('is_available', True) else 'Нет'}\n"
        text += f"📏 <b>Единица измерения:</b> {product_data.get('measurement_unit', 'шт')}\n\n"
        text += "✅ <b>Сохранить товар?</b>"
        return text
    
    def _create_cancel_keyboard(self):
        """Клавиатура с кнопкой отмены"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard
    
    def _create_skip_keyboard(self):
        """Клавиатура с кнопкой пропуска"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("⏭️ Пропустить"))
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard
    
    def _create_categories_keyboard(self):
        """Создание клавиатуры с категориями"""
        categories = self.db_manager.get_all_categories()
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        
        for category in categories:
            keyboard.add(types.KeyboardButton(category['name']))
        
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        
        return keyboard
        
    def _handle_product_confirmation(self, message: Message):
        """Обработка подтверждения сохранения товара"""
        user_id = message.from_user.id
        
        if message.text == "✅ Сохранить":
            product_data = self.states_manager.get_product_data(user_id)
            
            # Сохраняем товар в базу данных (без фото)
            product_id = self.db_manager.add_product_returning_id(product_data)
            print(f'{product_id = }')
            
            if product_id:
                # Обновляем данные продукта с ID
                product_data['id'] = product_id
                self.states_manager.update_product_data(user_id, product_data)
                print(f'{product_data = }')
                
                # Переходим к вопросу о фото
                self.states_manager.set_product_state(user_id, {
                    'state': ProductState.ASKING_FOR_PHOTOS,
                    'product_data': product_data
                })
                
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                keyboard.add(types.KeyboardButton("✅ Да"))
                keyboard.add(types.KeyboardButton("❌ Нет"))
                
                self.bot.send_message(
                    message.chat.id,
                    f"✅ Товар <b>'{product_data['name']}'</b> успешно сохранен!\n\n"
                    "📸 Хотите добавить фотографии товара?",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Ошибка при сохранении товара. Попробуйте еще раз.",
                    reply_markup=self._create_confirmation_keyboard()
                )
        
        elif message.text == "✏️ Редактировать":
            # Возвращаемся к началу редактирования
            self.states_manager.set_product_state(user_id, {
                'state': ProductState.WAITING_NAME,
                'product_data': self.states_manager.get_product_data(user_id)
            })
            
            self.bot.send_message(
                message.chat.id,
                "📝 Введите <b>название</b> товара:",
                parse_mode='HTML',
                reply_markup=self._create_cancel_keyboard()
            )
        
        elif message.text == "❌ Отменить":
            self._cancel_product_creation_message(message)
        
        else:
            self.bot.send_message(
                message.chat.id,
                "Пожалуйста, выберите действие:",
                reply_markup=self._create_confirmation_keyboard()
            )

    def _save_product(self, product_data: dict) -> bool:
        """Сохранение товара в базу данных с обработкой фото"""
        try:
            # Сначала создаем товар в базе чтобы получить ID
            product_id = self.db_manager.add_product_returning_id(product_data)
            
            if not product_id:
                return False
            
            # Переносим фото из временной папки в папку товара
            if 'temp_photos' in product_data:
                for temp_photo_path in product_data['temp_photos']:
                    if os.path.exists(temp_photo_path):
                        # Создаем папку для товара
                        product_dir = os.path.join(self.photos_dir, str(product_id))
                        os.makedirs(product_dir, exist_ok=True)
                        
                        # Переносим файл
                        filename = os.path.basename(temp_photo_path)
                        new_path = os.path.join(product_dir, filename)
                        os.rename(temp_photo_path, new_path)
                        
                        # Обновляем пути в данных товара
                        if product_data.get('cover_photo_path') == temp_photo_path:
                            product_data['cover_photo_path'] = new_path
                        
                        if 'additional_photos' in product_data:
                            for i, photo_path in enumerate(product_data['additional_photos']):
                                if photo_path == temp_photo_path:
                                    product_data['additional_photos'][i] = new_path
                
                # Обновляем товар в базе с правильными путями к фото
                return self.db_manager.update_product(product_id, product_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении товара с фото: {e}")
            # Очищаем временные фото в случае ошибки
            if 'temp_photos' in product_data:
                self._cleanup_temp_photos(product_data['temp_photos'])
            return False
    
    def _create_confirmation_keyboard(self):
        """Клавиатура для подтверждения"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("✅ Сохранить"))
        keyboard.add(types.KeyboardButton("✏️ Редактировать"))
        keyboard.add(types.KeyboardButton("❌ Отменить"))
        return keyboard

    def _cancel_product_creation_message(self, message: Message):
        """Отмена создания товара из сообщения"""
        user_id = message.from_user.id
        self.states_manager.clear_product_state(user_id)
        
        self.bot.send_message(
            message.chat.id,
            "❌ Создание товара отменено.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Возвращаемся к управлению продукцией
        self.manage_products(message)

    
    def _add_category_start(self, callback: CallbackQuery):
        """Начало добавления категории"""
        if not self._check_admin_access(callback=callback):
            return
        
        # Сохраняем состояние для добавления категории
        self.states_manager.set_management_state(callback.from_user.id, {
            'state': 'adding_category_name',
            'category_data': {}
        })
        
        # Удаляем предыдущее сообщение
        try:
            self.bot.delete_message(callback.message.chat.id, callback.message.message_id)
        except:
            pass
        
        # Отправляем запрос на название категории
        self.bot.send_message(
            callback.message.chat.id,
            "📁 <b>Добавление новой категории</b>\n\n"
            "📝 Введите <b>название</b> категории:",
            parse_mode='HTML',
            reply_markup=self._create_cancel_keyboard()
        )
        self.bot.answer_callback_query(callback.id)
    
    def _handle_category_name(self, message: Message):
        """Обработка названия категории"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_management_state(user_id)
        
        if not user_state or user_state.get('state') != 'adding_category_name':
            return
        
        category_data = user_state.get('category_data', {})
        category_data['name'] = message.text
        
        # Обновляем состояние
        self.states_manager.set_management_state(user_id, {
            'state': 'adding_category_description',
            'category_data': category_data
        })
        
        self.bot.send_message(
            message.chat.id,
            "📄 Введите <b>описание</b> категории (или нажмите 'Пропустить'):",
            parse_mode='HTML',
            reply_markup=self._create_skip_keyboard()
        )
    
    def _handle_category_description(self, message: Message):
        """Обработка описания категории"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_management_state(user_id)
        
        if not user_state or user_state.get('state') != 'adding_category_description':
            return
        
        category_data = user_state.get('category_data', {})
        
        if message.text.lower() == '⏭️ пропустить':
            category_data['description'] = ''
        else:
            category_data['description'] = message.text
        
        # Сохраняем категорию в базу
        if self._save_category(category_data):
            self.states_manager.clear_management_state(user_id)
            
            self.bot.send_message(
                message.chat.id,
                f"✅ Категория <b>'{category_data['name']}'</b> успешно добавлена!",
                parse_mode='HTML',
                reply_markup=types.ReplyKeyboardRemove()
            )
            
            # Возвращаемся к управлению продукцией
            self.manage_products(message)
        else:
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка при сохранении категории. Попробуйте еще раз.",
                reply_markup=self._create_cancel_keyboard()
            )
    
    def _save_category(self, category_data: dict) -> bool:
        """Сохранение категории в базу данных"""
        try:
            # Используем существующий метод DatabaseManager или добавляем новый
            return self.db_manager.add_category(
                name=category_data['name'],
                description=category_data.get('description', '')
            )
        except Exception as e:
            logger.error(f"Ошибка при сохранении категории: {e}")
            return False
    
    def _cancel_category_creation(self, callback: CallbackQuery):
        """Отмена создания категории"""
        user_id = callback.from_user.id
        self.states_manager.clear_management_state(user_id)
        
        self.bot.send_message(
            callback.message.chat.id,
            "❌ Создание категории отменено.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        self.bot.answer_callback_query(callback.id, "❌ Создание отменено")
        
        # Возвращаемся к управлению продукцией
        self.manage_products(callback.message)
    
    # ===== НОВЫЕ МЕТОДЫ ДЛЯ РЕДАКТИРОВАНИЯ =====

    def _edit_products_start(self, callback: CallbackQuery):
        """1. Начало редактирования - выбор категории"""
        if not self._check_admin_access(callback=callback):
            return
        
        categories = self.db_manager.get_all_categories()
        
        if not categories:
            self.bot.send_message(
                callback.message.chat.id,
                "📭 Нет доступных категорий для редактирования.",
                reply_markup=self._create_back_to_products_keyboard()
            )
            return
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        for category in categories:
            keyboard.add(types.InlineKeyboardButton(
                f"📁 {category['name']}",
                callback_data=f"select_category_{category['id']}"
            ))
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад",
            callback_data="product_edit_back"
        ))
        
        try:
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="📂 <b>Редактирование товаров</b>\n\nВыберите категорию:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except:
            self.bot.send_message(
                callback.message.chat.id,
                "📂 <b>Редактирование товаров</b>\n\nВыберите категорию:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        
        self.bot.answer_callback_query(callback.id)

    def _handle_edit_callbacks(self, callback: CallbackQuery):
        """Обработка callback'ов редактирования"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            data = callback.data
            
            if data.startswith('select_category_'):
                # Выбор категории для редактирования
                category_id = int(data.replace('select_category_', ''))
                self._show_products_for_editing(callback, category_id)
                
            elif data.startswith('edit_product_'):
                # Выбор товара для редактирования
                product_id = int(data.replace('edit_product_', ''))
                self._show_edit_options(callback, product_id)
                
            elif data.startswith('edit_option_'):
                # Выбор опции редактирования
                parts = data.split('_')
                if len(parts) >= 4:
                    product_id = int(parts[2])
                    option = '_'.join(parts[3:])  # Берем все части после product_id
                    self._start_editing_option(callback, product_id, option)
                else:
                    self.bot.answer_callback_query(callback.id, "❌ Неверный формат callback")
                
            elif data == 'edit_back_to_categories':
                # Назад к категориям
                self._edit_products_start(callback)
                
            elif data == 'edit_back_to_products':
                # Назад к товарам категории
                user_state = self.states_manager.get_management_state(callback.from_user.id)
                if user_state and 'category_id' in user_state:
                    category_id = user_state.get('category_id')
                    self._show_products_for_editing(callback, category_id)
                else:
                    # Если состояние не найдено, возвращаемся к выбору категории
                    self._edit_products_start(callback)
                
            elif data == 'product_edit_back':
                # Назад в меню продукции
                self.manage_products(callback.message)

            elif data.startswith('edit_delete_option_'):
                # Переход к подтверждению удаления
                product_id = int(data.replace('edit_delete_option_', ''))
                print(f'Debug: Удаление продукта {product_id}')
                self._show_delete_confirmation(callback, product_id)
            
            elif data.startswith('edit_delete_confirm_'):
                # Подтверждение удаления товара
                product_id = int(data.replace('edit_delete_confirm_', ''))
                print(f"DEBUG: Delete confirmation received for product {product_id}")
                self._delete_product(callback, product_id)
                
            elif data.startswith('edit_back_to_options_'):
                # Возврат к опциям редактирования
                product_id = int(data.replace('edit_back_to_options_', ''))
                self._show_edit_options(callback, product_id)
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка в edit callback: {e}", exc_info=True)
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при обработке")

    def _show_products_for_editing(self, callback: CallbackQuery, category_id: int):
        """2. Показать товары категории для редактирования"""
        products = self.db_manager.get_products_by_category(category_id)
        
        if not products:
            self.bot.send_message(
                callback.message.chat.id,
                "📭 В этой категории нет товаров для редактирования.",
                reply_markup=self._create_edit_back_keyboard()
            )
            return
        
        # Сохраняем category_id в состоянии для возврата
        current_state = self.states_manager.get_management_state(callback.from_user.id) or {}
        current_state.update({
            'state': 'editing_category',
            'category_id': category_id
        })
        self.states_manager.set_management_state(callback.from_user.id, current_state)
        
        # Получаем информацию о категории
        categories = self.db_manager.get_all_categories()
        category_name = next((cat['name'] for cat in categories if cat['id'] == category_id), 'Неизвестно')
        
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        for product in products:
            status_emoji = "✅" if product['is_available'] else "❌"
            keyboard.add(types.InlineKeyboardButton(
                f"{status_emoji} #{product['id']} {product['name']} - {product['price']} руб.",
                callback_data=f"edit_product_{product['id']}"
            ))
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к категориям",
            callback_data="edit_back_to_categories"
        ))
        
        try:
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"📦 <b>Товары в категории:</b> {category_name}\n\nВыберите товар для редактирования:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except:
            self.bot.send_message(
                callback.message.chat.id,
                f"📦 <b>Товары в категории:</b> {category_name}\n\nВыберите товар для редактирования:",
                parse_mode='HTML',
                reply_markup=keyboard
            )

    def _show_edit_options(self, callback: CallbackQuery, product_id: int):
        """3. Показать опции редактирования для товара"""
        product = self.db_manager.get_product_by_id(product_id)
        
        if not product:
            self.bot.answer_callback_query(callback.id, "❌ Товар не найден")
            return
        
        # Сохраняем product_id в состоянии
        self.states_manager.set_management_state(callback.from_user.id, {
            'state': 'editing_product',
            'product_id': product_id
        })
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        # Основные опции
        keyboard.add(
            types.InlineKeyboardButton("✏️ Имя", callback_data=f"edit_option_{product_id}_name"),
            types.InlineKeyboardButton("📁 Категория", callback_data=f"edit_option_{product_id}_category")
        )
        keyboard.add(
            types.InlineKeyboardButton("📄 Описание", callback_data=f"edit_option_{product_id}_description"),
            types.InlineKeyboardButton("📏 Единица", callback_data=f"edit_option_{product_id}_unit")
        )
        keyboard.add(
            types.InlineKeyboardButton("⚖️ Количество", callback_data=f"edit_option_{product_id}_quantity"),
            types.InlineKeyboardButton("💰 Цена", callback_data=f"edit_option_{product_id}_price")
        )
        keyboard.add(
            types.InlineKeyboardButton("💳 Оплата", callback_data=f"edit_option_{product_id}_prepayment"),
            types.InlineKeyboardButton("🔄 Доступность", callback_data=f"edit_option_{product_id}_availability")
        )
        
        # Фото опции
        keyboard.add(
            types.InlineKeyboardButton("📸 Добавить фото", callback_data=f"edit_option_{product_id}_add_photo"),
            types.InlineKeyboardButton("🖼️ Выбрать основное", callback_data=f"edit_option_{product_id}_main_photo")
        )
        
        keyboard.add(
            types.InlineKeyboardButton("🗑️ Удалить товар", callback_data=f"edit_delete_option_{product_id}"),
            types.InlineKeyboardButton("🔙 Назад к товарам", callback_data="edit_back_to_products")
        )
        
        
        photos = self.db_manager.get_product_photos(product['id'])
        if photos:
            main_photos = [p for p in photos if p['is_main']]
            text_photos = f"📸 <b>Фотографии:</b> {len(photos)} шт.\n"
            # if main_photos:
            #     text_photos = f"📌 <b>Основное фото:</b> Установлено\n"
        else:
            text_photos = "📸 <b>Фотографии:</b> Нет\n"
        
        
        product_info = f"🎂 <b>Редактирование товара</b>\n\n"
        product_info += f"🆔 <b>ID:</b> {product['id']}\n"
        product_info += f"📝 <b>Название:</b> {product['name']}\n"
        product_info += f"📁 <b>Категория:</b> {product['category_name']}\n"
        product_info += text_photos
        product_info += f"📄 <b>Описание:</b> {product['short_description'] or 'Не указано'}\n"
        product_info += f"🔄 <b>Доступен:</b> {'✅ Да' if product['is_available'] else '❌ Нет'}\n"
        product_info += f"📏 <b>Единица измерения:</b> {product['measurement_unit']}\n"
        product_info += f"⚖️ <b>Количество:</b> {product['quantity']}\n"
        product_info += f"💰 <b>Цена:</b> {product['price']} руб.\n"
        product_info += f"💳 <b>Условия оплаты:</b> {product['prepayment_conditions'] or 'Не указано'}\n"
        product_info += "Выберите что хотите изменить:"
        
        try:
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=product_info,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except:
            self.bot.send_message(
                callback.message.chat.id,
                product_info,
                parse_mode='HTML',
                reply_markup=keyboard
            )

    def _show_edit_options_after_cancel(self, callback: CallbackQuery, product_id: int):
        """Вернуться к опциям редактирования после отмены удаления"""
        try:
            product = self.db_manager.get_product_by_id(product_id)
            
            if not product:
                self.bot.answer_callback_query(callback.id, "❌ Товар не найден")
                return
            
            # Показываем опции редактирования (аналогично _show_edit_options)
            self._show_edit_options(callback, product_id)
            
        except Exception as e:
            logger.error(f"Ошибка при возврате к опциям редактирования: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка")

    def _start_editing_option(self, callback: CallbackQuery, product_id: int, option: str):
        """Начать редактирование конкретной опции"""
        product = self.db_manager.get_product_by_id(product_id)
        
        if not product:
            self.bot.answer_callback_query(callback.id, "❌ Товар не найден")
            return
        
        # Сохраняем состояние редактирования
        self.states_manager.set_management_state(callback.from_user.id, {
            'state': f'editing_{option}',
            'product_id': product_id
        })
        
        messages = {
            'name': "✏️ Введите новое название товара:",
            'category': "📁 Выберите новую категорию:",
            'description': "📄 Введите новое описание товара:",
            'unit': "📏 Выберите новую единицу измерения:",
            'quantity': "⚖️ Введите новое количество товара:",
            'price': "💰 Введите новую цену товара:",
            'prepayment': "💳 Выберите новые условия оплаты:",
            'availability': "🔄 Товар доступен для заказа?",
            'add_photo': "📸 Отправьте новое фото товара:",
            'main_photo': "🖼️ Выберите основное фото:",
            'delete': "🗑️ Вы действительно хотите удалить товар?"
        }
        
        if option in ['category', 'unit', 'availability', 'prepayment']:
            # Для этих опций показываем клавиатуру
            if option == 'category':
                keyboard = self._create_categories_keyboard()
            elif option == 'unit':
                keyboard = self._create_measurement_units_keyboard()
            elif option == 'availability':
                keyboard = self._create_availability_keyboard()
            elif option == 'prepayment':
                keyboard = self._create_prepayment_keyboard()
            
            self.bot.send_message(
                callback.message.chat.id,
                messages[option],
                parse_mode='HTML',
                reply_markup=keyboard
            )
        elif option in ['add_photo', 'main_photo']:
            # Для работы с фото
            if option == 'main_photo':
                # Показываем список фото для выбора основного
                photos = self.db_manager.get_product_photos(product_id)
                if not photos:
                    self.bot.send_message(callback.message.chat.id, "❌ У товара нет фотографий")
                    self._return_to_edit_options(callback.message, product_id)
                    return
                
                photos_text = "\n".join([f"{i}. 📸 Фото {i}" for i in range(1, len(photos) + 1)])
                self.bot.send_message(
                    callback.message.chat.id,
                    f"📸 Выберите <b>главное фото</b>:\n\n{photos_text}",
                    parse_mode='HTML',
                    reply_markup=self._create_photo_selection_keyboard(photos)
                )
            else:
                # Для добавления фото
                self.bot.send_message(
                    callback.message.chat.id,
                    messages[option],
                    parse_mode='HTML',
                    reply_markup=self._create_cancel_edit_keyboard()
                )
        elif option == 'delete':
            # Показываем подтверждение удаления
            self._show_delete_confirmation(callback, product_id)
            return
        else:
            # Для текстовых опций
            self.bot.send_message(
                callback.message.chat.id,
                messages[option],
                parse_mode='HTML',
                reply_markup=self._create_cancel_edit_keyboard()
            )

    def _handle_edit_states(self, message: Message):
        """Обработка состояний редактирования"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_management_state(user_id)
        
        if not user_state:
            return
        
        state = user_state.get('state')
        product_id = user_state.get('product_id')
        
        if not product_id:
            self.bot.send_message(message.chat.id, "❌ Ошибка: товар не найден")
            return
        
        try:
            if state == 'editing_name':
                self._update_product_name(message, product_id)
                
            elif state == 'editing_description':
                self._update_product_description(message, product_id)
                
            elif state == 'editing_quantity':
                self._update_product_quantity(message, product_id)
                
            elif state == 'editing_price':
                self._update_product_price(message, product_id)
                
            elif state == 'editing_category':
                self._update_product_category(message, product_id)
                
            elif state == 'editing_unit':
                self._update_product_unit(message, product_id)
                
            elif state == 'editing_prepayment':
                self._update_product_prepayment(message, product_id)
                
            elif state == 'editing_availability':
                self._update_product_availability(message, product_id)
                
            elif state == 'editing_add_photo':
                self._add_product_photo(message, product_id)
                
            elif state == 'editing_main_photo':
                self._select_main_photo(message, product_id)
                
        except Exception as e:
            logger.error(f"Ошибка при редактировании: {e}")
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении товара")

    def _update_product_name(self, message: Message, product_id: int):
        """Обновление названия товара"""
        new_name = message.text
        logger.info(f"Попытка обновления названия товара {product_id} на: {new_name}")
        
        if self.db_manager.update_product_field(product_id, 'name', new_name):
            logger.info(f"Название товара {product_id} успешно обновлено")
            
            self.states_manager.clear_management_state(message.from_user.id)
            self.bot.send_message(message.chat.id, "✅ Название товара обновлено!")
            self._return_to_edit_options(message, product_id)
        else:
            logger.error(f"Ошибка при обновлении названия товара {product_id}")
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении названия")


    def _update_product_description(self, message: Message, product_id: int):
        """Обновление описания товара"""
        new_description = message.text
        if self.db_manager.update_product_field(product_id, 'short_description', new_description):
            self.states_manager.clear_management_state(message.from_user.id)
            self.bot.send_message(message.chat.id, "✅ Описание товара обновлено!")
            self._return_to_edit_options(message, product_id)
        else:
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении описания")

    def _update_product_quantity(self, message: Message, product_id: int):
        """Обновление количества товара"""
        try:
            new_quantity = float(message.text)
            if self.db_manager.update_product_field(product_id, 'quantity', new_quantity):
                self.states_manager.clear_management_state(message.from_user.id)
                self.bot.send_message(message.chat.id, "✅ Количество товара обновлено!")
                self._return_to_edit_options(message, product_id)
            else:
                self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении количества")
        except ValueError:
            self.bot.send_message(message.chat.id, "❌ Введите число для количества")

    def _update_product_price(self, message: Message, product_id: int):
        """Обновление цены товара"""
        try:
            new_price = float(message.text)
            if self.db_manager.update_product_field(product_id, 'price', new_price):
                self.states_manager.clear_management_state(message.from_user.id)
                self.bot.send_message(message.chat.id, "✅ Цена товара обновлена!")
                self._return_to_edit_options(message, product_id)
            else:
                self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении цены")
        except ValueError:
            self.bot.send_message(message.chat.id, "❌ Введите число для цены")

    def _update_product_category(self, message: Message, product_id: int):
        """Обновление категории товара"""
        categories = self.db_manager.get_all_categories()
        category_names = [cat['name'].lower() for cat in categories]
        
        if message.text.lower() not in category_names:
            self.bot.send_message(
                message.chat.id,
                "❌ Категория не найдена. Выберите из предложенных:",
                reply_markup=self._create_categories_keyboard()
            )
            return
        
        category_id = next((cat['id'] for cat in categories if cat['name'].lower() == message.text.lower()), None)
        
        if category_id and self.db_manager.update_product_field(product_id, 'category_id', category_id):
            self.states_manager.clear_management_state(message.from_user.id)
            self.bot.send_message(message.chat.id, "✅ Категория товара обновлена!")
            self._return_to_edit_options(message, product_id)
        else:
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении категории")

    def _update_product_unit(self, message: Message, product_id: int):
        """Обновление единицы измерения"""
        valid_units = ['шт', 'кг', 'г', 'грамм', 'л', 'мл', 'уп', 'пачка', 'упаковка', 'набор', 'комплект']
        
        if message.text not in valid_units:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, выберите единицу измерения из предложенных:",
                reply_markup=self._create_measurement_units_keyboard()
            )
            return
        
        if self.db_manager.update_product_field(product_id, 'measurement_unit', message.text):
            self.states_manager.clear_management_state(message.from_user.id)
            self.bot.send_message(message.chat.id, "✅ Единица измерения обновлена!")
            self._return_to_edit_options(message, product_id)
        else:
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении единицы измерения")

    def _update_product_prepayment(self, message: Message, product_id: int):
        """Обновление условий оплаты"""
        valid_options = ["50% предоплата", "100% предоплата", "Постоплата"]
        
        if message.text not in valid_options:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, выберите вариант из предложенных:",
                reply_markup=self._create_prepayment_keyboard()
            )
            return
        
        if self.db_manager.update_product_field(product_id, 'prepayment_conditions', message.text):
            self.states_manager.clear_management_state(message.from_user.id)
            self.bot.send_message(message.chat.id, "✅ Условия оплаты обновлены!")
            self._return_to_edit_options(message, product_id)
        else:
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении условий оплаты")

    def _update_product_availability(self, message: Message, product_id: int):
        """Обновление доступности товара"""
        if message.text == "✅ Да":
            new_availability = True
        elif message.text == "❌ Нет":
            new_availability = False
        else:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, выберите вариант:",
                reply_markup=self._create_availability_keyboard()
            )
            return
        
        if self.db_manager.update_product_field(product_id, 'is_available', new_availability):
            self.states_manager.clear_management_state(message.from_user.id)
            status = "доступен" if new_availability else "не доступен"
            self.bot.send_message(message.chat.id, f"✅ Товар теперь {status} для заказа!")
            self._return_to_edit_options(message, product_id)
        else:
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении доступности")

    def _add_product_photo(self, message: Message, product_id: int):
        """Добавление фото к товару"""
        if message.content_type != 'photo':
            self.bot.send_message(message.chat.id, "❌ Пожалуйста, отправьте фото")
            return
        
        try:
            photo_id = message.photo[-1].file_id
            photo_path = self._save_photo(photo_id, product_id)
            
            if photo_path and self.db_manager.add_product_photo(product_id, photo_path, is_main=False):
                self.bot.send_message(message.chat.id, "✅ Фото добавлено к товару!")
                self._return_to_edit_options(message, product_id)
            else:
                self.bot.send_message(message.chat.id, "❌ Ошибка при добавлении фото")
        except Exception as e:
            logger.error(f"Ошибка при добавлении фото: {e}")
            self.bot.send_message(message.chat.id, "❌ Ошибка при обработке фото")

    def _select_main_photo(self, message: Message, product_id: int):
        """Выбор основного фото"""
        photos = self.db_manager.get_product_photos(product_id)
        
        if not photos:
            self.bot.send_message(message.chat.id, "❌ У товара нет фотографий")
            self._return_to_edit_options(message, product_id)
            return
        
        try:
            photo_number = int(message.text)
            if 1 <= photo_number <= len(photos):
                selected_photo = photos[photo_number - 1]
                
                # Устанавливаем выбранное фото как основное
                if self.db_manager.set_main_photo(product_id, selected_photo['photo_path']):
                    self.bot.send_message(message.chat.id, "✅ Основное фото установлено!")
                    self._return_to_edit_options(message, product_id)
                else:
                    self.bot.send_message(message.chat.id, "❌ Ошибка при установке основного фото")
            else:
                self.bot.send_message(
                    message.chat.id,
                    f"❌ Неверный номер. Введите число от 1 до {len(photos)}:",
                    reply_markup=self._create_photo_selection_keyboard(photos)
                )
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, введите номер фото:",
                reply_markup=self._create_photo_selection_keyboard(photos)
            )

    def _return_to_edit_options(self, message: Message, product_id: int):
        """Вернуться к опциям редактирования после изменения"""
        # Очищаем состояние редактирования
        self.states_manager.clear_management_state(message.from_user.id)
        
        # Получаем информацию о товаре для показа опций
        product = self.db_manager.get_product_by_id(product_id)
        
        if not product:
            self.bot.send_message(message.chat.id, "❌ Товар не найден")
            self.manage_products(message)
            return
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        # Основные опции
        keyboard.add(
            types.InlineKeyboardButton("✏️ Имя", callback_data=f"edit_option_{product_id}_name"),
            types.InlineKeyboardButton("📁 Категория", callback_data=f"edit_option_{product_id}_category")
        )
        keyboard.add(
            types.InlineKeyboardButton("📄 Описание", callback_data=f"edit_option_{product_id}_description"),
            types.InlineKeyboardButton("📏 Единица", callback_data=f"edit_option_{product_id}_unit")
        )
        keyboard.add(
            types.InlineKeyboardButton("⚖️ Количество", callback_data=f"edit_option_{product_id}_quantity"),
            types.InlineKeyboardButton("💰 Цена", callback_data=f"edit_option_{product_id}_price")
        )
        keyboard.add(
            types.InlineKeyboardButton("💳 Оплата", callback_data=f"edit_option_{product_id}_prepayment"),
            types.InlineKeyboardButton("🔄 Доступность", callback_data=f"edit_option_{product_id}_availability")
        )
        
        # Фото опции
        keyboard.add(
            types.InlineKeyboardButton("📸 Добавить фото", callback_data=f"edit_option_{product_id}_add_photo"),
            types.InlineKeyboardButton("🖼️ Выбрать основное", callback_data=f"edit_option_{product_id}_main_photo")
        )
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к товарам",
            callback_data="edit_back_to_products"
        ))
        
        photos = self.db_manager.get_product_photos(product['id'])
        if photos:
            main_photos = [p for p in photos if p['is_main']]
            text_photos = f"📸 <b>Фотографии:</b> {len(photos)} шт.\n"
            # if main_photos:
            #     text_photos = f"📌 <b>Основное фото:</b> Установлено\n"
        else:
            text_photos = "📸 <b>Фотографии:</b> Нет\n"
        
        
        product_info = f"🎂 <b>Редактирование товара</b>\n\n"
        product_info += f"🆔 <b>ID:</b> {product['id']}\n"
        product_info += f"📝 <b>Название:</b> {product['name']}\n"
        product_info += f"📁 <b>Категория:</b> {product['category_name']}\n"
        product_info += text_photos
        product_info += f"📄 <b>Описание:</b> {product['short_description'] or 'Не указано'}\n"
        product_info += f"🔄 <b>Доступен:</b> {'✅ Да' if product['is_available'] else '❌ Нет'}\n"
        product_info += f"📏 <b>Единица измерения:</b> {product['measurement_unit']}\n"
        product_info += f"⚖️ <b>Количество:</b> {product['quantity']}\n"
        product_info += f"💰 <b>Цена:</b> {product['price']} руб.\n"
        product_info += f"💳 <b>Условия оплаты:</b> {product['prepayment_conditions'] or 'Не указано'}\n"
        product_info += "Выберите что хотите изменить:"
        
        self.bot.send_message(
            message.chat.id,
            product_info,
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def _create_prepayment_keyboard(self):
        """Клавиатура для выбора оплаты"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("50% предоплата"))
        keyboard.add(types.KeyboardButton("100% предоплата"))
        keyboard.add(types.KeyboardButton("Постоплата"))
        keyboard.add(types.KeyboardButton("❌ Отмена редактирования"))
        return keyboard

    def _create_cancel_edit_keyboard(self):
        """Клавиатура для отмены редактирования"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("❌ Отмена редактирования"))
        return keyboard

    def _create_edit_back_keyboard(self):
        """Клавиатура для возврата при редактировании"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад",
            callback_data="edit_back_to_categories"
        ))
        return keyboard
    
    def _show_delete_confirmation(self, callback: CallbackQuery, product_id: int):
        """Показать подтверждение удаления товара"""
        product = self.db_manager.get_product_by_id(product_id)
        print(f' == Подтверждение удаления продукта ==')
        
        if not product:
            self.bot.answer_callback_query(callback.id, "❌ Товар не найден")
            return
        
        # Форматируем информацию о товаре
        product_text = self._format_product_details(product)
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("✅ Да, удалить", callback_data=f"edit_delete_confirm_{product_id}"),
            types.InlineKeyboardButton("❌ Нет, отменить", callback_data=f"edit_back_to_options_{product_id}")
        )
        
        try:
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"🗑️ <b>Подтверждение удаления товара</b>\n\n{product_text}\n\n"
                    "Вы действительно хотите удалить этот товар?",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except:
            self.bot.send_message(
                callback.message.chat.id,
                f"🗑️ <b>Подтверждение удаления товара</b>\n\n{product_text}\n\n"
                "Вы действительно хотите удалить этот товар?",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        
    def _delete_product(self, callback: CallbackQuery, product_id: int):
        """Удаление товара"""
        print(f"DEBUG: Starting deletion of product {product_id}")
        try:
            # Получаем информацию о товаре перед удалением
            product = self.db_manager.get_product_by_id(product_id)
            
            if not product:
                print(f"DEBUG: Product {product_id} not found")
                self.bot.answer_callback_query(callback.id, "❌ Товар не найден")
                return
            
            print(f"DEBUG: Product found: {product['name']}")
            
            # 1. Удаляем фотографии товара с диска
            photos = self.db_manager.get_product_photos(product_id)
            print(f"DEBUG: Found {len(photos)} photos to delete")
            for photo in photos:
                try:
                    if os.path.exists(photo['photo_path']):
                        os.remove(photo['photo_path'])
                        print(f"DEBUG: Deleted photo: {photo['photo_path']}")
                except Exception as e:
                    logger.error(f"Ошибка при удалении фото: {e}")
            
            # 2. Удаляем папку товара
            product_dir = os.path.join(self.photos_dir, str(product_id))
            try:
                if os.path.exists(product_dir):
                    import shutil
                    shutil.rmtree(product_dir)
                    print(f"DEBUG: Deleted product directory: {product_dir}")
            except Exception as e:
                logger.error(f"Ошибка при удалении папки товара: {e}")
            
            # 3. Удаляем товар из базы данных
            if self.db_manager.delete_product(product_id):
                print(f"DEBUG: Product {product_id} deleted from database")
                
                # Удаляем сообщение с подтверждением
                try:
                    self.bot.delete_message(callback.message.chat.id, callback.message.message_id)
                except:
                    pass
                    
                # Отправляем подтверждение удаления
                self.bot.send_message(
                    callback.message.chat.id,
                    f"✅ Товар '{product['name']}' успешно удален!"
                )
                
                # Возвращаемся к списку товаров категории
                user_state = self.states_manager.get_management_state(callback.from_user.id)
                if user_state and 'category_id' in user_state:
                    category_id = user_state.get('category_id')
                    self._show_products_for_editing(callback, category_id)
                else:
                    self._edit_products_start(callback)
            else:
                print(f"DEBUG: Failed to delete product {product_id} from database")
                self.bot.answer_callback_query(callback.id, "❌ Ошибка при удалении из базы данных")
                        
        except Exception as e:
            logger.error(f"Ошибка при удалении товара: {e}")
            import traceback
            traceback.print_exc()
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при удалении")                   

    # ===== КОНЕЦ НОВЫХ МЕТОДОВ ДЛЯ РЕДАКТИРОВАНИЯ =====

    # ===== методы для просмотра =====
    
    def _view_products(self, message: Message):
        """Просмотр товаров - выбор категории"""
        if not self._check_admin_access(message=message):
            return
        
        categories = self.db_manager.get_all_categories()
        
        if not categories:
            self.bot.send_message(
                message.chat.id,
                "📭 Нет доступных категорий.",
                reply_markup=self._create_back_to_products_keyboard()
            )
            return
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        for category in categories:
            keyboard.add(types.InlineKeyboardButton(
                f"📁 {category['name']}",
                callback_data=f"view_category_{category['id']}"
            ))
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад",
            callback_data="view_back_products"
        ))
        
        self.bot.send_message(
            message.chat.id,
            "📂 <b>Просмотр товаров</b>\n\nВыберите категорию:",
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def _handle_view_category(self, callback: CallbackQuery):
        """Обработка выбора категории для просмотра"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            category_id = int(callback.data.replace('view_category_', ''))
            products = self.db_manager.get_products_by_category(category_id)
            
            if not products:
                self.bot.send_message(
                    callback.message.chat.id,
                    "📭 В этой категории нет товаров.",
                    reply_markup=self._create_back_to_categories_keyboard()
                )
                return
            
            # Получаем информацию о категории
            categories = self.db_manager.get_all_categories()
            category_name = next((cat['name'] for cat in categories if cat['id'] == category_id), 'Неизвестно')
            
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            
            for product in products:
                status_emoji = "✅" if product['is_available'] else "❌"
                keyboard.add(types.InlineKeyboardButton(
                    f"{status_emoji} {product['name']} - {product['price']} руб.",
                    callback_data=f"view_product_{product['id']}"
                ))
            
            keyboard.add(types.InlineKeyboardButton(
                "🔙 Назад к категориям",
                callback_data="view_back_categories"
            ))
            
            # Редактируем сообщение вместо отправки нового
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"📂 <b>Товары в категории:</b> {category_name}\n\nВыберите товар:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при просмотре категории: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при загрузке")

    def _handle_view_product(self, callback: CallbackQuery):
        """Обработка просмотра конкретного товара"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            product_id = int(callback.data.replace('view_product_', ''))
            product = self.db_manager.get_product_by_id(product_id)
            
            if not product:
                self.bot.answer_callback_query(callback.id, "❌ Товар не найден")
                return
            
            # Форматируем информацию о товаре
            product_text = self._format_product_details(product)
            
            # Получаем фотографии товара
            photos = self.db_manager.get_product_photos(product_id)
            main_photo_path = product['cover_photo_path']
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(
                "🔙 Назад к товарам",
                callback_data=f"view_back_to_category_{product['category_id']}"
            ))
            keyboard.add(types.InlineKeyboardButton(
                "🔙 В меню",
                callback_data="view_back_products"
            ))
            
            # Если есть основное фото, отправляем его с описанием
            if main_photo_path and os.path.exists(main_photo_path):
                try:
                    with open(main_photo_path, 'rb') as photo:
                        self.bot.send_photo(
                            chat_id=callback.message.chat.id,
                            photo=photo,
                            caption=product_text,
                            parse_mode='HTML',
                            reply_markup=keyboard
                        )
                except Exception as e:
                    logger.error(f"Ошибка отправки фото: {e}")
                    self.bot.send_message(
                        callback.message.chat.id,
                        product_text,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
            else:
                # Если фото нет, отправляем просто текст
                self.bot.send_message(
                    callback.message.chat.id,
                    product_text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            
            # Отправляем дополнительные фото, если они есть
            if len(photos) > 1:
                additional_photos = [p for p in photos if p['photo_path'] != main_photo_path]
                if additional_photos:
                    media_group = []
                    for i, photo_info in enumerate(additional_photos[:9]):  # Максимум 10 фото в группе
                        if os.path.exists(photo_info['photo_path']):
                            with open(photo_info['photo_path'], 'rb') as photo:
                                media_group.append(types.InputMediaPhoto(photo))
                    
                    if media_group:
                        try:
                            self.bot.send_media_group(
                                callback.message.chat.id,
                                media_group
                            )
                        except Exception as e:
                            logger.error(f"Ошибка отправки медиагруппы: {e}")
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при просмотре товара: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при загрузке")

    def _handle_view_back(self, callback: CallbackQuery):
        """Обработка кнопки назад при просмотре"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            data = callback.data
            
            if data == 'view_back_products':
                # Возврат в меню управления продукцией
                self.manage_products(callback.message)
                
            elif data == 'view_back_categories':
                # Возврат к списку категорий
                self._view_products(callback.message)
                
            elif data.startswith('view_back_to_category_'):
                # Возврат к товарам конкретной категории
                category_id = int(data.replace('view_back_to_category_', ''))
                self._show_products_in_category(callback.message, category_id)
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке назад: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка")

    def _show_products_in_category(self, message: Message, category_id: int):
        """Показать товары в категории"""
        products = self.db_manager.get_products_by_category(category_id)
        categories = self.db_manager.get_all_categories()
        category_name = next((cat['name'] for cat in categories if cat['id'] == category_id), 'Неизвестно')
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        for product in products:
            status_emoji = "✅" if product['is_available'] else "❌"
            keyboard.add(types.InlineKeyboardButton(
                f"{status_emoji} {product['name']} - {product['price']} руб.",
                callback_data=f"view_product_{product['id']}"
            ))
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к категориям",
            callback_data="view_back_categories"
        ))
        
        self.bot.send_message(
            message.chat.id,
            f"📂 <b>Товары в категории:</b> {category_name}\n\nВыберите товар:",
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def _format_product_details(self, product: dict) -> str:
        """Форматирование детальной информации о товаре"""
        text = "🎂 <b>Информация о товаре</b>\n\n"
        text += f"🆔 <b>ID:</b> {product['id']}\n"
        text += f"📝 <b>Название:</b> {product['name']}\n"
        text += f"📁 <b>Категория:</b> {product['category_name']}\n"
        text += f"📄 <b>Описание:</b> {product['short_description'] or 'Не указано'}\n"
        text += f"🔄 <b>Доступен:</b> {'✅ Да' if product['is_available'] else '❌ Нет'}\n"
        text += f"📏 <b>Единица измерения:</b> {product['measurement_unit']}\n"
        text += f"⚖️ <b>Количество:</b> {product['quantity']}\n"
        text += f"💰 <b>Цена:</b> {product['price']} руб.\n"
        text += f"💳 <b>Условия оплаты:</b> {product['prepayment_conditions'] or 'Не указано'}\n"
        text += f"📅 <b>Создан:</b> {product['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
        text += f"🔄 <b>Обновлен:</b> {product['updated_at'].strftime('%d.%m.%Y %H:%M') if product['updated_at'] else 'Не обновлялся'}\n"
        
        # Информация о фотографиях
        photos = self.db_manager.get_product_photos(product['id'])
        if photos:
            main_photos = [p for p in photos if p['is_main']]
            text += f"\n📸 <b>Фотографии:</b> {len(photos)} шт.\n"
            if main_photos:
                text += f"📌 <b>Основное фото:</b> Установлено\n"
        else:
            text += "\n📸 <b>Фотографии:</b> Нет\n"
        
        return text

    # ===== КОНЕЦ МЕТОДОВ ДЛЯ просмотра =====
    
    def _create_back_to_products_keyboard(self):
        """Клавиатура для возврата к управлению продукцией"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "🔙 В меню продукции",
            callback_data="view_back_products"
        ))
        return keyboard

    def _create_back_to_categories_keyboard(self):
        """Клавиатура для возврата к категориям"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "🔙 К категориям",
            callback_data="view_back_categories"
        ))
        return keyboard
    
    def _delete_products(self, message: Message):
        """Удаление товаров"""
        self.bot.send_message(message.chat.id, "🚫 Функция удаления товаров в разработке")
    
    def _cancel_product_creation(self, callback: CallbackQuery):
        """Отмена создания товара"""
        user_id = callback.from_user.id
        self.states_manager.clear_product_state(user_id)
        
        self.bot.send_message(
            callback.message.chat.id,
            "❌ Создание товара отменено.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        self.bot.answer_callback_query(callback.id, "❌ Создание отменено")