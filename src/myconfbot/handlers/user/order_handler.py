# src/myconfbot/handlers/user/order_handler.py

import logging
import os
from datetime import datetime, timedelta
from telebot import types
from telebot.types import Message, CallbackQuery

from src.myconfbot.handlers.user.base_user_handler import BaseUserHandler
from src.myconfbot.handlers.user.order_constants import OrderConstants
from src.myconfbot.handlers.user.order_states import OrderStatesManager
from src.myconfbot.handlers.user.order_product_viewer import OrderProductViewer

logger = logging.getLogger(__name__)

class OrderHandler(BaseUserHandler):
    """Обработчик заказов"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
        self.order_states = OrderStatesManager(self.states_manager)
        self.photos_dir = OrderConstants.PHOTOS_DIR
        self.product_viewer = OrderProductViewer(bot, db_manager, self.photos_dir)
    
    def register_handlers(self):
        """Регистрация обработчиков заказов"""
        self._register_order_callbacks()
        self._register_order_message_handlers()
    
    def _register_order_callbacks(self):
        """Регистрация callback обработчиков"""
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_category_'))
        def handle_order_category(callback: CallbackQuery):
            self._handle_category_selection(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_product_'))
        def handle_order_product(callback: CallbackQuery):
            self._handle_product_selection(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_favorite_'))
        def handle_order_favorite(callback: CallbackQuery):
            self._handle_add_to_favorite(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_start_'))
        def handle_order_start(callback: CallbackQuery):
            self._handle_order_start(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_step_'))
        def handle_order_step(callback: CallbackQuery):
            self._handle_order_step(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_confirm_'))
        def handle_order_confirm(callback: CallbackQuery):
            self._handle_order_confirm(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_cancel_'))
        def handle_order_cancel(callback: CallbackQuery):
            self._handle_order_cancel(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == 'order_back_categories')
        def handle_back_to_categories(callback: CallbackQuery):
            self._handle_back_to_categories(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_back_to_category_'))
        def handle_back_to_category(callback: CallbackQuery):
            self._handle_back_to_category(callback)
    
    def _register_order_message_handlers(self):
        """Регистрация обработчиков сообщений для шагов заказа"""
        
        @self.bot.message_handler(
            func=lambda message: self.order_states.is_in_order_process(message.from_user.id)
        )
        def handle_order_message(message: Message):
            self._handle_order_message(message)
    
    def start_order_process(self, message: Message):
        """Начало процесса заказа - показ категорий"""
        categories = self.db_manager.get_all_categories()
        
        if not categories:
            self.bot.send_message(
                message.chat.id,
                "📭 Нет доступных категорий.",
                reply_markup=self._create_back_to_main_keyboard()
            )
            return
        
        keyboard = OrderConstants.create_categories_keyboard(
            categories=categories,
            back_callback="main_menu"
        )
        
        self.bot.send_message(
            message.chat.id,
            "📂 <b>Выберите категорию:</b>",
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def _send_products_media_group(self, chat_id, products):
        """Отправка медиагруппы с товарами"""
        media_group = []
        file_objects = []
        
        try:
            for product in products:
                # Проверяем наличие основного фото
                cover_photo_path = product.get('cover_photo_path')
                if cover_photo_path and os.path.exists(cover_photo_path):
                    # Формируем подпись
                    short_desc = product['short_description'] or ''
                    if len(short_desc) > 25:
                        short_desc = short_desc[:25] + "..."
                    
                    caption = f"🎂 {product['name']}\n{short_desc}"
                    
                    # Открываем файл
                    file_obj = open(cover_photo_path, 'rb')
                    file_objects.append(file_obj)
                    
                    # Добавляем в медиагруппу
                    media_group.append(types.InputMediaPhoto(
                        file_obj,
                        caption=caption,
                        parse_mode='HTML'
                    ))
            
            # Отправляем медиагруппу если есть фото
            if media_group:
                self.bot.send_media_group(chat_id, media_group)
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка отправки медиагруппы товаров: {e}")
            return False
        finally:
            # Закрываем все файлы
            for file_obj in file_objects:
                try:
                    file_obj.close()
                except:
                    pass
    
    def _handle_category_selection(self, callback: CallbackQuery):
        """Обработка выбора категории с отправкой фото товаров"""
        try:
            category_id = int(callback.data.replace('order_category_', ''))
            products = self.db_manager.get_products_by_category(category_id)
            
            if not products:
                self.bot.answer_callback_query(callback.id, "📭 В этой категории нет товаров")
                return
            
            # Получаем информацию о категории
            categories = self.db_manager.get_all_categories()
            category_name = next((cat['name'] for cat in categories if cat['id'] == category_id), 'Неизвестно')
            
            # Сначала отправляем заголовок категории
            self.bot.send_message(
                callback.message.chat.id,
                f"📂 <b>Товары в категории:</b> {category_name}",
                parse_mode='HTML'
            )
            
            # Затем для каждого товара отправляем фото + кнопку выбора
            for product in products:
                self._send_product_with_button(callback.message.chat.id, product)
            
            # В конце отправляем кнопку "Назад"
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(
                "🔙 Назад к категориям",
                callback_data="order_back_categories"
            ))
            
            self.bot.send_message(
                callback.message.chat.id,
                "⬆️ <b>Выберите товар из списка выше:</b>",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при выборе категории: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при выборе категории")

    def _send_product_with_button(self, chat_id, product):
        """Отправка товара с фото и кнопкой выбора"""
        try:
            # Формируем подпись
            short_desc = product['short_description'] or ''
            if len(short_desc) > 60:
                short_desc = short_desc[:60] + "..."
            
            caption = f"🎂 <b>{product['name']}</b>\n{short_desc}\n💰 Цена: {product['price']} руб."
            
            # Создаем кнопку для выбора товара
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(
                "🔍 Подробнее...",
                callback_data=f"order_product_{product['id']}"
            ))
            
            # Проверяем наличие фото
            cover_photo_path = product.get('cover_photo_path')
            if cover_photo_path and os.path.exists(cover_photo_path):
                # Отправляем фото с кнопкой
                with open(cover_photo_path, 'rb') as photo:
                    self.bot.send_photo(
                        chat_id,
                        photo,
                        caption=caption,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
            else:
                # Если фото нет, отправляем только текст с кнопкой
                self.bot.send_message(
                    chat_id,
                    caption,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Ошибка отправки товара {product['id']}: {e}")
    
    # def _handle_category_selection(self, callback: CallbackQuery):
    #     """Обработка выбора категории"""
    #     try:
    #         category_id = int(callback.data.replace('order_category_', ''))
    #         products = self.db_manager.get_products_by_category(category_id)
            
    #         if not products:
    #             self.bot.answer_callback_query(callback.id, "📭 В этой категории нет товаров")
    #             return
            
    #         # Получаем информацию о категории
    #         categories = self.db_manager.get_all_categories()
    #         category_name = next((cat['name'] for cat in categories if cat['id'] == category_id), 'Неизвестно')
            
    #         keyboard = OrderConstants.create_products_keyboard(
    #             products=products,
    #             back_callback="order_back_categories"
    #         )
            
    #         self.bot.edit_message_text(
    #             chat_id=callback.message.chat.id,
    #             message_id=callback.message.message_id,
    #             text=f"📂 <b>Товары в категории:</b> {category_name}\n\nВыберите товар:",
    #             parse_mode='HTML',
    #             reply_markup=keyboard
    #         )
            
    #         self.bot.answer_callback_query(callback.id)
            
    #     except Exception as e:
    #         logger.error(f"Ошибка при выборе категории: {e}")
    #         self.bot.answer_callback_query(callback.id, "❌ Ошибка при выборе категории")
    
    def _handle_product_selection(self, callback: CallbackQuery):
        """Обработка выбора товара"""
        try:
            product_id = int(callback.data.replace('order_product_', ''))
            
            # Показываем детальную информацию о товаре
            self.product_viewer.show_product_summary(callback.message, product_id)
            
            # Добавляем кнопки действий
            keyboard = OrderConstants.create_product_actions_keyboard(
                product_id=product_id,
                back_callback=f"order_back_to_category_{self._get_product_category_id(product_id)}"
            )
            
            # Отправляем кнопки действий отдельным сообщением
            self.bot.send_message(
                callback.message.chat.id,
                "⬇️ Выберите действие:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при выборе товара: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при выборе товара")
    
    def _handle_add_to_favorite(self, callback: CallbackQuery):
        """Добавление товара в избранное"""
        try:
            product_id = int(callback.data.replace('order_favorite_', ''))
            
            # TODO: Реализовать добавление в избранное
            self.bot.answer_callback_query(
                callback.id, 
                "⭐ Товар добавлен в избранное"
            )
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении в избранное: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка")
    
    def _handle_order_start(self, callback: CallbackQuery):
        """Начало оформления заказа"""
        try:
            product_id = int(callback.data.replace('order_start_', ''))
            user_id = callback.from_user.id
            
            # Начинаем процесс заказа
            self.order_states.start_order(user_id, product_id)
            
            # Переходим к первому шагу - количество
            self._ask_quantity(callback.message, product_id)
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при начале заказа: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при начале заказа")
    
    def _ask_quantity(self, message: Message, product_id: int):
        """Запрос количества товара"""
        product = self.db_manager.get_product_by_id(product_id)
        
        if not product:
            self.bot.send_message(message.chat.id, "❌ Товар не найден")
            return
        
        keyboard = OrderConstants.create_back_keyboard("order_cancel_quantity")
        
        question = f"🎂 <b>{product['name']}</b>\n\n"
        question += f"💰 Цена: {product['price']} руб. за {product['measurement_unit']}\n"
        question += f"📦 Доступно: {product['quantity']} {product['measurement_unit']}\n\n"
        question += "➡️ <b>Введите количество:</b>"
        
        self.bot.send_message(
            message.chat.id,
            question,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    def _handle_order_step(self, callback: CallbackQuery):
        """Обработка шагов заказа через callback"""
        # Можно использовать для быстрого выбора дат и т.д.
        pass
    
    def _handle_order_message(self, message: Message):
        """Обработка сообщений в процессе заказа"""
        user_id = message.from_user.id
        order_data = self.order_states.get_order_data(user_id)
        
        if not order_data:
            return
        
        current_state = order_data.get('state')
        
        if current_state == 'order_quantity':
            self._process_quantity_input(message, order_data)
        elif current_state == 'order_date':
            self._process_date_input(message, order_data)
        elif current_state == 'order_delivery':
            self._process_delivery_input(message, order_data)
        elif current_state == 'order_payment':
            self._process_payment_input(message, order_data)
        elif current_state == 'order_notes':
            self._process_notes_input(message, order_data)
    
    def _process_quantity_input(self, message: Message, order_data: dict):
        """Обработка ввода количества"""
        try:
            quantity = float(message.text)
            product_id = order_data['product_id']
            product = self.db_manager.get_product_by_id(product_id)
            
            if not product:
                self.bot.send_message(message.chat.id, "❌ Товар не найден")
                self.order_states.cancel_order(message.from_user.id)
                return
            
            # Проверяем доступное количество
            if quantity <= 0:
                self.bot.send_message(message.chat.id, "❌ Введите положительное число")
                return
            
            if quantity > product['quantity']:
                self.bot.send_message(
                    message.chat.id,
                    f"❌ Недостаточно товара. Доступно: {product['quantity']}"
                )
                return
            
            # Сохраняем количество
            self.order_states.update_order_data(
                message.from_user.id,
                quantity=quantity,
                state='order_date'
            )
            
            # Переходим к следующему шагу - дата
            self._ask_date(message, product_id)
            
        except ValueError:
            self.bot.send_message(message.chat.id, "❌ Введите число")
    
    def _ask_date(self, message: Message, product_id: int):
        """Запрос даты приготовления"""
        # Минимальная дата - завтра
        min_date = datetime.now() + timedelta(days=1)
        
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        
        # Предлагаем ближайшие даты
        for i in range(1, 4):
            date = min_date + timedelta(days=i)
            keyboard.add(types.InlineKeyboardButton(
                date.strftime("%d.%m"),
                callback_data=f"order_date_{date.strftime('%Y-%m-%d')}"
            ))
        
        keyboard.add(types.InlineKeyboardButton(
            "📅 Другая дата",
            callback_data="order_custom_date"
        ))
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад",
            callback_data="order_back_quantity"
        ))
        
        self.bot.send_message(
            message.chat.id,
            "📅 <b>Выберите дату приготовления:</b>\n\n"
            "Минимальный срок - завтра.",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    def _process_date_input(self, message: Message, order_data: dict):
        """Обработка ввода даты"""
        # Реализация для ручного ввода даты
        pass
    
    def _ask_delivery(self, message: Message):
        """Запрос способа доставки"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            types.InlineKeyboardButton("🚗 Доставка", callback_data="order_delivery_home"),
            types.InlineKeyboardButton("🏃 Самовывоз", callback_data="order_delivery_pickup")
        )
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад",
            callback_data="order_back_date"
        ))
        
        self.bot.send_message(
            message.chat.id,
            "🚚 <b>Выберите способ получения:</b>",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    def _ask_payment(self, message: Message):
        """Запрос способа оплаты"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            types.InlineKeyboardButton("💳 Онлайн", callback_data="order_payment_online"),
            types.InlineKeyboardButton("💵 При получении", callback_data="order_payment_cash")
        )
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад", 
            callback_data="order_back_delivery"
        ))
        
        self.bot.send_message(
            message.chat.id,
            "💳 <b>Выберите способ оплаты:</b>",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    def _ask_notes(self, message: Message):
        """Запрос примечаний"""
        keyboard = OrderConstants.create_back_keyboard("order_back_payment")
        
        self.bot.send_message(
            message.chat.id,
            "📝 <b>Добавьте примечания к заказу:</b>\n\n"
            "Например: особые пожелания, аллергии и т.д.\n"
            "Или отправьте '-' если примечаний нет.",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    def _show_order_summary(self, message: Message, order_data: dict):
        """Показать сводку заказа"""
        product = self.db_manager.get_product_by_id(order_data['product_id'])
        
        if not product:
            self.bot.send_message(message.chat.id, "❌ Товар не найден")
            return
        
        total_cost = float(product['price']) * order_data['quantity']
        
        summary = "📋 <b>Сводка заказа</b>\n\n"
        summary += f"🎂 <b>Товар:</b> {product['name']}\n"
        summary += f"📦 <b>Количество:</b> {order_data['quantity']} {product['measurement_unit']}\n"
        summary += f"💰 <b>Цена за единицу:</b> {product['price']} руб.\n"
        summary += f"💵 <b>Общая стоимость:</b> {total_cost:.2f} руб.\n"
        summary += f"📅 <b>Дата приготовления:</b> {order_data.get('ready_date', 'Не указана')}\n"
        summary += f"🚚 <b>Доставка:</b> {order_data.get('delivery_type', 'Не указана')}\n"
        summary += f"💳 <b>Оплата:</b> {order_data.get('payment_type', 'Не указана')}\n"
        summary += f"📝 <b>Примечания:</b> {order_data.get('notes', 'Нет')}\n"
        
        keyboard = OrderConstants.create_order_confirmation_keyboard("temp_id")
        
        self.bot.send_message(
            message.chat.id,
            summary,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    def _handle_order_confirm(self, callback: CallbackQuery):
        """Подтверждение заказа"""
        try:
            user_id = callback.from_user.id
            order_data = self.order_states.complete_order(user_id)
            
            if not order_data:
                self.bot.answer_callback_query(callback.id, "❌ Данные заказа не найдены")
                return
            
            # Создаем заказ в базе данных
            order_success = self._create_order_in_db(user_id, order_data)
            
            if order_success:
                self.bot.answer_callback_query(callback.id, "✅ Заказ создан!")
                
                # Показываем подтверждение
                self.bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text="✅ <b>Заказ успешно создан!</b>\n\n"
                         "Мы свяжемся с вами для уточнения деталей.",
                    parse_mode='HTML'
                )
                
                # TODO: Уведомление администраторов
                
            else:
                self.bot.answer_callback_query(callback.id, "❌ Ошибка при создании заказа")
                
        except Exception as e:
            logger.error(f"Ошибка при подтверждении заказа: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при создании заказа")
    
    def _handle_order_cancel(self, callback: CallbackQuery):
        """Отмена заказа"""
        user_id = callback.from_user.id
        self.order_states.cancel_order(user_id)
        
        self.bot.answer_callback_query(callback.id, "❌ Заказ отменен")
        
        self.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ <b>Заказ отменен</b>",
            parse_mode='HTML'
        )

    def _handle_back_to_categories(self, callback: CallbackQuery):
        """Обработка возврата к списку категорий"""
        try:
            # Просто заново запускаем процесс заказа, который покажет категории
            self.start_order_process(callback.message)
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при возврате к категориям: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка")

    def _handle_back_to_category(self, callback: CallbackQuery):
        """Обработка возврата к товарам категории"""
        try:
            category_id = int(callback.data.replace('order_back_to_category_', ''))
            products = self.db_manager.get_products_by_category(category_id)
            
            if not products:
                self.bot.answer_callback_query(callback.id, "📭 В этой категории нет товаров")
                return
            
            # Получаем информацию о категории
            categories = self.db_manager.get_all_categories()
            category_name = next((cat['name'] for cat in categories if cat['id'] == category_id), 'Неизвестно')
            
            # Сначала отправляем заголовок категории
            self.bot.send_message(
                callback.message.chat.id,
                f"📂 <b>Товары в категории:</b> {category_name}",
                parse_mode='HTML'
            )
            
            # Затем для каждого товара отправляем фото + кнопку выбора
            for product in products:
                self._send_product_with_button(callback.message.chat.id, product)
            
            # В конце отправляем кнопку "Назад"
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(
                "🔙 Назад к категориям",
                callback_data="order_back_categories"
            ))
            
            self.bot.send_message(
                callback.message.chat.id,
                "⬆️ <b>Выберите товар из списка выше:</b>",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при возврате к категории: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка")
    
    def _create_order_in_db(self, user_id: int, order_data: dict) -> bool:
        """Создание заказа в базе данных"""
        try:
            product = self.db_manager.get_product_by_id(order_data['product_id'])
            
            if not product:
                return False
            
            total_cost = float(product['price']) * order_data['quantity']
            
            order_db_data = {
                'user_id': user_id,
                'product_id': order_data['product_id'],
                'quantity': order_data['quantity'],
                'total_cost': total_cost,
                'delivery_type': order_data.get('delivery_type', 'Не указано'),
                'payment_type': order_data.get('payment_type', 'Не указано'),
                'admin_notes': order_data.get('notes', ''),
                'ready_at': order_data.get('ready_date')
            }
            
            # Используем существующий метод создания заказа
            order = self.db_manager.create_order(order_db_data)
            return order is not None
            
        except Exception as e:
            logger.error(f"Ошибка при создании заказа в БД: {e}")
            return False
    
    def _get_product_category_id(self, product_id: int) -> int:
        """Получить ID категории товара"""
        product = self.db_manager.get_product_by_id(product_id)
        return product['category_id'] if product else 0
    
    def _create_back_to_main_keyboard(self):
        """Клавиатура для возврата в главное меню"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Главное меню",
            callback_data="main_menu"
        ))
        return keyboard