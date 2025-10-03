# src\myconfbot\handlers\admin\order_admin_handler.py

import logging
import os
import uuid
from datetime import datetime
from telebot import types
from telebot.types import Message, CallbackQuery

from src.myconfbot.handlers.admin.admin_base import BaseAdminHandler
from src.myconfbot.handlers.user.base_user_handler import BaseUserHandler
from src.myconfbot.handlers.shared.admin_constants import AdminConstants
from src.myconfbot.handlers.shared.constants import UserStates

logger = logging.getLogger(__name__)

class OrderAdminHandler(BaseAdminHandler):
    """Обработчик админского функционала заказов"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
    
    def register_handlers(self):
        """Регистрация обработчиков"""
        self._register_callback_handlers()
    
    def _register_callback_handlers(self):
        """Регистрация callback обработчиков"""
        
        # Обработчики управления заказами
        @self.bot.callback_query_handler(func=lambda call: call.data == "orderadm_active_orders")
        def handle_active_orders(callback: CallbackQuery):
            """Обработка кнопки 'Активные заказы'"""
            self._show_active_orders(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == "orderadm_all_orders")
        def handle_all_orders(callback: CallbackQuery):
            """Обработка кнопки 'Все заказы'"""
            self._show_all_orders(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == "orderadm_statistics")
        def handle_orders_statistics(callback: CallbackQuery):
            """Обработка кнопки 'Статистика заказов'"""
            self._show_orders_statistics(callback)
        
        # Обработчики навигации
        @self.bot.callback_query_handler(func=lambda call: call.data == "orderadm_back_management")
        def handle_back_management(callback: CallbackQuery):
            """Возврат к управлению заказами"""
            self._show_orders_management(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == "orderadm_back_active_orders")
        def handle_back_active_orders(callback: CallbackQuery):
            """Возврат к активным заказам"""
            self._show_active_orders(callback)
        
        # Обработчики конкретных заказов
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("orderadm_order_"))
        def handle_order_select(callback: CallbackQuery):
            """Обработка выбора заказа"""
            self._show_order_actions(callback)

        # Обработчик выбора статуса из кнопок
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("orderadm_select_status_"))
        def handle_status_selection(callback: CallbackQuery):
            """Обработка выбора статуса из кнопок"""
            if self._check_admin_access(callback=callback):
                self._process_status_selection_from_button(callback)
               
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("orderadm_change_status_"))
        def handle_change_status(callback: CallbackQuery):
            """Обработка изменения статуса"""
            self._show_status_history(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("orderadm_add_status_"))
        def handle_add_status(callback: CallbackQuery):
            """Обработка добавления статуса"""
            self._start_add_status_process(callback)

        # Обработчики переписки
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("orderadm_notes_"))
        def handle_order_notes(callback: CallbackQuery):
            """Обработка просмотра примечаний заказа"""
            if self._check_admin_access(callback=callback):
                self._show_order_notes(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("orderadm_add_note_"))
        def handle_add_note(callback: CallbackQuery):
            """Обработка добавления сообщения к заказу"""
            if self._check_admin_access(callback=callback):
                self._handle_add_admin_note(callback)
        
        # Обработчики кнопок управления заказом
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("orderadm_change_cost_"))
        def handle_change_cost(callback: CallbackQuery):
            """Обработка кнопки 'Изменить стоимость'"""
            if self._check_admin_access(callback=callback):
                self._start_change_cost_process(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("orderadm_change_delivery_"))
        def handle_change_delivery(callback: CallbackQuery):
            """Обработка кнопки 'Изменить доставку'"""
            if self._check_admin_access(callback=callback):
                self._start_change_delivery_process(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("orderadm_change_ready_date_"))
        def handle_change_ready_date(callback: CallbackQuery):
            """Обработка кнопки 'Изменить дату готовности'"""
            if self._check_admin_access(callback=callback):
                self._start_change_ready_date_process(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("orderadm_change_quantity_"))
        def handle_change_quantity(callback: CallbackQuery):
            """Обработка кнопки 'Изменить количество'"""
            if self._check_admin_access(callback=callback):
                self._start_change_quantity_process(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("orderadm_change_payment_status_"))
        def handle_change_payment_status(callback: CallbackQuery):
            """Обработка кнопки 'Изменить статус оплаты'"""
            if self._check_admin_access(callback=callback):
                self._start_change_payment_status_process(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("orderadm_add_admin_notes_"))
        def handle_add_admin_notes(callback: CallbackQuery):
            """Обработка кнопки 'Добавить примечание админа'"""
            if self._check_admin_access(callback=callback):
                self._start_add_admin_notes_process(callback)

        # Обработчик выбора типа доставки
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("delivery_type_"))
        def handle_delivery_type_selection(callback: CallbackQuery):
            """Обработка выбора типа доставки"""
            if self._check_admin_access(callback=callback):
                self._start_edit_delivery_type(callback)
        
        # Обработчик выбора типа количества
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("quantity_type_"))
        def handle_quantity_type_selection(callback: CallbackQuery):
            """Обработка выбора типа количества"""
            if self._check_admin_access(callback=callback):
                try:
                    parts = callback.data.split('_')
                    order_id = int(parts[2])
                    quantity_type = parts[3]  # 'weight' или 'quantity'
                    
                    user_id = callback.from_user.id
                    self.states_manager.set_user_state(user_id, {
                        'state': UserStates.ADMIN_CHANGING_QUANTITY_VALUE,
                        'order_id': order_id,
                        'quantity_type': quantity_type
                    })
                    
                    unit = "граммах" if quantity_type == "weight" else "штуках"
                    
                    self.bot.edit_message_text(
                        chat_id=callback.message.chat.id,
                        message_id=callback.message.message_id,
                        text=f"🔢 <b>Введите количество в {unit}:</b>",
                        parse_mode='HTML'
                    )
                    
                    self.bot.register_next_step_handler(
                        callback.message,
                        lambda message: self._process_new_quantity(message, order_id, quantity_type)
                    )
                    
                    self.bot.answer_callback_query(callback.id)
                    
                except Exception as e:
                    logger.error(f"Ошибка при выборе типа количества: {e}")
                    self.bot.answer_callback_query(callback.id, "❌ Ошибка при изменении количества")

        # Обработчик выбора статуса оплаты
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("payment_status_"))
        def handle_payment_status_selection(callback: CallbackQuery):
            """Обработка выбора статуса оплаты"""
            if self._check_admin_access(callback=callback):
                try:
                    parts = callback.data.split('_')
                    order_id = int(parts[2])
                    payment_status = parts[3]  # 'paid', 'unpaid', 'pending'
                    
                    status_texts = {
                        'paid': 'Оплачен',
                        'unpaid': 'Не оплачен', 
                        'pending': 'Ожидает оплаты'
                    }
                    
                    new_status = status_texts.get(payment_status, 'Не указан')
                    
                    # Обновляем статус оплаты
                    success = self.db_manager.update_order_field(order_id, 'payment_status', new_status)
                    
                    if success:
                        self.bot.edit_message_text(
                            chat_id=callback.message.chat.id,
                            message_id=callback.message.message_id,
                            text=f"✅ Статус оплаты изменен на <b>{new_status}</b>",
                            parse_mode='HTML'
                        )
                        
                        # Показываем обновленные детали заказа
                        self._show_updated_order_details(callback.message.chat.id, order_id)
                    else:
                        self.bot.answer_callback_query(callback.id, "❌ Ошибка при обновлении статуса")
                    
                except Exception as e:
                    logger.error(f"Ошибка при выборе статуса оплаты: {e}")
                    self.bot.answer_callback_query(callback.id, "❌ Ошибка при изменении статуса оплаты")
        
        # кнопка пропуска при добавлении коментария к статусу
        @self.bot.callback_query_handler(func=lambda call: call.data == "skip_notes")
        def handle_skip_notes(callback: CallbackQuery):
            """Обработка пропуска примечания"""
            if self._check_admin_access(callback=callback):
                # Получаем данные из состояния пользователя
                user_id = callback.from_user.id
                user_state = self.states_manager.get_user_state(user_id)
                
                if user_state and user_state.get('state') == UserStates.ADMIN_ADDING_STATUS:
                    order_id = user_state.get('order_id')
                    selected_status = user_state.get('selected_status')
                    
                    # Переходим к следующему шагу (добавление фото)
                    self._process_status_notes(callback, order_id, selected_status)

        # кнопка пропуска при добавлении фотографии 
        @self.bot.callback_query_handler(func=lambda call: call.data == "skip_photo")
        def handle_skip_photo(callback: CallbackQuery):
            """Обработка пропуска фото"""
            if self._check_admin_access(callback=callback):
                # Получаем данные из состояния пользователя
                user_id = callback.from_user.id
                user_state = self.states_manager.get_user_state(user_id)
                
                if user_state and user_state.get('state') == UserStates.ADMIN_ADDING_STATUS:
                    order_id = user_state.get('order_id')
                    selected_status = user_state.get('selected_status')
                    admin_notes = user_state.get('admin_notes')
                    
                    # Завершаем процесс добавления статуса
                    self._process_status_photo(callback, order_id, selected_status, admin_notes)                                                            

        
                
        
    

    def _show_orders_management(self, callback: CallbackQuery):
        """Показать управление заказами"""
        keyboard = AdminConstants.get_orders_management_keyboard()
        
        self.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="📦 Управление заказами\nВыберите действие:",
            reply_markup=keyboard
        )
        self.bot.answer_callback_query(callback.id)
    
    def _show_active_orders(self, callback: CallbackQuery):
        """Показать активные заказы"""
        try:
            # Получаем активные заказы (статус не "Выполнен / Завершён")
            active_orders = self.db_manager.get_active_orders()
            
            if not active_orders:
                self.bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text="📭 Активных заказов нет",
                    reply_markup=AdminConstants.create_active_orders_keyboard([])
                )
                return
            
            keyboard = AdminConstants.create_active_orders_keyboard(active_orders)
            
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="📋 Активные заказы\n\nВыберите заказ для управления:",
                reply_markup=keyboard
            )
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при получении активных заказов: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при загрузке заказов")
    
    def _show_all_orders(self, callback: CallbackQuery):
        """Показать все заказы"""
        # TODO: Реализовать позже
        self.bot.answer_callback_query(callback.id, "📚 Функция в разработке")
    
    def _show_orders_statistics(self, callback: CallbackQuery):
        """Показать статистику заказов"""
        # TODO: Реализовать позже
        self.bot.answer_callback_query(callback.id, "📊 Функция в разработке")
    
    def _show_order_actions(self, callback: CallbackQuery):
        """Показать действия с заказом"""
        try:
            order_id = int(callback.data.replace("orderadm_order_", ""))
            order_details = self._get_order_details_admin(order_id)
            
            if not order_details:
                self.bot.answer_callback_query(callback.id, "❌ Заказ не найден")
                return
            
            keyboard = AdminConstants.create_order_detail_keyboard(order_id)
            text = self._format_order_details_admin(order_details)
            
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при показе деталей заказа: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при загрузке заказа")

    def _process_status_selection_from_button(self, callback: CallbackQuery):
        """Обработка выбора статуса из кнопки"""
        logger.info(f"Обработка callback data: {callback.data}")
        try:
            # Разбираем callback data: orderadm_select_status_{order_id}_{status_name}
            parts = callback.data.split('_')
            logger.info(f"Разделенные части: {parts}")
            # Первые 4 части фиксированы: ['orderadm', 'select', 'status', '{order_id}']
            if len(parts) < 5:
                raise ValueError("Неверный формат callback data")
            
            order_id = int(parts[3])

            # Остальные части - это название статуса (может содержать подчеркивания)
            status_name_parts = parts[4:]
            status_name = '_'.join(status_name_parts)
            
            # Получаем текст статуса из enum
            from src.myconfbot.utils.models import OrderStatusEnum
            #status_enum = OrderStatusEnum[status_name]
            # Ищем соответствующий статус
            status_enum = None
            for status in OrderStatusEnum:
                if status.name == status_name:
                    status_enum = status
                    break
            
            if status_enum is None:
                raise ValueError(f"Статус с именем '{status_name}' не найден")
            
            
            
            selected_status = status_enum.value
            
            # Обновляем состояние
            user_id = callback.from_user.id
            user_state = self.states_manager.get_user_state(user_id)
            user_state['selected_status'] = selected_status
            user_state['step'] = 'add_notes'
            self.states_manager.set_user_state(user_id, user_state)

            # Создаем клавиатуру с кнопкой "Пропустить"
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_notes")
            )
            
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"📝 <b>Добавление примечания к статусу</b>\n\n"
                    f"Заказ: <b>#{order_id}</b>\n"
                    f"Статус: <b>{selected_status}</b>\n\n"
                    f"Добавьте примечание к статусу или нажмите 'Пропустить':",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            self.bot.register_next_step_handler(
                callback.message,
                lambda msg: self._process_status_notes(msg, order_id, selected_status)
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке выбора статуса: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при выборе статуса")
    
    
    def _show_status_history(self, callback: CallbackQuery):
        """Показать историю статусов"""
        try:
            order_id = int(callback.data.replace("orderadm_change_status_", ""))
            status_history = self._get_order_status_history(order_id)
            
            keyboard = AdminConstants.create_status_history_keyboard(order_id)
            text = self._format_status_history_for_admin(status_history, order_id)
            
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при показе истории статусов: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при загрузке статусов")
    
    def _start_add_status_process(self, callback: CallbackQuery):
        """Начать процесс добавления статуса"""
        try:
            order_id = int(callback.data.replace("orderadm_add_status_", ""))
            
            # Устанавливаем состояние для добавления статуса
            user_id = callback.from_user.id
            self.states_manager.set_user_state(user_id, {
                'state': UserStates.ADMIN_ADDING_STATUS,
                'order_id': order_id,
                'step': 'select_status'
            })
            
            # Показываем доступные статусы
            from src.myconfbot.utils.models import OrderStatusEnum
            
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            
            status_buttons = []

            for status in OrderStatusEnum:
                # Используем безопасный формат callback data
                callback_data = f"orderadm_select_status_{order_id}_{status.name}"
                
                # Обрезаем длинные названия статусов для кнопок
                button_text = status.value
                if len(button_text) > 20:
                    button_text = button_text[:17] + "..."
                    
                status_buttons.append(
                    types.InlineKeyboardButton(
                        f"🔄 {button_text}", 
                        callback_data=callback_data
                    )
                )

                # status_buttons.append(
                #     types.InlineKeyboardButton(
                #         f"🔄 {status.value}", 
                #         callback_data=f"orderadm_select_status_{order_id}_{status.name}"
                #     )
                # )
            
            # Распределяем кнопки по 2 в ряд
            for i in range(0, len(status_buttons), 2):
                if i + 1 < len(status_buttons):
                    keyboard.add(status_buttons[i], status_buttons[i + 1])
                else:
                    keyboard.add(status_buttons[i])
            
            # Добавляем кнопку возврата
            keyboard.add(
                types.InlineKeyboardButton(
                    "🔙 Назад", 
                    callback_data=f"orderadm_change_status_{order_id}"
                )
            )
            
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"🔄 <b>Добавление статуса для заказа #{order_id}</b>\n\n"
                    f"Выберите новый статус из списка ниже:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при начале добавления статуса: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при добавлении статуса")
    
    # def _process_status_selection(self, message: Message, order_id: int):
    #     """Обработка выбора статуса"""
    #     try:
    #         selected_status = message.text.strip()
            
    #         # Проверяем валидность статуса
    #         from src.myconfbot.utils.models import OrderStatusEnum
    #         valid_statuses = [status.value for status in OrderStatusEnum]
            
    #         if selected_status not in valid_statuses:
    #             self.bot.send_message(
    #                 message.chat.id,
    #                 f"❌ Неверный статус. Доступные статусы:\n" + "\n".join([f"• {status}" for status in valid_statuses])
    #             )
    #             return
            
    #         # Обновляем состояние
    #         user_id = message.from_user.id
    #         user_state = self.states_manager.get_user_state(user_id)
    #         user_state['selected_status'] = selected_status
    #         user_state['step'] = 'add_notes'
    #         self.states_manager.set_user_state(user_id, user_state)
            
    #         self.bot.send_message(
    #             message.chat.id,
    #             "📝 Добавьте примечание к статусу (или напишите 'пропустить'):"
    #         )
            
    #         self.bot.register_next_step_handler(
    #             message,
    #             lambda msg: self._process_status_notes(msg, order_id, selected_status)
    #         )
            
    #     except Exception as e:
    #         logger.error(f"Ошибка при обработке выбора статуса: {e}")
    #         self.bot.send_message(message.chat.id, "❌ Ошибка при обработке статуса")
    
    def _process_status_notes(self, message: Message, order_id: int, status: str):
        """Обработка примечания к статусу с кнопкой пропустить"""
        try:
            # Если пользователь нажал на кнопку "Пропустить" (это CallbackQuery)
            if isinstance(message, CallbackQuery) and message.data == 'skip_notes':
                admin_notes = None
                # Отвечаем на callback query
                self.bot.answer_callback_query(message.id)
                chat_id = message.message.chat.id
                user_id = message.from_user.id
                msg_obj = message.message  # Используем message из CallbackQuery
            else:
                # Это обычное текстовое сообщение
                admin_notes = message.text.strip() if message.text else None
                if admin_notes and admin_notes.lower() == 'пропустить':
                    admin_notes = None
                chat_id = message.chat.id
                user_id = message.from_user.id
                msg_obj = message
            
            # Обновляем состояние
            user_state = self.states_manager.get_user_state(user_id)
            user_state['admin_notes'] = admin_notes
            user_state['step'] = 'add_photo'
            self.states_manager.set_user_state(user_id, user_state)
            
            # Создаем клавиатуру с кнопкой "Пропустить"
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_photo")
            )
            
            self.bot.send_message(
                chat_id,
                f"📸 <b>Добавление фото к статусу заказа</b>\n\n"
                f"Заказ: <b>#{order_id}</b>\n"
                f"Статус: <b>{status}</b>\n"
                f"Примечание: <i>{admin_notes if admin_notes else 'нет'}</i>\n\n"
                f"Отправьте фото именно для этого статуса заказа или нажмите 'Пропустить':",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            # Регистрируем обработчики для следующего шага
            self.bot.register_next_step_handler(
                msg_obj,
                lambda m: self._process_status_photo(m, order_id, status, admin_notes)
            )
            
        except Exception as e:
            logger.error(f"Ошибка при обработке примечания статуса: {e}")
            # Определяем chat_id в зависимости от типа объекта
            if isinstance(message, CallbackQuery):
                chat_id = message.message.chat.id
            else:
                chat_id = message.chat.id
            self.bot.send_message(chat_id, "❌ Ошибка при обработке примечания")

    def _process_status_photo(self, message: Message, order_id: int, status: str, admin_notes: str):
        """Обработка фото статуса с кнопкой пропустить"""
        try:
            photo_path = None
            
            # Если пользователь нажал на кнопку "Пропустить" (это CallbackQuery)
            if isinstance(message, CallbackQuery) and message.data == 'skip_photo':
                # Отвечаем на callback query
                self.bot.answer_callback_query(message.id)
                user_id = message.from_user.id
                chat_id = message.message.chat.id
                # message_id = message.message.message_id
            else:
                # Обрабатываем обычное сообщение
                if message.content_type == 'photo' and message.photo:
                    # Проверяем, что это фото для статуса заказа
                    if not self._validate_status_photo(message, order_id):
                        self.bot.send_message(
                            message.chat.id,
                            "❌ Пожалуйста, отправьте фото именно для статуса заказа"
                        )
                        # Повторно регистрируем обработчик
                        self.bot.register_next_step_handler(
                            message,
                            lambda m: self._process_status_photo(m, order_id, status, admin_notes)
                        )
                        return
                    
                    # Сохраняем фото
                    photo_path = self._save_status_photo(message, order_id)
                    if photo_path:
                        self.bot.send_message(message.chat.id, "✅ Фото для статуса сохранено")
                    else:
                        self.bot.send_message(message.chat.id, "❌ Ошибка при сохранении фото")
                
                user_id = message.from_user.id
                chat_id = message.chat.id
                # message_id = message.message_id
            
            # Сохраняем статус в базу
            success = self.db_manager.add_order_status(
                order_id=order_id,
                status=status,
                admin_notes=admin_notes,
                photo_path=photo_path
            )
            
            # Очищаем состояние
            self.states_manager.clear_user_state(user_id)

            if success:
                # Формируем сообщение об успехе
                success_message = f"✅ Статус '{status}' успешно добавлен к заказу #{order_id}"
                if photo_path:
                    success_message += "\n📸 Фото добавлено к статусу"
                if admin_notes:
                    success_message += f"\n📝 Примечание: {admin_notes}"
                    
                self.bot.send_message(chat_id, success_message)
                
                # Показываем обновленную историю статусов
                status_history = self._get_order_status_history(order_id)
                keyboard = AdminConstants.create_status_history_keyboard(order_id)
                text = self._format_status_history_for_admin(status_history, order_id)
                
                self.bot.send_message(
                    chat_id,
                    text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            else:
                self.bot.send_message(chat_id, "❌ Ошибка при сохранении статуса")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке фото статуса: {e}")
            # Определяем chat_id в зависимости от типа объекта
            if isinstance(message, CallbackQuery):
                chat_id = message.message.chat.id
            else:
                chat_id = message.chat.id
            self.bot.send_message(chat_id, "❌ Ошибка при обработке фото")
            
        #     if success:
        #         self.bot.send_message(
        #             chat_id,
        #             f"✅ Статус '{status}' успешно добавлен к заказу #{order_id}"
        #         )
                
        #         # Показываем обновленную историю статусов
        #         status_history = self._get_order_status_history(order_id)
        #         keyboard = AdminConstants.create_status_history_keyboard(order_id)
        #         text = self._format_status_history_for_admin(status_history, order_id)
                
        #         self.bot.send_message(
        #             chat_id,
        #             text,
        #             parse_mode='HTML',
        #             reply_markup=keyboard
        #         )
        #     else:
        #         self.bot.send_message(
        #             chat_id,
        #             "❌ Ошибка при сохранении статуса"
        #         )
                
        # except Exception as e:
        #     logger.error(f"Ошибка при обработке фото статуса: {e}")
        #     # Определяем chat_id в зависимости от типа объекта
        #     if isinstance(message, CallbackQuery):
        #         chat_id = message.message.chat.id
        #     else:
        #         chat_id = message.chat.id
        #     self.bot.send_message(chat_id, "❌ Ошибка при обработке фото")

    # def _process_status_photo(self, message: Message, order_id: int, status: str, admin_notes: str):
    #     """Обработка фото статуса с кнопкой пропустить"""
    #     try:
    #         photo_path = None
            
    #         # Если пользователь нажал на кнопку "Пропустить"
    #         if hasattr(message, 'data') and message.data == 'skip_photo':
    #             # Отвечаем на callback query
    #             self.bot.answer_callback_query(message.id)
    #             user_id = message.from_user.id
    #             chat_id = message.message.chat.id
    #             message_id = message.message.message_id
    #         else:
    #             # Обрабатываем обычное сообщение
    #             if message.content_type == 'photo' and message.photo:
    #                 # Проверяем, что это фото для статуса заказа
    #                 if not self._validate_status_photo(message, order_id):
    #                     self.bot.send_message(
    #                         message.chat.id,
    #                         "❌ Пожалуйста, отправьте фото именно для статуса заказа"
    #                     )
    #                     # Повторно регистрируем обработчик
    #                     self.bot.register_next_step_handler(
    #                         message,
    #                         lambda m: self._process_status_photo(m, order_id, status, admin_notes)
    #                     )
    #                     return
                    
    #                 # Сохраняем фото
    #                 photo_path = self._save_status_photo(message, order_id)
    #                 if photo_path:
    #                     self.bot.send_message(message.chat.id, "✅ Фото для статуса сохранено")
    #                 else:
    #                     self.bot.send_message(message.chat.id, "❌ Ошибка при сохранении фото")
                
    #             user_id = message.from_user.id
    #             chat_id = message.chat.id
    #             message_id = message.message_id
            
    #         # Сохраняем статус в базу
    #         success = self.db_manager.add_order_status(
    #             order_id=order_id,
    #             status=status,
    #             admin_notes=admin_notes,
    #             photo_path=photo_path
    #         )
            
    #         # Очищаем состояние
    #         self.states_manager.clear_user_state(user_id)
            
    #         if success:
    #             self.bot.send_message(
    #                 chat_id,
    #                 f"✅ Статус '{status}' успешно добавлен к заказу #{order_id}"
    #             )
                
    #             # Показываем обновленную историю статусов
    #             status_history = self._get_order_status_history(order_id)
    #             keyboard = AdminConstants.create_status_history_keyboard(order_id)
    #             text = self._format_status_history_for_admin(status_history, order_id)
                
    #             self.bot.send_message(
    #                 chat_id,
    #                 text,
    #                 parse_mode='HTML',
    #                 reply_markup=keyboard
    #             )
    #         else:
    #             self.bot.send_message(
    #                 chat_id,
    #                 "❌ Ошибка при сохранении статуса"
    #             )
                
    #     except Exception as e:
    #         logger.error(f"Ошибка при обработке фото статуса: {e}")
    #         self.bot.send_message(message.chat.id, "❌ Ошибка при обработке фото")

    def _validate_status_photo(self, message: Message, order_id: int) -> bool:
        """Проверка, что фото предназначено для статуса заказа"""
        try:
            # Проверяем состояние пользователя
            user_id = message.from_user.id
            user_state = self.states_manager.get_user_state(user_id)
            
            if not user_state:
                return False
                
            # Проверяем, что пользователь находится в процессе добавления статуса
            if user_state.get('state') != UserStates.ADMIN_ADDING_STATUS:
                return False
                
            # Проверяем, что order_id совпадает
            if user_state.get('order_id') != order_id:
                return False
                
            # Проверяем, что это действительно фото (дополнительная проверка)
            if not message.photo:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при проверке фото статуса: {e}")
            return False

    def _save_status_photo(self, message: Message, order_id: int) -> str:
        """Сохранение фото статуса заказа"""
        try:
            # Создаем путь для сохранения
            import os
            from datetime import datetime
            
            # Базовая папка для данных
            base_data_dir = "data"
            orders_dir = os.path.join(base_data_dir, "orders")
            order_dir = os.path.join(orders_dir, f"order_{order_id}")
            status_photos_dir = os.path.join(order_dir, "status_photos")
            
            # Создаем директории, если они не существуют
            os.makedirs(status_photos_dir, exist_ok=True)
            
            # Получаем фото (берем самое высокое качество)
            photo = message.photo[-1]
            file_id = photo.file_id
            
            # Получаем информацию о файле
            file_info = self.bot.get_file(file_id)
            file_extension = os.path.splitext(file_info.file_path)[1] or '.jpg'
            
            # Генерируем уникальное имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"status_photo_{timestamp}{file_extension}"
            file_path = os.path.join(status_photos_dir, filename)
            
            # Скачиваем и сохраняем файл
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            with open(file_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            logger.info(f"Фото статуса сохранено: {file_path}")
            
            # Возвращаем относительный путь для хранения в БД
            relative_path = os.path.join("orders", f"order_{order_id}", "status_photos", filename)
            return relative_path
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении фото статуса: {e}")
            return None

    # def _process_status_photo(self, message: Message, order_id: int, status: str, admin_notes: str):
    #     """Обработка фото статуса с кнопкой пропустить"""
    #     try:
    #         photo_path = None
            
    #         # Если пользователь нажал на кнопку "Пропустить"
    #         if hasattr(message, 'data') and message.data == 'skip_photo':
    #             # Отвечаем на callback query
    #             self.bot.answer_callback_query(message.id)
    #             user_id = message.from_user.id
    #             chat_id = message.message.chat.id
    #             message_id = message.message.message_id
    #         else:
    #             # Обрабатываем обычное сообщение
    #             if message.content_type == 'photo' and message.photo:
    #                 # TODO: Реализовать сохранение фото
    #                 photo_path = "path/to/saved/photo.jpg"  # Заглушка
    #                 # Отправляем подтверждение о получении фото
    #                 self.bot.send_message(message.chat.id, "✅ Фото получено")
                
    #             user_id = message.from_user.id
    #             chat_id = message.chat.id
    #             message_id = message.message_id
            
    #         # Сохраняем статус в базу
    #         success = self.db_manager.add_order_status(
    #             order_id=order_id,
    #             status=status,
    #             admin_notes=admin_notes,
    #             photo_path=photo_path
    #         )
            
    #         # Очищаем состояние
    #         self.states_manager.clear_user_state(user_id)
            
    #         if success:
    #             self.bot.send_message(
    #                 chat_id,
    #                 f"✅ Статус '{status}' успешно добавлен к заказу #{order_id}"
    #             )
                
    #             # Показываем обновленную историю статусов
    #             status_history = self._get_order_status_history(order_id)
    #             keyboard = AdminConstants.create_status_history_keyboard(order_id)
    #             text = self._format_status_history_for_admin(status_history, order_id)
                
    #             self.bot.send_message(
    #                 chat_id,
    #                 text,
    #                 parse_mode='HTML',
    #                 reply_markup=keyboard
    #             )
    #         else:
    #             self.bot.send_message(
    #                 chat_id,
    #                 "❌ Ошибка при сохранении статуса"
    #             )
                
    #     except Exception as e:
    #         logger.error(f"Ошибка при обработке фото статуса: {e}")
    #         self.bot.send_message(message.chat.id, "❌ Ошибка при обработке фото")
    
    # Вспомогательные методы для работы с данными
    
    def _get_active_orders(self):
        """Получить активные заказы (статус не 'Выполнен / Завершён')"""
        try:
            # Используем метод из DatabaseManager вместо прямого запроса
            return self.db_manager.get_active_orders()
        except Exception as e:
            logger.error(f"Ошибка при получении активных заказов: {e}")
            return []
    
    # def _get_order_brief_info(self, order_id: int):
    #     """Получить краткую информацию о заказе"""
    #     try:
    #         # Используем метод из DatabaseManager
    #         order_details = self.db_manager.get_order_full_details(order_id)
    #         if not order_details:
    #             return None
            
    #         order = order_details['order']
    #         product = order_details['product']
            
    #         return {
    #             'id': order['id'],
    #             'ready_at': order['ready_at'],
    #             'product_name': product['name'] if product else 'Неизвестно',
    #             'quantity': order['quantity'],
    #             'weight_grams': order['weight_grams']
    #         }
            
    #     except Exception as e:
    #         logger.error(f"Ошибка при получении краткой информации о заказе: {e}")
    #         return None

    def _get_order_details_admin(self, order_id: int) -> dict:
        """Получить детальную информацию о заказе для администратора (аналогично my_order_handler)"""
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
                        'user_id': order.user_id,
                        'user_telegram_id': order_user.telegram_id if order_user else None,
                        'product_id': order.product_id,
                        'quantity': order.quantity,
                        'weight_grams': order.weight_grams,
                        'delivery_type': order.delivery_type,
                        'delivery_address': order.delivery_address,
                        'created_at': order.created_at,
                        'ready_at': order.ready_at,
                        'total_cost': order.total_cost,
                        'payment_type': order.payment_type,
                        'payment_status': order.payment_status,
                        'admin_notes': order.admin_notes
                    },
                    'user': {
                        'id': order_user.id if order_user else None,
                        'telegram_id': order_user.telegram_id if order_user else None,
                        'full_name': order_user.full_name if order_user else 'Неизвестно',
                        'telegram_username': order_user.telegram_username if order_user else None,
                        'phone': order_user.phone if order_user else None,
                        'address': order_user.address if order_user else None
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
                        'created_at': last_status.created_at if last_status else None,
                        'admin_notes': last_status.admin_notes if last_status else None
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
    
    def _get_order_status_history(self, order_id: int):
        """Получить историю статусов заказа"""
        try:
            # Используем метод из DatabaseManager
            return self.db_manager.get_order_status_history(order_id)
        except Exception as e:
            logger.error(f"Ошибка при получении истории статусов: {e}")
            return []
    
    # Методы форматирования
    
    # def _format_order_brief_info(self, order_info: dict) -> str:
    #     """Форматирование краткой информации о заказе"""
    #     text = "📦 <b>Информация о заказе</b>\n\n"
    #     text += f"🆔 <b>ID заказа:</b> #{order_info['id']}\n"
        
    #     if order_info['ready_at']:
    #         text += f"⏰ <b>Дата готовности:</b> {order_info['ready_at'].strftime('%d.%m.%Y %H:%M')}\n"
        
    #     text += f"🎂 <b>Продукт:</b> {order_info['product_name']}\n"
        
    #     # Определение отображаемого количества
    #     if order_info['weight_grams']:
    #         text += f"⚖️ <b>Количество:</b> {order_info['weight_grams']} г\n"
    #     elif order_info['quantity']:
    #         text += f"🔢 <b>Количество:</b> {order_info['quantity']} шт\n"
        
    #     return text
    
    def _format_order_details_admin(self, order_details: dict) -> str:
        """Форматирование полной информации о заказе для администратора"""
        order = order_details['order']
        product = order_details['product']
        user = order_details['user']
        last_status = order_details['last_status']
        
        # Расчет времени до готовности
        time_until_ready = ""
        if order['ready_at']:
            from datetime import datetime
            now = datetime.now()
            time_diff = order['ready_at'] - now
            
            if time_diff.total_seconds() > 0:
                days = time_diff.days
                hours = time_diff.seconds // 3600
                time_until_ready = f"{days} дн. {hours} час."
            else:
                time_until_ready = "Время готовности прошло"
        
        text = "📋 <b>Детальная информация о заказе</b>\n\n"
        text += f"🆔 <b>ID заказа:</b> #{order['id']}\n"
        text += f"👤 <b>Имя клиента:</b> {user['full_name'] if user else 'Неизвестно'}\n"
        
        if user['telegram_username']:
            text += f"📱 <b>Telegram:</b> @{user['telegram_username']}\n"
        
        if user['phone']:
            text += f"📞 <b>Телефон:</b> {user['phone']}\n"
        
        if user['address']:
            text += f"🏠 <b>Адрес:</b> {user['address']}\n"
        
        text += f"📅 <b>Дата заказа:</b> {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
        text += f"🎂 <b>Название продукта:</b> {product['name'] if product else 'Неизвестно'}\n"
        text += f"🚚 <b>Доставка:</b> {order['delivery_type'] or 'Не указана'}\n"
        
        if order['delivery_address']:
            text += f"📍 <b>Адрес доставки:</b> {order['delivery_address']}\n"
        
        if order['ready_at']:
            text += f"⏰ <b>Дата готовности:</b> {order['ready_at'].strftime('%d.%m.%Y %H:%M')}\n"
        
        if time_until_ready:
            text += f"⏳ <b>Осталось времени:</b> {time_until_ready}\n"
        
        # Определение отображаемого количества
        if order['weight_grams']:
            text += f"⚖️ <b>Количество:</b> {order['weight_grams']} г\n"
        elif order['quantity']:
            unit = product['measurement_unit'] if product else 'шт'
            text += f"🔢 <b>Количество:</b> {order['quantity']} {unit}\n"
        
        text += f"💰 <b>Стоимость заказа:</b> {float(order['total_cost']):.2f} руб.\n"
        text += f"💳 <b>Вид оплаты:</b> {order['payment_type'] or 'Не указан'}\n"
        text += f"✅ <b>Статус оплаты:</b> {order['payment_status'] or 'Не указан'}\n"
        text += f"🔄 <b>Текущий статус:</b> {last_status['status'] if last_status else 'Неизвестно'}\n"
        
        if last_status and last_status['admin_notes']:
            text += f"📝 <b>Примечание к статусу:</b> {last_status['admin_notes']}\n"
        
        if order['admin_notes']:
            text += f"🗒️ <b>Примечание админа к заказу:</b> {order['admin_notes']}\n"
        
        return text
    
    def _format_status_history_for_admin(self, status_history: list, order_id: int) -> str:
        """Форматирование истории статусов для администратора с фото"""
        text = f"🔄 <b>История статусов заказа #{order_id}</b>\n\n"
        
        if not status_history:
            text += "📭 История статусов пуста\n"
            return text
        
        for status in status_history:
            text += f"📅 <b>{status['created_at'].strftime('%d.%m.%Y %H:%M')}</b>\n"
            text += f"🔄 <b>Статус:</b> {status['status']}\n"
            
            if status['admin_notes']:
                text += f"📝 <b>Примечание:</b> {status['admin_notes']}\n"
            
            if status['photo_path']:
                # Показываем, что есть фото
                text += f"📸 <b>Есть фото</b>\n"
                
                # Можно также отправить само фото, но для этого нужен отдельный метод
                # text += f"📸 <a href=\"{self._get_full_photo_url(status['photo_path'])}\">Фото</a>\n"
            
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        return text
    
    def _get_full_photo_url(self, relative_path: str) -> str:
        """Получение полного URL/path к фото (заглушка, можно реализовать позже)"""
        # В будущем можно реализовать отдачу фото через веб-сервер
        # Пока просто возвращаем относительный путь
        return relative_path
    
    # def _format_status_history_for_admin(self, status_history: list, order_id: int) -> str:
    #     """Форматирование истории статусов для администратора"""
    #     text = f"🔄 <b>История статусов заказа #{order_id}</b>\n\n"
        
    #     if not status_history:
    #         text += "📭 История статусов пуста\n"
    #         return text
        
    #     for status in status_history:
    #         text += f"📅 <b>{status['created_at'].strftime('%d.%m.%Y %H:%M')}</b>\n"
    #         text += f"🔄 <b>Статус:</b> {status['status']}\n"
            
    #         if status['admin_notes']:
    #             text += f"📝 <b>Примечание:</b> {status['admin_notes']}\n"
            
    #         if status['photo_path']:
    #             text += f"📸 <b>Есть фото</b>\n"
            
    #         text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
    #     return text
    
    # --- методы для работы с перепиской ---
    
    def _show_order_notes(self, callback: CallbackQuery):
        """Показать примечания к заказу для администратора"""
        try:
            order_id = int(callback.data.replace('orderadm_notes_', ''))
            order_notes = self.db_manager.get_order_notes(order_id)
            
            if not order_notes:
                message_text = (
                    "💬 <b>Примечания к заказу #{}</b>\n\n"
                    "📭 Пока нет примечаний.\n\n"
                    "Здесь отображается переписка по заказу между клиентом и администратором."
                ).format(order_id)
            else:
                message_text = self._format_order_notes_admin(order_notes, order_id)
            
            keyboard = AdminConstants.create_order_notes_keyboard(order_id)

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

    def _handle_add_admin_note(self, callback: CallbackQuery):
        """Обработка добавления сообщения администратором к заказу"""
        try:
            order_id = int(callback.data.replace('orderadm_add_note_', ''))
            
            # Сохраняем order_id в состоянии пользователя
            user_id = callback.from_user.id
            self.states_manager.set_user_state(user_id, {
                'state': UserStates.ADMIN_ADDING_NOTE,
                'order_id': order_id
            })
            
            self.bot.answer_callback_query(
                callback.id, 
                "✍️ Введите ваше сообщение для заказа"
            )
            
            # Устанавливаем состояние ожидания сообщения
            self.bot.send_message(
                callback.message.chat.id,
                f"💬 <b>Добавление сообщения к заказу #{order_id}</b>\n\n"
                "Введите ваше сообщение:",
                parse_mode='HTML'
            )
            
            self.bot.register_next_step_handler(
                callback.message, 
                lambda message: self._process_admin_note(message, order_id)
            )
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении сообщения: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при добавлении сообщения")

    def _process_admin_note(self, message: Message, order_id: int):
        """Обработка введенного администратором сообщения"""
        try:
            user_id = message.from_user.id
            note_text = message.text
            
            # Проверяем, что пользователь все еще администратор
            if not self._check_admin_access(message=message):
                return
            
            # Сохраняем примечание в базу данных
            success = self.db_manager.add_order_note(
                order_id=order_id,
                telegram_id=user_id,
                note_text=note_text
            )
            
            # Очищаем состояние
            self.states_manager.clear_user_state(user_id)
            
            if success:
                # Получаем обновленные примечания
                order_notes = self.db_manager.get_order_notes(order_id)
                
                if not order_notes:
                    message_text = (
                        "💬 <b>Примечания к заказу #{}</b>\n\n"
                        "📭 Пока нет примечаний.\n\n"
                        "Здесь отображается переписка по заказу между клиентом и администратором."
                    ).format(order_id)
                else:
                    message_text = self._format_order_notes_admin(order_notes, order_id)
                
                # Используем клавиатуру для примечаний
                keyboard = AdminConstants.create_order_notes_keyboard(order_id)
                
                # Отправляем новое сообщение с обновленными примечаниями
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
            logger.error(f"Ошибка при обработке сообщения администратора: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Произошла ошибка. Попробуйте позже."
            )

    def _format_order_notes_admin(self, order_notes: list, order_id: int) -> str:
        """Форматирование примечаний к заказу для администратора"""
        text = f"💬 <b>Примечания к заказу #{order_id}</b>\n\n"
        
        for note in order_notes:
            # Определяем тип отправителя
            sender_type = "👤 Администратор" if self._is_admin_user(note['user_name']) else "👥 Клиент"
            
            text += f"{sender_type} | {note['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            text += "----\n"
            text += f"💬 {note['note_text']}\n"
            text += "━━━━━━━━━━━━━━━━━━\n\n"
        
        return text

    def _is_admin_user(self, user_name: str) -> bool:
        """Проверка, является ли отправитель администратором (простая эвристика)"""
        # Здесь можно добавить более сложную логику проверки,
        # например, по наличию определенных маркеров в имени или через базу данных
        admin_indicators = ['admin', 'админ', 'administrator']
        return any(indicator in user_name.lower() for indicator in admin_indicators)
    
    # Методы для изменения стоимости
    def _start_change_cost_process(self, callback: CallbackQuery):
        """Начать процесс изменения стоимости"""
        try:
            order_id = int(callback.data.replace("orderadm_change_cost_", ""))
            
            # Устанавливаем состояние для изменения стоимости
            user_id = callback.from_user.id
            self.states_manager.set_user_state(user_id, {
                'state': UserStates.ADMIN_CHANGING_COST,
                'order_id': order_id
            })
            
            # Получаем текущую стоимость заказа
            order_details = self._get_order_details_admin(order_id)
            current_cost = order_details['order']['total_cost'] if order_details else 0
            
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"💰 <b>Изменение стоимости заказа #{order_id}</b>\n\n"
                    f"Текущая стоимость: <b>{float(current_cost):.2f} руб.</b>\n\n"
                    f"Введите новую стоимость:",
                parse_mode='HTML'
            )
            
            self.bot.register_next_step_handler(
                callback.message,
                lambda message: self._process_new_cost(message, order_id)
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при начале изменения стоимости: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при изменении стоимости")

    def _process_new_cost(self, message: Message, order_id: int):
        """Обработка новой стоимости"""
        try:
            user_id = message.from_user.id
            
            # Проверяем, что введено число
            try:
                new_cost = float(message.text.strip().replace(',', '.'))
                if new_cost < 0:
                    raise ValueError("Стоимость не может быть отрицательной")
            except ValueError:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Пожалуйста, введите корректное число для стоимости (например: 1500.50)"
                )
                return
            
            # Обновляем стоимость в базе данных
            success = self.db_manager.update_order_field(order_id, 'total_cost', new_cost)
            
            # Очищаем состояние
            self.states_manager.clear_user_state(user_id)
            
            if success:
                self.bot.send_message(
                    message.chat.id,
                    f"✅ Стоимость заказа #{order_id} изменена на <b>{new_cost:.2f} руб.</b>",
                    parse_mode='HTML'
                )
                
                # Показываем обновленные детали заказа
                order_details = self._get_order_details_admin(order_id)
                keyboard = AdminConstants.create_order_detail_keyboard(order_id)
                text = self._format_order_details_admin(order_details)
                
                self.bot.send_message(
                    message.chat.id,
                    text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Ошибка при обновлении стоимости"
                )
                
        except Exception as e:
            logger.error(f"Ошибка при обработке новой стоимости: {e}")
            self.bot.send_message(message.chat.id, "❌ Ошибка при изменении стоимости")

    # Методы для изменения доставки
    def _start_change_delivery_process(self, callback: CallbackQuery):
        """Начать процесс изменения доставки"""
        try:
            order_id = int(callback.data.replace("orderadm_change_delivery_", ""))
            
            # Устанавливаем состояние для изменения доставки
            user_id = callback.from_user.id
            self.states_manager.set_user_state(user_id, {
                'state': UserStates.ADMIN_CHANGING_DELIVERY,
                'order_id': order_id
            })
            
            # Получаем текущие данные о доставке
            order_details = self._get_order_details_admin(order_id)
            current_delivery = order_details['order']['delivery_type'] if order_details else "Не указана"
            current_address = order_details['order']['delivery_address'] if order_details else "Не указан"
            
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton("🚗 Самовывоз", callback_data=f"delivery_type_{order_id}_pickup"),
                types.InlineKeyboardButton("🚚 Доставка", callback_data=f"delivery_type_{order_id}_delivery")
            )
            keyboard.add(
                types.InlineKeyboardButton("🔙 Назад", callback_data=f"orderadm_order_{order_id}")
            )
            
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"🚚 <b>Изменение доставки заказа #{order_id}</b>\n\n"
                    f"Текущий тип: <b>{current_delivery}</b>\n"
                    f"Текущий адрес: <b>{current_address}</b>\n\n"
                    f"Выберите тип доставки:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при начале изменения доставки: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при изменении доставки")

    def _start_edit_delivery_type(self, callback: CallbackQuery):
        try:
            parts = callback.data.split('_')
            order_id = int(parts[2])
            delivery_type = parts[3]  # 'pickup' или 'delivery'
            
            delivery_type_text = "Самовывоз" if delivery_type == "pickup" else "Доставка"
            
            # Обновляем тип доставки
            self.db_manager.update_order_field(order_id, 'delivery_type', delivery_type_text)
            
            if delivery_type == "delivery":
                # Запрашиваем адрес доставки
                user_id = callback.from_user.id
                self.states_manager.set_user_state(user_id, {
                    'state': UserStates.ADMIN_CHANGING_DELIVERY_ADDRESS,
                    'order_id': order_id
                })
                
                self.bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text=f"📍 <b>Введите адрес доставки для заказа #{order_id}:</b>",
                    parse_mode='HTML'
                )
                
                self.bot.register_next_step_handler(
                    callback.message,
                    lambda message: self._process_delivery_address(message, order_id)
                )
            else:
                # Для самовывоза очищаем адрес
                self.db_manager.update_order_field(order_id, 'delivery_address', None)
                
                self.bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text=f"✅ Тип доставки изменен на <b>Самовывоз</b>",
                    parse_mode='HTML'
                )
                
                # Показываем обновленные детали заказа
                self._show_updated_order_details(callback.message.chat.id, order_id)
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при выборе типа доставки: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при изменении доставки")

    def _process_delivery_address(self, message: Message, order_id: int):
        """Обработка адреса доставки"""
        try:
            user_id = message.from_user.id
            delivery_address = message.text.strip()
            
            if not delivery_address:
                self.bot.send_message(message.chat.id, "❌ Адрес не может быть пустым")
                return
            
            # Обновляем адрес доставки
            success = self.db_manager.update_order_field(order_id, 'delivery_address', delivery_address)
            
            # Очищаем состояние
            self.states_manager.clear_user_state(user_id)
            
            if success:
                self.bot.send_message(
                    message.chat.id,
                    f"✅ Адрес доставки обновлен: <b>{delivery_address}</b>",
                    parse_mode='HTML'
                )
                
                # Показываем обновленные детали заказа
                self._show_updated_order_details(message.chat.id, order_id)
            else:
                self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении адреса")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке адреса доставки: {e}")
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении адреса")

    # Методы для изменения даты готовности
    def _start_change_ready_date_process(self, callback: CallbackQuery):
        """Начать процесс изменения даты готовности"""
        try:
            order_id = int(callback.data.replace("orderadm_change_ready_date_", ""))
            
            # Устанавливаем состояние для изменения даты
            user_id = callback.from_user.id
            self.states_manager.set_user_state(user_id, {
                'state': UserStates.ADMIN_CHANGING_READY_DATE,
                'order_id': order_id
            })
            
            # Получаем текущую дату готовности
            order_details = self._get_order_details_admin(order_id)
            current_date = order_details['order']['ready_at'] if order_details else None
            
            current_date_text = current_date.strftime('%d.%m.%Y %H:%M') if current_date else "Не указана"
            
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"⏰ <b>Изменение даты готовности заказа #{order_id}</b>\n\n"
                    f"Текущая дата: <b>{current_date_text}</b>\n\n"
                    f"Введите новую дату в формате <b>ДД.ММ.ГГГГ ЧЧ:MM</b>\n"
                    f"Например: <code>25.12.2024 14:30</code>",
                parse_mode='HTML'
            )
            
            self.bot.register_next_step_handler(
                callback.message,
                lambda message: self._process_new_ready_date(message, order_id)
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при начале изменения даты: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при изменении даты")

    def _process_new_ready_date(self, message: Message, order_id: int):
        """Обработка новой даты готовности"""
        try:
            user_id = message.from_user.id
            date_text = message.text.strip()
            
            # Парсим дату
            try:
                new_date = datetime.strptime(date_text, '%d.%m.%Y %H:%M')
            except ValueError:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Неверный формат даты. Используйте: <b>ДД.ММ.ГГГГ ЧЧ:MM</b>\n"
                    "Например: <code>25.12.2024 14:30</code>",
                    parse_mode='HTML'
                )
                return
            
            # Обновляем дату в базе данных
            success = self.db_manager.update_order_field(order_id, 'ready_at', new_date)
            
            # Очищаем состояние
            self.states_manager.clear_user_state(user_id)
            
            if success:
                self.bot.send_message(
                    message.chat.id,
                    f"✅ Дата готовности изменена на <b>{new_date.strftime('%d.%m.%Y %H:%M')}</b>",
                    parse_mode='HTML'
                )
                
                # Показываем обновленные детали заказа
                self._show_updated_order_details(message.chat.id, order_id)
            else:
                self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении даты")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке новой даты: {e}")
            self.bot.send_message(message.chat.id, "❌ Ошибка при изменении даты")

    # Методы для изменения количества
    def _start_change_quantity_process(self, callback: CallbackQuery):
        """Начать процесс изменения количества"""
        try:
            order_id = int(callback.data.replace("orderadm_change_quantity_", ""))
            
            # Устанавливаем состояние для изменения количества
            user_id = callback.from_user.id
            self.states_manager.set_user_state(user_id, {
                'state': UserStates.ADMIN_CHANGING_QUANTITY,
                'order_id': order_id
            })
            
            # Получаем текущие данные
            order_details = self._get_order_details_admin(order_id)
            current_quantity = order_details['order']['quantity'] if order_details else None
            current_weight = order_details['order']['weight_grams'] if order_details else None
            
            product = order_details['product'] if order_details else None
            measurement_unit = product['measurement_unit'] if product else 'шт'
            
            quantity_text = ""
            if current_weight:
                quantity_text = f"{current_weight} г"
            elif current_quantity:
                quantity_text = f"{current_quantity} {measurement_unit}"
            else:
                quantity_text = "Не указано"
            
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton("⚖️ Вес (граммы)", callback_data=f"quantity_type_{order_id}_weight"),
                types.InlineKeyboardButton("🔢 Количество (шт)", callback_data=f"quantity_type_{order_id}_quantity")
            )
            keyboard.add(
                types.InlineKeyboardButton("🔙 Назад", callback_data=f"orderadm_order_{order_id}")
            )
            
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"⚖️ <b>Изменение количества заказа #{order_id}</b>\n\n"
                    f"Текущее количество: <b>{quantity_text}</b>\n\n"
                    f"Выберите тип количества:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при начале изменения количества: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при изменении количества")

    

    def _process_new_quantity(self, message: Message, order_id: int, quantity_type: str):
        """Обработка нового количества"""
        try:
            user_id = message.from_user.id
            
            # Проверяем, что введено число
            try:
                new_value = float(message.text.strip().replace(',', '.'))
                if new_value <= 0:
                    raise ValueError("Количество должно быть положительным")
            except ValueError:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Пожалуйста, введите корректное число"
                )
                return
            
            # Обновляем данные в базе
            if quantity_type == "weight":
                success1 = self.db_manager.update_order_field(order_id, 'weight_grams', new_value)
                success2 = self.db_manager.update_order_field(order_id, 'quantity', None)
                success = success1 and success2
                display_text = f"{new_value} г"
            else:
                success1 = self.db_manager.update_order_field(order_id, 'quantity', int(new_value))
                success2 = self.db_manager.update_order_field(order_id, 'weight_grams', None)
                success = success1 and success2
                display_text = f"{int(new_value)} шт"
            
            # Очищаем состояние
            self.states_manager.clear_user_state(user_id)
            
            if success:
                self.bot.send_message(
                    message.chat.id,
                    f"✅ Количество изменено на <b>{display_text}</b>",
                    parse_mode='HTML'
                )
                
                # Показываем обновленные детали заказа
                self._show_updated_order_details(message.chat.id, order_id)
            else:
                self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении количества")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке нового количества: {e}")
            self.bot.send_message(message.chat.id, "❌ Ошибка при изменении количества")

    # Методы для изменения статуса оплаты
    def _start_change_payment_status_process(self, callback: CallbackQuery):
        """Начать процесс изменения статуса оплаты"""
        try:
            order_id = int(callback.data.replace("orderadm_change_payment_status_", ""))
            
            # Устанавливаем состояние для изменения статуса оплаты
            user_id = callback.from_user.id
            self.states_manager.set_user_state(user_id, {
                'state': UserStates.ADMIN_CHANGING_PAYMENT_STATUS,
                'order_id': order_id
            })
            
            # Получаем текущий статус оплаты
            order_details = self._get_order_details_admin(order_id)
            current_status = order_details['order']['payment_status'] if order_details else "Не указан"
            
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton("✅ Оплачен", callback_data=f"payment_status_{order_id}_paid"),
                types.InlineKeyboardButton("❌ Не оплачен", callback_data=f"payment_status_{order_id}_unpaid")
            )
            keyboard.add(
                types.InlineKeyboardButton("⏳ Ожидает оплаты", callback_data=f"payment_status_{order_id}_pending")
            )
            keyboard.add(
                types.InlineKeyboardButton("🔙 Назад", callback_data=f"orderadm_order_{order_id}")
            )
            
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"💳 <b>Изменение статуса оплаты заказа #{order_id}</b>\n\n"
                    f"Текущий статус: <b>{current_status}</b>\n\n"
                    f"Выберите новый статус:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при начале изменения статуса оплаты: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при изменении статуса оплаты")

    

    # Методы для добавления примечания админа
    def _start_add_admin_notes_process(self, callback: CallbackQuery):
        """Начать процесс добавления примечания админа"""
        try:
            order_id = int(callback.data.replace("orderadm_add_admin_notes_", ""))
            
            # Устанавливаем состояние для добавления примечания
            user_id = callback.from_user.id
            self.states_manager.set_user_state(user_id, {
                'state': UserStates.ADMIN_ADDING_ORDER_NOTES,
                'order_id': order_id
            })
            
            # Получаем текущее примечание
            order_details = self._get_order_details_admin(order_id)
            current_notes = order_details['order']['admin_notes'] if order_details else None
            
            current_notes_text = current_notes if current_notes else "Примечаний нет"
            
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"📝 <b>Добавление примечания админа для заказа #{order_id}</b>\n\n"
                    f"Текущее примечание: <i>{current_notes_text}</i>\n\n"
                    f"Введите новое примечание:",
                parse_mode='HTML'
            )
            
            self.bot.register_next_step_handler(
                callback.message,
                lambda message: self._process_admin_notes(message, order_id)
            )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при начале добавления примечания: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при добавлении примечания")

    def _process_admin_notes(self, message: Message, order_id: int):
        """Обработка примечания админа"""
        try:
            user_id = message.from_user.id
            admin_notes = message.text.strip()
            
            if not admin_notes:
                self.bot.send_message(message.chat.id, "❌ Примечание не может быть пустым")
                return
            
            # Обновляем примечание в базе данных
            success = self.db_manager.update_order_admin_notes(order_id, admin_notes)
            
            # Очищаем состояние
            self.states_manager.clear_user_state(user_id)
            
            if success:
                self.bot.send_message(
                    message.chat.id,
                    f"✅ Примечание админа добавлено к заказу #{order_id}",
                    parse_mode='HTML'
                )
                
                # Показываем обновленные детали заказа
                self._show_updated_order_details(message.chat.id, order_id)
            else:
                self.bot.send_message(message.chat.id, "❌ Ошибка при добавлении примечания")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке примечания: {e}")
            self.bot.send_message(message.chat.id, "❌ Ошибка при добавлении примечания")

    # Вспомогательный метод для показа обновленных деталей заказа
    def _show_updated_order_details(self, chat_id: int, order_id: int):
        """Показать обновленные детали заказа"""
        try:
            order_details = self._get_order_details_admin(order_id)
            keyboard = AdminConstants.create_order_detail_keyboard(order_id)
            text = self._format_order_details_admin(order_details)
            
            self.bot.send_message(
                chat_id,
                text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Ошибка при показе обновленных деталей заказа: {e}")
            self.bot.send_message(chat_id, "❌ Ошибка при загрузке деталей заказа")