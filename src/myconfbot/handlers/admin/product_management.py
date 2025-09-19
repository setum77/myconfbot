import logging
import os
import uuid
from datetime import datetime
from telebot import types
from telebot.types import Message, CallbackQuery

from .admin_base import BaseAdminHandler
from .product_states import ProductState

logger = logging.getLogger(__name__)

class ProductManagementHandler(BaseAdminHandler):
    """Обработчик управления продукцией"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
        self.logger = logging.getLogger(__name__)
        self.photos_dir = "data/products"
        os.makedirs(self.photos_dir, exist_ok=True)
    
    def register_handlers(self):
        """Регистрация обработчиков управления продукцией"""
        self._register_product_callbacks()
        self._register_product_states()
        self._register_category_states()

    
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
    
    def _register_product_states(self):
        """Регистрация обработчиков состояний товаров"""
        # 12.1 Дополнительные фото
        @self.bot.message_handler(
            content_types=['photo'],
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.WAITING_ADDITIONAL_PHOTOS
        )
        def handle_additional_photos(message: Message):
            self._handle_additional_photos(message)
        
        # 11.1 Основное фото
        @self.bot.message_handler(
            content_types=['photo'],
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.WAITING_MAIN_PHOTO
        )
        def handle_main_photo(message: Message):
            self._handle_main_photo(message)

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

        # 10.1 Спросить про фото
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.ASKING_FOR_PHOTOS
        )
        def handle_asking_for_photos(message: Message):
            self._handle_asking_for_photos(message)
        
        # Обработчик кнопки "Готово" для дополнительных фото
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_product_state(message.from_user.id) == ProductState.WAITING_ADDITIONAL_PHOTOS and
                message.text == "✅ Готово"
            )
        )
        def handle_photos_done(message: Message):
            self._handle_photos_done(message)
    
        # 13.1 Выбор главного фото
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.SELECTING_MAIN_PHOTO
        )
        def handle_selecting_main_photo(message: Message):
            self._handle_selecting_main_photo(message)
        
        # Обработчик отмены
        @self.bot.message_handler(
            func=lambda message: (
                self.states_manager.get_product_state(message.from_user.id) is not None and
                message.text == "❌ Отмена"
            )
        )
        def handle_product_cancel(message: Message):
            self._cancel_product_creation_message(message)

   
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
                self._edit_products(callback.message)
            elif data == 'product_view':
                self._view_products(callback.message)
            elif data == 'product_delete':
                self._delete_products(callback.message)
            elif data == 'product_cancel':
                self._cancel_product_creation(callback)
            elif data == 'category_cancel': 
                self._cancel_category_creation(callback)
            elif data == 'product_confirm':
                self._confirm_product_creation(callback)
                
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            self.logger.error(f"Ошибка в product callback: {e}", exc_info=True)
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
        """Начало добавления товара"""
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
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        if message.text == "✅ Да":
            # Переходим к добавлению основного фото
            self.states_manager.set_product_state(user_id, {
                'state': ProductState.WAITING_MAIN_PHOTO,
                'product_data': product_data
            })
            
            self.bot.send_message(
                message.chat.id,
                "📸 Отправьте <b>основное фото</b> товара:",
                parse_mode='HTML',
                reply_markup=self._create_cancel_keyboard()
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
            
            # Возвращаемся к управлению продукцией
            self.manage_products(message)
        
        else:
            self.bot.send_message(
                message.chat.id,
                "Пожалуйста, выберите вариант:",
                reply_markup=self._create_yes_no_keyboard()
            )
    
    
    def _handle_main_photo(self, message: Message):
        """Обработка основного фото"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        try:
            # Сохраняем основное фото
            photo_id = message.photo[-1].file_id
            photo_path = self._save_photo(photo_id, product_data['id'])  # Сохраняем сразу в папку товара
            
            if photo_path:
                # Сохраняем фото в базу
                self.db_manager.add_product_photo(product_data['id'], photo_path, is_main=True)
                
                # Обновляем данные
                product_data['cover_photo_path'] = photo_path
                self.db_manager.update_product_cover_photo(product_data['id'], photo_path)
                self.states_manager.update_product_data(user_id, product_data)
                
                # Переходим к дополнительным фото
                self.states_manager.set_product_state(user_id, {
                    'state': ProductState.WAITING_ADDITIONAL_PHOTOS,
                    'product_data': product_data
                })
                
                self.bot.send_message(
                    message.chat.id,
                    "✅ Основное фото сохранено!\n\n"
                    "📸 Теперь можете отправить <b>дополнительные фото</b> "
                    "или нажмите '✅ Готово' чтобы завершить:",
                    parse_mode='HTML',
                    reply_markup=self._create_photos_done_keyboard()
                )
    
        except Exception as e:
            self.logger.error(f"Ошибка при обработке основного фото: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка при сохранении фото. Попробуйте еще раз.",
                reply_markup=self._create_cancel_keyboard()
            )
    
    
    def _handle_additional_photos(self, message: Message):
        """Обработка дополнительных фотографий"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        try:
            # Сохраняем фото
            photo_id = message.photo[-1].file_id
            photo_path = self._save_photo(photo_id, product_data['id'])  # Сохраняем сразу в папку товара
            
            if photo_path:
                # Сохраняем фото в базу (пока не как основное)
                self.db_manager.add_product_photo(product_data['id'], photo_path, is_main=False)
                
                # Получаем обновленный список фото
                photos = self.db_manager.get_product_photos(product_data['id'])
                
                self.bot.send_message(
                    message.chat.id,
                    f"✅ Фото добавлено! Всего фото: {len(photos)}\n"
                    "Можете отправить еще фото или нажмите '✅ Готово' чтобы завершить",
                    reply_markup=self._create_photos_done_keyboard()
                )
        
        except Exception as e:
            self.logger.error(f"Ошибка при обработке дополнительного фото: {e}")
                
        except Exception as e:
            print(f"ERROR: Ошибка при обработке фото: {e}")
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
                    reply_markup=self._create_cancel_keyboard()
                )
        
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, введите номер фото:",
                reply_markup=self._create_cancel_keyboard()
            )
    
    def _handle_photos_done(self, message: Message):
        """Обработка завершения добавления фото"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        photos = self.db_manager.get_product_photos(product_data['id'])
        
        if len(photos) <= 1:
            # Если только одно фото (основное), просто завершаем
            self.states_manager.clear_product_state(user_id)
            self.bot.send_message(
                message.chat.id,
                f"✅ Товар <b>'{product_data['name']}'</b> успешно добавлен!",
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
                f"📸 У вас несколько фотографий. Выберите <b>главное фото</b>:\n\n{photos_text}",
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
        self.logger.info(f"Выбрана единица измерения: {message.text}")
        self.logger.info(f"Допустимые единицы: {valid_units}")
        
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
        self.logger.info(f"Сохраненная единица измерения: {product_data['measurement_unit']}")

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
            'state': ProductState.CONFIRMATION,  # Переходим к подтверждению
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
        
        for i, photo in enumerate(photos, 1):
            keyboard.add(types.KeyboardButton(f"{i}"))
        
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
        try:
            # Скачиваем фото
            file_info = self.bot.get_file(photo_file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            # Создаем уникальное имя файла
            file_extension = os.path.splitext(file_info.file_path)[1] or '.jpg'
            filename = f"{uuid.uuid4().hex}{file_extension}"
            
            # Всегда сохраняем в папку товара (product_id обязателен)
            if not product_id:
                raise ValueError("product_id required for photo saving")
            
            product_dir = os.path.join(self.photos_dir, str(product_id))
            os.makedirs(product_dir, exist_ok=True)
            filepath = os.path.join(product_dir, filename)
            
            # Сохраняем файл
            with open(filepath, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении фото: {e}")
            return None
    
    def _cleanup_temp_photos(self, temp_photos: list):
        """Очистка временных фото"""
        for photo_path in temp_photos:
            try:
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            except Exception as e:
                self.logger.error(f"Ошибка при удалении временного фото: {e}")


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

        # Отладочная информация
        # print(f"Обработка подтверждения для пользователя {user_id}")
        # print(f"Текст сообщения: {message.text}")
        # print(f"Текущее состояние: {self.states_manager.get_product_state(user_id)}")
        
        if message.text == "✅ Сохранить":
            product_data = self.states_manager.get_product_data(user_id)
            
            # Сохраняем товар в базу данных (без фото)
            product_id = self.db_manager.add_product_returning_id(product_data)
            
            if product_id:
                # Обновляем данные продукта с ID
                product_data['id'] = product_id
                self.states_manager.update_product_data(user_id, product_data)
                
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
            self.logger.error(f"Ошибка при сохранении товара с фото: {e}")
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
            self.logger.error(f"Ошибка при сохранении категории: {e}")
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
    
    def _edit_products(self, message: Message):
        """Редактирование товаров"""
        self.bot.send_message(message.chat.id, "✏️ Функция редактирования товаров в разработке")
    
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
            self.logger.error(f"Ошибка при просмотре категории: {e}")
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
                    self.logger.error(f"Ошибка отправки фото: {e}")
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
                            self.logger.error(f"Ошибка отправки медиагруппы: {e}")
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            self.logger.error(f"Ошибка при просмотре товара: {e}")
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
            self.logger.error(f"Ошибка при обработке назад: {e}")
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