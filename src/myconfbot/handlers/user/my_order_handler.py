# src/myconfbot/handlers/user/my_order_handler.py

import logging
import os
from pathlib import Path
from datetime import datetime
from telebot import types
from telebot.types import Message, CallbackQuery, ReplyKeyboardRemove

from src.myconfbot.handlers.user.base_user_handler import BaseUserHandler
from src.myconfbot.handlers.user.my_order_constants import MyOrderConstants

logger = logging.getLogger(__name__)

class MyOrderHandler(BaseUserHandler):
    """Обработчик раздела Мои заказы"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
    
    def register_handlers(self):
        """Регистрация обработчиков"""
        self._register_message_handlers()
        self._register_callback_handlers()
    
    def _register_message_handlers(self):
        """Регистрация обработчиков сообщений"""
        @self.bot.message_handler(func=lambda message: message.text == '📋 Мои заказы')
        def handle_my_orders(message: Message):
            """Обработка нажатия кнопки 'Мои заказы'"""
            self.show_user_orders(message)
    
    def _register_callback_handlers(self):
        """Регистрация callback обработчиков"""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('my_order_select_'))
        def handle_order_select(callback: CallbackQuery):
            """Обработка выбора заказа"""
            self._show_order_details(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('my_order_status_'))
        def handle_order_status(callback: CallbackQuery):
            """Обработка просмотра статуса заказа"""
            self._show_order_status(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('my_order_notes_'))
        def handle_order_notes(callback: CallbackQuery):
            """Обработка просмотра примечаний заказа"""
            self._show_order_notes(callback)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('my_order_add_note_'))
        def handle_add_note(callback: CallbackQuery):
            """Обработка добавления сообщения к заказу"""
            self._handle_add_note(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == 'my_order_back_to_list')
        def handle_back_to_list(callback: CallbackQuery):
            """Обработка возврата к списку заказов"""
            self._show_user_orders_from_callback(callback)
    
    def show_user_orders(self, message: Message):
        """Показать заказы пользователя"""
        try:
            user_id = message.from_user.id
            orders = self.db_manager.get_orders_by_user(user_id)
            
            if not orders:
                self.bot.send_message(
                    message.chat.id,
                    "📭 У вас пока нет заказов.\n\n"
                    "Совершите ваш первый заказ в разделе «🎂 Продукция»!",
                    reply_markup=MyOrderConstants.create_back_to_orders_keyboard()
                )
                return
            
            keyboard = MyOrderConstants.create_orders_keyboard(orders)
            
            self.bot.send_message(
                message.chat.id,
                "📋 <b>Ваши заказы</b>\n\n"
                "Выберите заказ для просмотра детальной информации:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка при получении заказов пользователя: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Произошла ошибка при загрузке заказов. Попробуйте позже."
            )
    
    def _show_order_details(self, callback: CallbackQuery):
        """Показать детальную информацию о заказе"""
        try:
            order_id = int(callback.data.replace('my_order_select_', ''))
            order_details = self._get_order_details(order_id)
            
            if not order_details:
                self.bot.answer_callback_query(callback.id, "❌ Заказ не найден")
                return
            
            # Формируем сообщение со сводной информацией
            message_text = self._format_order_summary(order_details)
            keyboard = MyOrderConstants.create_order_detail_keyboard(order_id)
            
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при показе деталей заказа: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при загрузке заказа")

    def _show_order_status(self, callback: CallbackQuery):
        """Показать историю статусов заказа с фото"""
        try:
            order_id = int(callback.data.replace('my_order_status_', ''))
            status_history = self._get_order_status_history(order_id)
            
            if not status_history:
                self.bot.answer_callback_query(callback.id, "❌ История статусов не найдена")
                return
            
            # Получаем текст и информацию о фото
            message_text, has_photos, photos_data = self._format_status_history(status_history)
            keyboard = MyOrderConstants.create_back_to_orders_keyboard()
            
            # Сначала отправляем текстовое сообщение
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            # Затем отправляем фото, если они есть
            if has_photos:
                for photo_data in photos_data:
                    try:
                        caption = (f"📸 <b>Фото к статусу:</b> {photo_data['status']}\n"
                                f"📅 <b>Дата:</b> {photo_data['created_at'].strftime('%d.%m.%Y %H:%M')}")
                        # Проверяем существование файла перед отправкой
                        if photo_data['photo_path'] and os.path.exists(photo_data['photo_path']):

                            with open(photo_data['photo_path'], 'rb') as photo:
                                self.bot.send_photo(
                                    chat_id=callback.message.chat.id,
                                    photo=photo,
                                    caption=caption,
                                    parse_mode='HTML'
                                )
                            logger.info(f"Фото успешно отправлено: {photo_data['photo_path']}")
                        else:
                            logger.error(f"Файл не существует: {photo_data['photo_path']}")
                            self.bot.send_message(
                                chat_id=callback.message.chat.id,
                                text=f"❌ Фото для статуса '{photo_data['status']}' не найдено\n"
                                    f"Путь: {photo_data['photo_path']}"
                            )
                    except FileNotFoundError:
                        logger.error(f"Фото не найдено: {photo_data['photo_path']}")
                        self.bot.send_message(
                            chat_id=callback.message.chat.id,
                            text=f"❌ Фото для статуса '{photo_data['status']}' не найдено на сервере"
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при отправке фото: {e}")
                        self.bot.send_message(
                            chat_id=callback.message.chat.id,
                            text=f"❌ Ошибка при отправке фото для статуса '{photo_data['status']}': {str(e)}"
                        )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при показе статусов заказа: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при загрузке статусов")
    
    # def _show_order_status(self, callback: CallbackQuery):
    #     """Показать историю статусов заказа"""
    #     try:
    #         order_id = int(callback.data.replace('my_order_status_', ''))
    #         status_history = self._get_order_status_history(order_id)
            
    #         if not status_history:
    #             self.bot.answer_callback_query(callback.id, "❌ История статусов не найдена")
    #             return
            
    #         message_text = self._format_status_history(status_history)
    #         keyboard = MyOrderConstants.create_back_to_orders_keyboard()
            
    #         self.bot.edit_message_text(
    #             chat_id=callback.message.chat.id,
    #             message_id=callback.message.message_id,
    #             text=message_text,
    #             parse_mode='HTML',
    #             reply_markup=keyboard
    #         )
            
    #         self.bot.answer_callback_query(callback.id)
            
    #     except Exception as e:
    #         logger.error(f"Ошибка при показе статусов заказа: {e}")
    #         self.bot.answer_callback_query(callback.id, "❌ Ошибка при загрузке статусов")
    
    def _show_order_notes(self, callback: CallbackQuery):
        """Показать примечания к заказу"""
        try:
            order_id = int(callback.data.replace('my_order_notes_', ''))
            order_notes = self.db_manager.get_order_notes(order_id)
            
            if not order_notes:
                message_text = (
                    "💬 <b>Примечания к заказу</b>\n\n"
                    "📭 Пока нет примечаний.\n\n"
                    "Здесь будет отображаться переписка по заказу."
                )
            else:
                message_text = self._format_order_notes(order_notes)
            
            keyboard = MyOrderConstants.create_order_notes_keyboard(order_id)

            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при показе примечаний заказа: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при загрузке примечаний")
    
    def _show_user_orders_from_callback(self, callback: CallbackQuery):
        """Показать заказы пользователя из callback"""
        try:
            user_id = callback.from_user.id
            orders = self.db_manager.get_orders_by_user(user_id)
            
            if not orders:
                self.bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text="📭 У вас пока нет заказов.\n\n"
                        "Совершите ваш первый заказ в разделе «🎂 Продукция»!",
                    parse_mode='HTML',
                    reply_markup=MyOrderConstants.create_back_to_orders_keyboard()
                )
                return
            
            keyboard = MyOrderConstants.create_orders_keyboard(orders)
            
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="📋 <b>Ваши заказы</b>\n\n"
                    "Выберите заказ для просмотра детальной информации:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при получении заказов пользователя: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Произошла ошибка при загрузке заказов. Попробуйте позже.")
    
    def _get_order_details(self, order_id: int) -> dict:
        """Получить детальную информацию о заказе"""
        try:
            with self.db_manager.session_scope() as session:
                from src.myconfbot.utils.models import Order, Product, Category, OrderStatus, OrderNote, User
                
                # Получаем заказ с связанными данными в одном запросе
                order = session.query(Order).filter_by(id=order_id).first()
                if not order:
                    return None
                
                # Получаем пользователя заказа
                order_user = session.query(User).filter_by(id=order.user_id).first()
                
                # Получаем связанные данные отдельными запросами в той же сессии
                product = session.query(Product).filter_by(id=order.product_id).first()
                category = session.query(Category).filter_by(id=product.category_id).first() if product else None
                
                # Получаем последний статус
                last_status = session.query(OrderStatus).filter_by(
                    order_id=order_id
                ).order_by(OrderStatus.created_at.desc()).first()
                
                # Получаем первое примечание
                first_note = session.query(OrderNote).filter_by(
                    order_id=order_id
                ).order_by(OrderNote.created_at).first()
                
                # Получаем автора первого примечания
                note_user = None
                if first_note:
                    note_user = session.query(User).filter_by(id=first_note.user_id).first()
                
                # Создаем словарь с простыми типами данных
                return {
                    'order': {
                        'id': order.id,
                        'user_id': order.user_id,  # user.id, а не telegram_id
                        'user_telegram_id': order_user.telegram_id if order_user else None,
                        'product_id': order.product_id,
                        'quantity': order.quantity,
                        'weight_grams': order.weight_grams,
                        'delivery_type': order.delivery_type,
                        'created_at': order.created_at,
                        'ready_at': order.ready_at,
                        'total_cost': order.total_cost,
                        'payment_type': order.payment_type,
                        'payment_status': order.payment_status,
                        'admin_notes': order.admin_notes
                    },
                    'product': {
                        'id': product.id if product else None,
                        'name': product.name if product else 'Неизвестно',
                        'category_id': product.category_id if product else None,
                        'measurement_unit': product.measurement_unit if product else 'шт',
                        'price': product.price if product else 0
                    } if product else None,
                    'category': {
                        'id': category.id if category else None,
                        'name': category.name if category else 'Неизвестно'
                    } if category else None,
                    'last_status': {
                        'status': last_status.status if last_status else 'Создан / Новый',
                        'created_at': last_status.created_at if last_status else None
                    } if last_status else None,
                    'first_note': {
                        'note_text': first_note.note_text if first_note else None,
                        'created_at': first_note.created_at if first_note else None,
                        'user_id': first_note.user_id if first_note else None,
                        'user_name': note_user.full_name if note_user else 'Неизвестно'
                    } if first_note else None
                }
                
        except Exception as e:
            logger.error(f"Ошибка при получении деталей заказа: {e}")
            return None

    # def _get_order_details(self, order_id: int) -> dict:
    #     """Получить детальную информацию о заказе"""
    #     try:
    #         with self.db_manager.session_scope() as session:
    #             from src.myconfbot.utils.models import Order, Product, Category, OrderStatus, OrderNote
                
    #             # Получаем заказ с связанными данными в одном запросе
    #             order = session.query(Order).filter_by(id=order_id).first()
    #             if not order:
    #                 return None
                
    #             # Получаем связанные данные отдельными запросами в той же сессии
    #             product = session.query(Product).filter_by(id=order.product_id).first()
    #             category = session.query(Category).filter_by(id=product.category_id).first() if product else None
                
    #             # Получаем последний статус
    #             last_status = session.query(OrderStatus).filter_by(
    #                 order_id=order_id
    #             ).order_by(OrderStatus.created_at.desc()).first()
                
    #             # Получаем первое примечание
    #             first_note = session.query(OrderNote).filter_by(
    #                 order_id=order_id
    #             ).order_by(OrderNote.created_at).first()
                
    #             # Создаем словарь с простыми типами данных
    #             return {
    #                 'order': {
    #                     'id': order.id,
    #                     'user_id': order.user_id,
    #                     'product_id': order.product_id,
    #                     'quantity': order.quantity,
    #                     'weight_grams': order.weight_grams,
    #                     'delivery_type': order.delivery_type,
    #                     'created_at': order.created_at,
    #                     'ready_at': order.ready_at,
    #                     'total_cost': order.total_cost,
    #                     'payment_type': order.payment_type,
    #                     'payment_status': order.payment_status,
    #                     'admin_notes': order.admin_notes
    #                 },
    #                 'product': {
    #                     'id': product.id if product else None,
    #                     'name': product.name if product else 'Неизвестно',
    #                     'category_id': product.category_id if product else None,
    #                     'measurement_unit': product.measurement_unit if product else 'шт',
    #                     'price': product.price if product else 0
    #                 } if product else None,
    #                 'category': {
    #                     'id': category.id if category else None,
    #                     'name': category.name if category else 'Неизвестно'
    #                 } if category else None,
    #                 'last_status': {
    #                     'status': last_status.status if last_status else 'Создан / Новый',
    #                     'created_at': last_status.created_at if last_status else None
    #                 } if last_status else None,
    #                 'first_note': {
    #                     'note_text': first_note.note_text if first_note else None,
    #                     'created_at': first_note.created_at if first_note else None,
    #                     'user_id': first_note.user_id if first_note else None
    #                 } if first_note else None
    #             }
                
    #     except Exception as e:
    #         logger.error(f"Ошибка при получении деталей заказа: {e}")
    #         return None
    
    def _get_order_status_history(self, order_id: int) -> list:
        """Получить историю статусов заказа"""
        try:
            with self.db_manager.session_scope() as session:
                from src.myconfbot.utils.models import OrderStatus
                
                status_history = session.query(OrderStatus).filter_by(
                    order_id=order_id
                ).order_by(OrderStatus.created_at).all()
                
                # Преобразуем в словари чтобы избежать проблем с сессией
                result = []
                for status in status_history:
                    photo_path = None
                    if status.photo_path:
                        # строим абсолютный путь используя config.py
                        photo_path = str(self.config.files.resolve_relative_path(status.photo_path))
                    
                    result.append({
                        'id': status.id,
                        'order_id': status.order_id,
                        'status': status.status,
                        'created_at': status.created_at,
                        'photo_path': photo_path  
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Ошибка при получении истории статусов: {e}")
            return []

    # def _get_order_status_history(self, order_id: int) -> list:
    #     """Получить историю статусов заказа"""
    #     try:
    #         with self.db_manager.session_scope() as session:
    #             from src.myconfbot.utils.models import OrderStatus
                
    #             status_history = session.query(OrderStatus).filter_by(
    #                 order_id=order_id
    #             ).order_by(OrderStatus.created_at).all()
                
    #             # Преобразуем в словари чтобы избежать проблем с сессией
    #             result = []
    #             for status in status_history:
    #                 result.append({
    #                     'id': status.id,
    #                     'order_id': status.order_id,
    #                     'status': status.status,
    #                     'created_at': status.created_at,
    #                     'photo_path': status.photo_path
    #                 })
                
    #             return result
                
    #     except Exception as e:
    #         logger.error(f"Ошибка при получении истории статусов: {e}")
    #         return []
    
    def _format_order_summary(self, order_details: dict) -> str:
        """Форматирование сводной информации о заказе"""
        order = order_details['order']
        product = order_details['product']
        category = order_details['category']
        last_status = order_details['last_status']
        first_note = order_details['first_note']
        
        # Расчет времени до готовности
        time_until_ready = ""
        if order['ready_at']:
            from datetime import datetime
            now = datetime.now()
            ready_time = order['ready_at']
            time_diff = ready_time - now
            
            if time_diff.total_seconds() > 0:
                days = time_diff.days
                hours = time_diff.seconds // 3600
                time_until_ready = f"{days} дн. {hours} час."
            else:
                time_until_ready = "Время готовности прошло"
        
        # Определение отображаемого количества
        quantity_display = ""
        if order['weight_grams']:
            quantity_display = f"{order['weight_grams']} г"
        elif order['quantity']:
            quantity_display = f"{order['quantity']} {product['measurement_unit'] if product else 'шт'}"
        
        text = "📋 <b>Детали заказа</b>\n\n"
        text += f"📅 <b>Дата и время заказа:</b> {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
        text += f"🎂 <b>Название продукта:</b> {product['name'] if product else 'Неизвестно'}\n"
        text += f"📁 <b>Категория:</b> {category['name'] if category else 'Не указана'}\n"
        
        if quantity_display:
            text += f"⚖️ <b>Количество:</b> {quantity_display}\n"
        
        if order['ready_at']:
            text += f"⏰ <b>Дата и время готовности:</b> {order['ready_at'].strftime('%d.%m.%Y %H:%M')}\n"
        
        if time_until_ready:
            text += f"⏳ <b>Время до готовности:</b> {time_until_ready}\n"
        
        text += f"🚚 <b>Условия доставки:</b> {order['delivery_type'] or 'Не указано'}\n"
        text += f"💳 <b>Вид расчета:</b> {order['payment_type'] or 'Не указан'}\n"
        text += f"💰 <b>Статус оплаты:</b> {order['payment_status'] or 'Не указан'}\n"
        text += f"🔄 <b>Статус заказа:</b> {last_status['status'] if last_status else 'Неизвестно'}\n"
        text += f"💵 <b>Стоимость заказа:</b> {float(order['total_cost']):.2f} руб.\n"
        
        if first_note and first_note['note_text']:
            # Обрезаем длинное примечание
            note_text = first_note['note_text']
            if len(note_text) > 100:
                note_text = note_text[:100] + "..."
            text += f"📝 <b>Примечания:</b> {note_text}\n"
        
        return text
    
    def _format_status_history(self, status_history: list) -> str:
        """Форматирование истории статусов с отправкой фото"""
        text = "🔄 <b>История статусов заказа</b>\n\n"
        
        has_photos = False
        photos_data = []  # Будем хранить данные о фото для отправки
        
        for status in status_history:
            text += f"📅 <b>{status['created_at'].strftime('%d.%m.%Y %H:%M')}</b>\n"
            text += f"<b>Статус:</b> {status['status']}\n"
            
            if status['photo_path']:
                text += f"📸 <b>Есть фото</b>\n"
                has_photos = True
                photos_data.append({
                    'status': status['status'],
                    'created_at': status['created_at'],
                    'photo_path': status['photo_path']
                })
            
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        return text, has_photos, photos_data
    
    # def _format_status_history(self, status_history: list) -> str:
    #     """Форматирование истории статусов"""
    #     text = "🔄 <b>История статусов заказа</b>\n\n"
        
    #     for status in status_history:
    #         text += f"📅 <b>{status['created_at'].strftime('%d.%m.%Y %H:%M')}</b>\n"
    #         text += f" <b>Статус:</b> {status['status']}\n"
            
    #         if status['photo_path']:
    #             text += f"📸 <b>Есть фото</b>\n"
            
    #         text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
    #     return text
    
    def _format_order_notes(self, order_notes: list) -> str:
        """Форматирование примечаний к заказу"""
        text = "💬 <b>Примечания к заказу</b>\n\n"
        
        for note in order_notes:
            text += f"👤 <b>{note['user_name']}</b> | {note['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            text += "----\n"
            text += f"💬 {note['note_text']}\n"
            text += "━━━━━━━━━━━━━━━━━━\n\n"
        
        return text
    
    def _handle_add_note(self, callback: CallbackQuery):
        """Обработка добавления сообщения к заказу"""
        try:
            order_id = int(callback.data.replace('my_order_add_note_', ''))
            
            # Сохраняем order_id в данных пользователя для следующего сообщения
            self.bot.answer_callback_query(
                callback.id, 
                "✍️ Введите ваше сообщение для заказа"
            )
            
            # Устанавливаем состояние ожидания сообщения
            self.bot.register_next_step_handler(
                callback.message, 
                lambda message: self._process_user_note(message, order_id)
            )
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении сообщения: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при добавлении сообщения")

    def _process_user_note(self, message: Message, order_id: int):
        """Обработка введенного пользователем сообщения"""
        try:
            user_id = message.from_user.id
            note_text = message.text
            
            # Сохраняем примечание в базу данных
            success = self.db_manager.add_order_note(
                order_id=order_id,
                telegram_id=user_id,
                note_text=note_text
            )
            
            if success:
                # Получаем обновленные примечания
                order_notes = self.db_manager.get_order_notes(order_id)
                
                if not order_notes:
                    message_text = (
                        "💬 <b>Примечания к заказу</b>\n\n"
                        "📭 Пока нет примечаний.\n\n"
                        "Здесь будет отображаться переписка по заказу."
                    )
                else:
                    message_text = self._format_order_notes(order_notes)
                
                # Используем новую клавиатуру с кнопкой добавления сообщения
                keyboard = MyOrderConstants.create_order_notes_keyboard(order_id)
                
                # Отправляем НОВОЕ сообщение вместо редактирования старого
                self.bot.send_message(
                    message.chat.id,
                    "✅ Сообщение успешно добавлено!\n\n" + message_text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                
            else:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Ошибка при сохранении сообщения. Попробуйте позже."
                )
                
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения пользователя: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Произошла ошибка. Попробуйте позже."
            )