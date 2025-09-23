import logging
logger = logging.getLogger(__name__)
import os
from telebot import types
from telebot.types import Message, CallbackQuery

from .admin_base import BaseAdminHandler


class UserManagementHandler(BaseAdminHandler):
    """Обработчик управления пользователями"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
    
    def register_handlers(self):
        """Регистрация обработчиков управления пользователями"""
        self._register_user_detail_handlers()
        self._register_user_characteristic_handlers()
        self._register_user_orders_handlers()
    
    def _register_user_detail_handlers(self):
        """Регистрация обработчиков деталей пользователя"""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('user_detail_'))
        def show_user_detail(callback: CallbackQuery):
            self._show_user_detail(callback)
    
    def _register_user_characteristic_handlers(self):
        """Регистрация обработчиков характеристик пользователя"""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('user_add_char_'))
        def add_characteristic_start(callback: CallbackQuery):
            self._add_characteristic_start(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('user_cancel_char_'))
        def cancel_characteristic(callback: CallbackQuery):
            self._cancel_characteristic(callback)
        
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_management_state(message.from_user.id) is not None and
            self.states_manager.get_management_state(message.from_user.id).get('state') == 'adding_characteristic'
        )
        def handle_characteristic_input(message: Message):
            self._handle_characteristic_input(message)
    
    def _register_user_orders_handlers(self):
        """Регистрация обработчиков заказов пользователя"""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('user_orders_'))
        def show_user_orders(callback: CallbackQuery):
            self._show_user_orders(callback)
        
    def manage_users(self, message: Message):
        """Управление пользователями"""
        if not self._check_admin_access(message=message):
            return
        
        users = self.db_manager.get_all_users_info()
    
        if not users:
            self.bot.send_message(message.chat.id, "👥 Пользователи не найдены")
            return
        
        # Сортируем: сначала админы, потом клиенты, затем по имени
        users_sorted = sorted(users, key=lambda x: (
            not x['is_admin'],  # Админы first (True > False)
            x['full_name'].lower() if x['full_name'] else ''
        ))
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        for user in users_sorted:
            username = user['telegram_username'][:8] + '...' if user['telegram_username'] and len(user['telegram_username']) > 8 else user['telegram_username'] or 'нет'
            status = "👑 Админ" if user['is_admin'] else "👤 Клиент"
            btn_text = f"{user['full_name'] or 'Без имени'} | {username} | {status}"
            
            keyboard.add(types.InlineKeyboardButton(
                btn_text, 
                callback_data=f"user_detail_{user['telegram_id']}"
            ))
        
        # Добавляем кнопку возврата
        keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
        
        # keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="_back_to_admin_main"))
        
        self.bot.send_message(
            message.chat.id,
            "👥 Управление пользователями\nВыберите пользователя для просмотра:",
            reply_markup=keyboard
        )
    
    def _show_user_detail(self, callback: CallbackQuery):
        """Показать подробный профиль пользователя с фотографией"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            telegram_id = int(callback.data.replace('user_detail_', ''))
            # Используем метод который возвращает словарь
            user = self.db_manager.get_user_info(telegram_id)
            
            if not user:
                self.bot.answer_callback_query(callback.id, "❌ Пользователь не найден")
                return
            
            # Формируем информацию о пользователе
            response = self._format_user_detail_response(user)
            
            # Создаем клавиатуру с действиями
            keyboard = self._create_user_detail_keyboard(user)
            
            # Сначала отвечаем на callback чтобы убрать "часики"
            self.bot.answer_callback_query(callback.id)
            
            # Удаляем старое сообщение со списком пользователей
            try:
                self.bot.delete_message(callback.message.chat.id, callback.message.message_id)
            except Exception as e:
                logger.warning(f"Не удалось удалить сообщение: {e}")
            
            # Проверяем наличие фото
            photo_path = user.get('photo_path')
            if photo_path and os.path.exists(photo_path):
                try:
                    with open(photo_path, 'rb') as photo:
                        # Отправляем фото новым сообщением
                        self.bot.send_photo(
                            callback.message.chat.id,
                            photo,
                            caption=response,
                            reply_markup=keyboard,
                            parse_mode='HTML'
                        )
                        return
                except Exception as e:
                    logger.error(f"Ошибка при отправке фото пользователя: {e}")
            
            # Если фото нет или не удалось отправить, отправляем текстовое сообщение
            self.bot.send_message(
                callback.message.chat.id,
                response,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка в show_user_detail: {e}", exc_info=True)
            try:
                self.bot.answer_callback_query(callback.id, "❌ Ошибка при загрузке профиля")
            except:
                pass
    
    def _format_user_detail_response(self, user: dict) -> str:
        """Форматирование ответа с деталями пользователя"""
        response = f"👤 <b>Профиль пользователя</b>\n\n"
        response += f"🆔 <b>ID:</b> {user['telegram_id']}\n"
        response += f"👑 <b>Статус:</b> {'Администратор' if user['is_admin'] else 'Клиент'}\n"
        response += f"📛 <b>Полное имя:</b> {user.get('full_name', 'Не указано')}\n"
        response += f"📞 <b>Телефон:</b> {user.get('phone', 'Не указан')}\n"
        response += f"🔗 <b>Username:</b> @{user.get('telegram_username', 'Не указан')}\n"
        response += f"📝 <b>Характеристика:</b> {user.get('characteristics', 'Не указана')}\n"
        response += f"📅 <b>Дата регистрации:</b> {user['created_at'].strftime('%d.%m.%Y %H:%M') if user['created_at'] else 'Неизвестно'}\n"
        return response
    
    def _create_user_detail_keyboard(self, user: dict) -> types.InlineKeyboardMarkup:
        """Создание клавиатуры для деталей пользователя"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("➕ Изменить характеристику", callback_data=f"user_add_char_{user['telegram_id']}"),
            types.InlineKeyboardButton("📋 Заказы", callback_data=f"user_orders_{user['telegram_id']}")
        )
        keyboard.add(types.InlineKeyboardButton("🔙 Назад к списку", callback_data="admin_manage_users"))
        return keyboard
    
    def _add_characteristic_start(self, callback: CallbackQuery):
        """Начать добавление/редактирование характеристики пользователя"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            telegram_id = int(callback.data.replace('user_add_char_', ''))
            #user = self.db_manager.get_user_by_telegram_id(telegram_id)
            user = self.db_manager.get_user_info(telegram_id)
            
            if not user:
                return self.bot.answer_callback_query(callback.id, "❌ Пользователь не найден")
            
            # Сохраняем состояние
            self.states_manager.set_management_state(callback.from_user.id, {
                'state': 'adding_characteristic',
                'target_user_id': telegram_id,
                'chat_id': callback.message.chat.id,
                'message_id': callback.message.message_id
            })
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("❌ Отменить", callback_data=f"user_cancel_char_{telegram_id}"))

            edit_text = (f"📝 Изменение характеристики для пользователя {user['full_name'] or 'Без имени'}\n\n"
                    f"Текущая характеристика: {user.get('characteristics', 'Не указана')}\n\n"
                    f"Отправьте новую характеристику или нажмите 'Отменить':")
            
            # Проверяем тип сообщения (текст или фото с подписью)
            if callback.message.photo:
                # Если это фото с подписью, отправляем новое текстовое сообщение
                self.bot.edit_message_caption(
                    caption=edit_text,
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    reply_markup=keyboard
                )
            else:
                # Если это текстовое сообщение, редактируем его
                self.bot.edit_message_text(
                    edit_text,
                    callback.message.chat.id,
                    callback.message.message_id,
                    reply_markup=keyboard
                )
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка в add_characteristic_start: {e}", exc_info=True)
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при начале редактирования")
    
    def _cancel_characteristic(self, callback: CallbackQuery):
        """Отмена добавления/редактирования характеристики"""
        user_id = callback.from_user.id
        telegram_id = int(callback.data.replace('user_cancel_char_', ''))
        
        # Удаляем состояние
        self.states_manager.clear_management_state(user_id)
        
        # Сначала отвечаем на callback
        self.bot.answer_callback_query(callback.id, "❌ Изменение характеристики отменено")
        
        # Возвращаемся к профилю пользователя через новое сообщение
        self._show_user_detail_from_message(callback.message, telegram_id)
    
    def _handle_characteristic_input(self, message: Message):
        """Обработка ввода характеристики пользователя"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_management_state(user_id)
        target_user_id = user_state.get('target_user_id')
        
        if not target_user_id:
            self.bot.send_message(message.chat.id, "❌ Ошибка: пользователь не найден")
            self.states_manager.clear_management_state(user_id)
            return
        
        # Проверяем команды отмены
        if message.text.lower() in ['отмена', 'cancel', 'назад', '❌', 'отменить']:
            self.states_manager.clear_management_state(user_id)
            self.bot.send_message(message.chat.id, "❌ Добавление характеристики отменено.")
            return
        
        try:
            # Обновляем характеристику в базе данных
            if self.db_manager.update_user_characteristic(target_user_id, message.text):
                self.states_manager.clear_management_state(user_id)
                
                # Получаем обновленные данные пользователя
                #user = self.db_manager.get_user_by_telegram_id(target_user_id)
                user = self.db_manager.get_user_info(target_user_id)
                
                self.bot.send_message(
                    message.chat.id,
                    f"✅ Характеристика для пользователя {user['full_name'] or 'Без имени'} успешно обновлена!\n\n"
                    f"Новая характеристика: {message.text}"
                )
                
                # Показываем обновленный профиль
                self._show_user_detail_from_message(message, target_user_id)
            else:
                self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении характеристики")
                
        except Exception as e:
            logger.error(f"Ошибка при обновлении характеристики: {e}", exc_info=True)
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении характеристики")
    
    def _show_user_detail_from_message(self, message: Message, telegram_id: int):
        """Вспомогательная функция для показа профиля пользователя из message handler"""
        #user = self.db_manager.get_user_by_telegram_id(telegram_id)
        user = self.db_manager.get_user_info(telegram_id)
        
        if not user:
            self.bot.send_message(message.chat.id, "❌ Пользователь не найден")
            return
        
        response = self._format_user_detail_response(user)
        keyboard = self._create_user_detail_keyboard(user)
        
        # Проверяем наличие фото
        photo_path = user.get('photo_path')
        if photo_path and os.path.exists(photo_path):
            try:
                with open(photo_path, 'rb') as photo:
                    self.bot.send_photo(
                        message.chat.id,
                        photo,
                        caption=response,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                    return
            except Exception as e:
                logger.error(f"Ошибка при отправке фото: {e}")
        
        # Если фото нет или не удалось отправить
        self.bot.send_message(
            message.chat.id,
            response,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    def _show_user_orders(self, callback: CallbackQuery):
        """Показать заказы пользователя"""
        if not self._check_admin_access(callback=callback):
            return
        
        telegram_id = int(callback.data.replace('user_orders_', ''))
        #user = self.db_manager.get_user_by_telegram_id(telegram_id)
        user = self.db_manager.get_user_info(telegram_id)
        
        if not user:
            return self.bot.answer_callback_query(callback.id, "❌ Пользователь не найден")
        
        # Заглушка - реализуем позже
        self.bot.answer_callback_query(callback.id, "📋 Функция просмотра заказов пользователя в разработке")
    