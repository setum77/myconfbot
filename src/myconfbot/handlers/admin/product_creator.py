# product_creator.py
import logging
import os
import uuid
from telebot import types
from telebot.types import Message, CallbackQuery
from .product_constants import ProductConstants
from .product_states import ProductState
from .photo_manager import PhotoManager

logger = logging.getLogger(__name__)

class ProductCreator:

    """Класс для создания товаров"""
    
    def __init__(self, bot, db_manager, states_manager, photos_dir, photo_manager=None):
        self.bot = bot
        self.db_manager = db_manager
        self.states_manager = states_manager
        self.photos_dir = photos_dir
        self.photo_manager = photo_manager

    def start_creation(self, callback: CallbackQuery):
        """Начало создания товара"""
        self.states_manager.set_product_state(callback.from_user.id, {
            'state': ProductState.WAITING_BASIC_INFO,
            'product_data': {'additional_photos': []}
        })
        
        try:
            self.bot.delete_message(callback.message.chat.id, callback.message.message_id)
        except:
            pass
        
        self.bot.send_message(
            callback.message.chat.id,
            ProductConstants.ADD_PRODUCT_START,
            parse_mode='HTML',
            reply_markup=ProductConstants.create_cancel_keyboard()
        )

    def handle_basic_info(self, message: Message):
        """Обработка основной информации"""
        # Обработка отмены
        if self._check_cancellation(message):
            return
        
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        if self.states_manager.get_product_state(user_id) == ProductState.WAITING_BASIC_INFO:
            if 'name' not in product_data:
                # Шаг 1: Название
                product_data['name'] = message.text
                self._update_product_state(user_id, product_data, ProductState.WAITING_BASIC_INFO)
                self._ask_category(message)
                
            elif 'category_id' not in product_data:
                # Шаг 2: Категория
                self._handle_category_input(message, product_data, user_id)
                
            elif 'is_available' not in product_data:
                # Шаг 3: Доступность
                self._handle_availability_input(message, product_data, user_id)

    def handle_details(self, message: Message):
        """Обработка детальной информации"""
        # Проверка отмены
        if self._check_cancellation(message):
            return

        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        
        if 'short_description' not in product_data:
            self._handle_description_input(message, product_data, user_id)
        elif 'measurement_unit' not in product_data:
            self._handle_unit_input(message, product_data, user_id)
        elif 'quantity' not in product_data:
            self._handle_quantity_input(message, product_data, user_id)
        elif 'price' not in product_data:
            self._handle_price_input(message, product_data, user_id)
        elif 'prepayment_conditions' not in product_data:
            self._handle_prepayment_input(message, product_data, user_id)
    
    def _check_cancellation(self, message: Message) -> bool:
        """Проверка нажатия кнопки отмены"""
        if message.text == "❌ Отмена":
            self._cancel_creation(message)
            return True
        return False

    def _cancel_creation(self, message: Message):
        """Отмена создания товара"""
        user_id = message.from_user.id
        self.states_manager.clear_product_state(user_id)
        
        self.bot.send_message(
            message.chat.id,
            "❌ Создание товара отменено.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Здесь можно добавить возврат в главное меню или другую логику
        # Например, отправить основное меню:
        self._back_to_product_management(message.chat.id)

    def _ask_category(self, message: Message):
        """Запрос категории"""
        keyboard = self._create_categories_keyboard()
        self.bot.send_message(
            message.chat.id,
            "📁 Выберите <b>категорию</b> товара:",
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def _handle_category_input(self, message: Message, product_data: dict, user_id: int):
        """Обработка ввода категории"""
        # Проверка отмены
        if self._check_cancellation(message):
            return
        
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
        product_data['category_id'] = category_id
        self._update_product_state(user_id, product_data, ProductState.WAITING_BASIC_INFO)
        
        self.bot.send_message(
            message.chat.id,
            "🔄 <b>Товар доступен для заказа?</b>",
            parse_mode='HTML',
            reply_markup=ProductConstants.create_availability_keyboard()
        )

    def _handle_availability_input(self, message: Message, product_data: dict, user_id: int):
        """Обработка доступности"""
        # Проверка отмены
        if self._check_cancellation(message):
            return

        if message.text == "✅ Да":
            product_data['is_available'] = True
        elif message.text == "❌ Нет":
            product_data['is_available'] = False
        else:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, выберите вариант:",
                reply_markup=ProductConstants.create_availability_keyboard()
            )
            return
        
        self._update_product_state(user_id, product_data, ProductState.WAITING_DETAILS)
        
        self.bot.send_message(
            message.chat.id,
            "📝 Введите <b>краткое описание</b> товара (или нажмите 'Пропустить'):",
            parse_mode='HTML',
            reply_markup=ProductConstants.create_skip_keyboard()
        )

    def _handle_description_input(self, message: Message, product_data: dict, user_id: int):
        """Обработка описания"""
        # Проверка отмены
        if self._check_cancellation(message):
            return
        
        if message.text.lower() == '⏭️ пропустить':
            product_data['short_description'] = ''
        else:
            product_data['short_description'] = message.text
        
        self._update_product_state(user_id, product_data, ProductState.WAITING_DETAILS)
        
        self.bot.send_message(
            message.chat.id,
            "📏 Выберите <b>единицу измерения</b> для товара:",
            parse_mode='HTML',
            reply_markup=ProductConstants.create_measurement_units_keyboard()
        )

    def _handle_unit_input(self, message: Message, product_data: dict, user_id: int):
        """Обработка единицы измерения"""
        # Проверка отмены
        if self._check_cancellation(message):
            return
        
        if message.text not in ProductConstants.MEASUREMENT_UNITS:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, выберите единицу измерения из предложенных:",
                reply_markup=ProductConstants.create_measurement_units_keyboard()
            )
            return
        
        product_data['measurement_unit'] = message.text
        self._update_product_state(user_id, product_data, ProductState.WAITING_DETAILS)
        
        self.bot.send_message(
            message.chat.id,
            "⚖️ Введите <b>количество</b> товара:",
            parse_mode='HTML',
            reply_markup=ProductConstants.create_cancel_keyboard()
        )

    def _handle_quantity_input(self, message: Message, product_data: dict, user_id: int):
        """Обработка количества"""
        # Проверка отмены
        if self._check_cancellation(message):
            return
        
        try:
            quantity = float(message.text)
            product_data['quantity'] = quantity
            self._update_product_state(user_id, product_data, ProductState.WAITING_DETAILS)
            
            self.bot.send_message(
                message.chat.id,
                "💰 Введите <b>цену</b> товара:",
                parse_mode='HTML',
                reply_markup=ProductConstants.create_cancel_keyboard()
            )
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, введите число:",
                reply_markup=ProductConstants.create_cancel_keyboard()
            )

    def _handle_price_input(self, message: Message, product_data: dict, user_id: int):
        """Обработка цены"""
        # Проверка отмены
        if self._check_cancellation(message):
            return
        
        try:
            price = float(message.text)
            product_data['price'] = price
            self._update_product_state(user_id, product_data, ProductState.WAITING_DETAILS)
            
            self.bot.send_message(
                message.chat.id,
                "💳 Выберите <b>условия оплаты</b>:",
                parse_mode='HTML',
                reply_markup=ProductConstants.create_prepayment_keyboard()
            )
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, введите число:",
                reply_markup=ProductConstants.create_cancel_keyboard()
            )

    def _handle_prepayment_input(self, message: Message, product_data: dict, user_id: int):
        """Обработка условий оплаты"""
        # Проверка отмены
        if self._check_cancellation(message):
            return
        
        if message.text not in ProductConstants.PREPAYMENT_OPTIONS:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, выберите вариант из предложенных:",
                reply_markup=ProductConstants.create_prepayment_keyboard()
            )
            return
        
        product_data['prepayment_conditions'] = message.text
        self._update_product_state(user_id, product_data, ProductState.CONFIRMATION)
        
        self._show_confirmation(message, product_data)

    def _show_confirmation(self, message: Message, product_data: dict):
        """Показать подтверждение"""
        confirmation_text = self._format_confirmation(product_data)
        
        self.bot.send_message(
            message.chat.id,
            confirmation_text,
            parse_mode='HTML',
            reply_markup=ProductConstants.create_confirmation_keyboard()
        )

    def _format_confirmation(self, product_data: dict) -> str:
        """Форматирование текста подтверждения"""
        text = "🎂 <b>Подтверждение данных товара</b>\n\n"
        text += f"📝 <b>Название:</b> {product_data.get('name', 'Не указано')}\n"
        text += f"📁 <b>Категория ID:</b> {product_data.get('category_id', 'Не указана')}\n"
        text += f"📄 <b>Описание:</b> {product_data.get('short_description', 'Не указано')}\n"
        text += f"🔄 <b>Доступен:</b> {'Да' if product_data.get('is_available', True) else 'Нет'}\n"
        #text += f"📏 <b>Единица измерения:</b> {product_data.get('measurement_unit', 'шт')}\n"
        text += f"⚖️ <b>Количество:</b> {product_data('quantity')} {product_data('measurement_unit')}\n"
        text += f"💰 <b>Цена:</b> {product_data.get('price', 0)} руб.\n"
        text += f"💳 <b>Оплата:</b> {product_data.get('prepayment_conditions', 'Не указано')}\n"
        text += "✅ <b>Сохранить товар?</b>"
        return text

    def _update_product_state(self, user_id: int, product_data: dict, state: ProductState):
        """Обновление состояния продукта"""
        self.states_manager.update_product_data(user_id, product_data)
        self.states_manager.set_product_state(user_id, {
            'state': state,
            'product_data': product_data
        })

    def _create_categories_keyboard(self):
        """Создание клавиатуры с категориями"""
        categories = self.db_manager.get_all_categories()
        category_names = [category['name'] for category in categories]
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        category_buttons = [types.KeyboardButton(name) for name in category_names]
        for i in range(0, len(category_buttons), 2):
            row_buttons = category_buttons[i:i+2]
            keyboard.add(*row_buttons)
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard
    
    # product_creator.py - добавим в конец класса
    def _handle_confirmation(self, message: Message):
        """Обработка подтверждения сохранения товара"""
        # Проверка отмены
        if self._check_cancellation(message):
            return
        
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
    def _back_to_product_management(self, chat_id: int):
        """Возврат в меню управления продукцией"""
        self.bot.send_message(
            chat_id,
            "🏪 <b>Управление продукцией</b>\n\nВыберите действие:",
            reply_markup=ProductConstants.create_management_keyboard(),
            parse_mode='HTML'
        )
