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
from src.myconfbot.handlers.user.order_processor import OrderProcessor

logger = logging.getLogger(__name__)

class OrderHandler(BaseUserHandler):
    """Обработчик заказов"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
        self.order_states = OrderStatesManager(self.states_manager, bot)
        self.photos_dir = OrderConstants.PHOTOS_DIR
        self.product_viewer = OrderProductViewer(bot, db_manager, self.photos_dir)
        self.order_processor = OrderProcessor(bot, db_manager, self.order_states)

        # Временный обработчик для отладки
        self._register_debug_handlers()

    def _register_debug_handlers(self):
        """Временные обработчики для отладки"""
        @self.bot.message_handler(
            func=lambda message: (
                not message.from_user.is_bot and
                self.order_states.is_in_order_process(message.from_user.id) and
                message.content_type == 'text'
            )
        )
        def handle_order_message(message: Message):
            logger.info(f"🔍 Обработка сообщения в процессе заказа: '{message.text}'")
            self._handle_order_message(message)

    
    def register_handlers(self):
        """Регистрация обработчиков заказов"""
        self._register_order_callbacks()
        self._register_order_message_handlers()
    
    def _register_order_callbacks(self):
        """Регистрация callback обработчиков"""
        @self.bot.callback_query_handler(func=lambda call: call.data == 'order_back_quantity')
        def handle_back_to_quantity(callback: CallbackQuery):
            self._handle_back_to_quantity(callback)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_date_'))
        def handle_order_date(callback: CallbackQuery):
            self.order_processor.handle_date_selection(callback)

        @self.bot.callback_query_handler(func=lambda call: call.data == 'order_custom_date')
        def handle_custom_date(callback: CallbackQuery):
            self.order_processor.handle_custom_date(callback)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_time_'))
        def handle_order_time(callback: CallbackQuery):
            self.order_processor.handle_time_selection(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == 'order_custom_time')
        def handle_custom_time(callback: CallbackQuery):
            self.order_processor.handle_custom_time(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == 'order_back_time')
        def handle_back_to_time(callback: CallbackQuery):
            self._handle_back_to_time(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == 'order_back_date')
        def handle_back_to_date(callback: CallbackQuery):
            self._handle_back_to_date(callback)

        @self.bot.callback_query_handler(func=lambda call: call.data == 'order_back_delivery')
        def handle_back_to_delivery(callback: CallbackQuery):
            self._handle_back_to_delivery(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == 'order_delivery_continue')
        def handle_delivery_continue(callback: CallbackQuery):
            self.order_processor.process_delivery_continue(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == 'order_payment_continue')
        def handle_payment_continue(callback: CallbackQuery):
            self.order_processor.process_payment_continue(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_confirm_'))
        def handle_order_confirm(callback: CallbackQuery):
            self.order_processor.complete_order(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_cancel_'))
        def handle_order_cancel(callback: CallbackQuery):
            self.order_processor.cancel_order(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == 'order_back_categories')
        def handle_back_to_categories(callback: CallbackQuery):
            self._handle_back_to_categories(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_back_to_category_'))
        def handle_back_to_category(callback: CallbackQuery):
            self._handle_back_to_category(callback)

        @self.bot.callback_query_handler(func=lambda call: call.data == 'order_back_payment')
        def handle_back_to_payment(callback: CallbackQuery):
            self._handle_back_to_payment(callback)

        @self.bot.callback_query_handler(func=lambda call: call.data == 'order_cancel_quantity')
        def handle_cancel_quantity(callback: CallbackQuery):
            self._handle_cancel_quantity(callback)




        # ОБЩИЕ ОБРАБОТЧИКИ
        
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
            self.order_processor.start_order_process(callback)
        
        # вроде не нужен после проверки удалить если что
        # @self.bot.callback_query_handler(func=lambda call: call.data.startswith('order_step_'))
        # def handle_order_step(callback: CallbackQuery):
        #     self._handle_order_step(callback)
      
        
    
    def _register_order_message_handlers(self):
        """Регистрация обработчиков сообщений для шагов заказа"""
        # ВРЕМЕННО: Более простой обработчик для диагностики
        @self.bot.message_handler(func=lambda message: True)  # ВРЕМЕННО ВСЕ СООБЩЕНИЯ
        def debug_all_messages(message: Message):
            user_id = message.from_user.id
            
            # Проверяем состояние
            in_order_process = self.order_states.is_in_order_process(user_id)
            order_data = self.order_states.get_order_data(user_id)
            
            logger.info(f"🔍 ALL MESSAGES DEBUG: user_id={user_id}, text='{message.text}'")
            logger.info(f"🔍 In order process: {in_order_process}")
            logger.info(f"🔍 Order data: {order_data}")
            
            # Если в процессе заказа - обрабатываем
            if in_order_process and order_data:
                logger.info(f"🎯 ПЕРЕДАЕМ В ОБРАБОТЧИК ЗАКАЗА!")
                self._handle_order_message(message)
            else:
                logger.info(f"🔍 Не в процессе заказа, пропускаем")

        
        # В order_handler.py добавьте временный обработчик:

        @self.bot.message_handler(func=lambda message: message.text.isdigit())
        def force_quantity_handler(message: Message):
            """Временный обработчик для цифровых сообщений"""
            user_id = message.from_user.id
            order_data = self.order_states.get_order_data(user_id)
            
            logger.info(f"🔍 FORCE HANDLER: user_id={user_id}, text='{message.text}'")
            logger.info(f"🔍 Order data: {order_data}")
            
            if order_data and order_data.get('state') == 'order_quantity':
                logger.info(f"🎯 ВЫЗЫВАЕМ process_quantity_input ЧЕРЕЗ FORCE HANDLER!")
                self.order_processor.process_quantity_input(message, order_data)
            else:
                logger.info(f"🔍 Не подходящее состояние для форсированной обработки")
        
        
        # @self.bot.message_handler(
        #     func=lambda message: (
        #         not message.from_user.is_bot and
        #         self.order_states.is_in_order_process(message.from_user.id) and
        #         message.content_type == 'text'  # ТОЛЬКО ТЕКСТОВЫЕ СООБЩЕНИЯ
        #     )
        # )
        # def handle_order_message(message: Message):
        #     logger.info(f"🔍 Обработка сообщения в процессе заказа: '{message.text}'")
        #     logger.info(f"🔍 User ID: {message.from_user.id}, Chat ID: {message.chat.id}")
            
        #     # Проверяем состояние еще раз
        #     user_id = message.from_user.id
        #     order_data = self.order_states.get_order_data(user_id)
        #     if order_data:
        #         logger.info(f"🔍 Состояние заказа перед обработкой: {order_data.get('state')}")
        #     else:
        #         logger.warning(f"⚠️ Нет данных заказа для пользователя {user_id}")
        #         return
        #     self._handle_order_message(message)


    def _handle_order_message(self, message: Message):
        """Обработка сообщений в процессе заказа"""
        user_id = message.from_user.id
        order_data = self.order_states.get_order_data(user_id)
        
        if not order_data:
            logger.warning(f"⚠️ Нет данных заказа для пользователя {user_id}")
            return
        
        current_state = order_data.get('state')
        logger.info(f"🔍 Текущее состояние заказа: {current_state}")
        logger.info(f"🔍 Текст сообщения: '{message.text}'")
        
        if current_state == 'order_quantity':
            logger.info("🔍 Обработка ввода количества/веса")
            self.order_processor.process_quantity_input(message, order_data)
            
        elif current_state == 'order_date_custom':
            logger.info("🔍 Обработка ручного ввода даты")
            self.order_processor.process_custom_date_input(message, order_data)

        elif current_state == 'order_time_custom':  # НОВОЕ: обработка ручного ввода времени
            logger.info("🔍 Обработка ручного ввода времени")
            self.order_processor.process_custom_time_input(message, order_data)

        elif current_state == 'order_notes':
            logger.info("🔍 Обработка ввода примечаний")
            self.order_processor.process_notes_input(message, order_data)

        else:
            logger.warning(f"⚠️ Неизвестное состояние: {current_state}")
            # Если состояние неизвестно, отменяем заказ
            self.bot.send_message(
                message.chat.id,
                "❌ Произошла ошибка в процессе заказа. Пожалуйста, начните заново."
            )
            self.order_states.cancel_order(user_id)
    
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

    def _handle_back_to_date(self, callback: CallbackQuery):
        """Обработка возврата к выбору даты"""
        try:
            user_id = callback.from_user.id
            order_data = self.order_states.get_order_data(user_id)
            
            if order_data:
                # Удаляем сохраненное время при возврате
                self.order_states.update_order_data(
                    user_id,
                    ready_time=None,
                    state='order_date'
                )
                # Запрашиваем дату заново
                self.order_processor._ask_date(callback.message, order_data['product_id'])
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при возврате к дате: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка")

    def _handle_back_to_time(self, callback: CallbackQuery):
        """Возврат к выбору времени"""
        try:
            user_id = callback.from_user.id
            order_data = self.order_states.get_order_data(user_id)
            
            if order_data:
                self.order_states.set_order_step(user_id, 'order_time')
                self.order_processor._ask_time(callback.message)
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при возврате ко времени: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка")


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


    def _handle_back_to_quantity(self, callback: CallbackQuery):
        """Возврат к вводу количества"""
        try:
            user_id = callback.from_user.id
            order_data = self.order_states.get_order_data(user_id)
            
            if order_data:
                # Возвращаемся к шагу количества
                self.order_states.update_order_data(
                    user_id,
                    state='order_quantity'
                )
                # Запрашиваем количество заново
                self.order_processor._ask_quantity(callback.message, order_data['product_id'])
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при возврате к количеству: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка")

    def _handle_back_to_delivery(self, callback: CallbackQuery):
        """Возврат к информации о доставке"""
        try:
            user_id = callback.from_user.id
            order_data = self.order_states.get_order_data(user_id)
            
            if order_data:
                # Возвращаемся к шагу доставки
                self.order_states.update_order_data(
                    user_id,
                    state='order_delivery_info'
                )
                # Показываем информацию о доставке заново
                self.order_processor._ask_delivery(callback.message)
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при возврате к доставке: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка")

    def _handle_back_to_payment(self, callback: CallbackQuery):
        """Возврат к информации об оплате"""
        try:
            user_id = callback.from_user.id
            order_data = self.order_states.get_order_data(user_id)
            
            if order_data:
                # Возвращаемся к шагу оплаты
                self.order_states.update_order_data(
                    user_id,
                    state='order_payment'
                )
                # Показываем информацию об оплате заново
                self.order_processor._ask_payment(callback.message, order_data['product_id'])
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при возврате к оплате: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка")

    def _handle_cancel_quantity(self, callback: CallbackQuery):
        """Отмена на шаге ввода количества"""
        try:
            user_id = callback.from_user.id
            self.order_states.cancel_order(user_id)
            
            self.bot.answer_callback_query(callback.id, "❌ Заказ отменен")
            
            # Возвращаем к категориям
            self.start_order_process(callback.message)
            
        except Exception as e:
            logger.error(f"Ошибка при отмене количества: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка")
        
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
    
  