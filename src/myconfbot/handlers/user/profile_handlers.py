# src\myconfbot\handlers\user\profile_handlers.py

import logging
import io
from typing import Optional
from PIL import Image
from telebot import types
from pathlib import Path
from telebot.types import Message, CallbackQuery

from src.myconfbot.handlers.user.base_user_handler import BaseUserHandler
from src.myconfbot.utils.file_utils import FileManager
from src.myconfbot.keyboards.profile_keyboards import create_profile_keyboard
from src.myconfbot.handlers.shared.constants import (
    UserStates, CallbackTypes, Validation, Messages
)

logger = logging.getLogger(__name__)

class ProfileHandler(BaseUserHandler):
    """Обработчик управления профилем пользователя"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
        self.file_manager = FileManager(config)
        self.logger = logger
    
    def register_handlers(self):
        """Регистрация обработчиков профиля"""
        self._register_profile_callback_handlers()
        self._register_photo_handlers()
        self._register_profile_edit_handlers()
    
    def _register_profile_callback_handlers(self):
        """Регистрация callback обработчиков профиля"""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('edit_profile_'))
        def handle_profile_edit(callback: CallbackQuery):
            self._handle_profile_edit_callback(callback)
    
    def _register_photo_handlers(self):
        """Регистрация обработчиков фото"""
        @self.bot.message_handler(
            content_types=['photo'],
            func=lambda message: self.states_manager.get_user_state(message.from_user.id) is not None and
            self.states_manager.get_user_state(message.from_user.id).get('state', '') == UserStates.EDITING_PHOTO
        )
        def handle_profile_photo(message: Message):
            self._handle_profile_photo(message)
    
    def _register_profile_edit_handlers(self):
        """Регистрация обработчиков редактирования профиля"""
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_user_state(message.from_user.id) is not None and
            self.states_manager.get_user_state(message.from_user.id).get('state', '').startswith('editing_')
        )
        def handle_profile_text_edit(message: Message):
            self._handle_profile_text_edit(message)
    
    def show_my_profile(self, message: Message):
        """Показать профиль пользователя"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        try:
            user_info = self.db_manager.get_user_info(user_id)
            
            if not user_info:
                self.bot.send_message(chat_id, Messages.ERROR_PROFILE_NOT_FOUND)
                return
            
            profile_text = self._format_profile_text(user_info)
            keyboard = create_profile_keyboard()
            
            # Отправляем фото если есть
            photo_path = self.file_manager.get_user_profile_photo_path(user_id, user_info.get('photo_path'))
            self.logger.debug(f"Попытка загрузить фото профиля: {photo_path}")
            
            if photo_path and photo_path.exists():
                self.logger.debug(f"Фото существует: {photo_path}")
                try:
                    with open(photo_path, 'rb') as photo:
                        self.bot.send_photo(
                            chat_id, photo, 
                            caption=profile_text,
                            parse_mode='Markdown', 
                            reply_markup=keyboard
                        )
                    return
                except Exception as e:
                    self.logger.error(f"Ошибка при отправке фото: {e}")
                    self._send_profile_text(chat_id, profile_text, keyboard)
            else:
                self.logger.debug("Фото профиля не найдено")
                self._send_profile_text(chat_id, profile_text, keyboard)
                
        except Exception as e:
            self.logger.error(f"Ошибка при показе профиля: {e}", exc_info=True)
            self.bot.send_message(chat_id, Messages.ERROR_LOADING_PROFILE)
    
    def _get_user_profile_photo_path(self, user_id: int, db_photo_path: str = None) -> Optional[Path]:
        """Получить путь к фото профиля пользователя"""
        return self.file_manager.get_user_profile_photo_path(user_id, db_photo_path)
    
    def _format_profile_text(self, user_info: dict) -> str:
        """Форматирование текста профиля"""
        profile_text = Messages.PROFILE_TITLE
        profile_text += Messages.PROFILE_NAME.format(user_info.get('full_name') or 'Не указано')
        profile_text += Messages.PROFILE_USERNAME.format(user_info.get('telegram_username') or 'Не указан')
        profile_text += Messages.PROFILE_PHONE.format(user_info.get('phone') or 'Не указан')
        profile_text += Messages.PROFILE_ADDRESS.format(user_info.get('address') or 'Не указан')
        profile_text += Messages.PROFILE_STATUS.format('👑 Администратор' if user_info.get('is_admin') else '👤 Клиент')
        
        # Добавляем дату обновления фото если есть
        if user_info.get('photo_path'):
            # Извлекаем дату из имени файла: profile_20241215_143022.jpg
            import re
            match = re.search(r'profile_(\d{8})_', user_info.get('photo_path', ''))
            if match:
                date_str = match.group(1)
                profile_text += f"\n📅 Фото обновлено: {date_str[6:8]}.{date_str[4:6]}.{date_str[:4]}"
        
        return profile_text
    
    def _send_profile_text(self, chat_id: int, profile_text: str, keyboard: types.InlineKeyboardMarkup):
        """Отправка текстового профиля"""
        self.bot.send_message(chat_id, profile_text, parse_mode='Markdown', reply_markup=keyboard)
        self.bot.send_message(chat_id, Messages.PROFILE_NO_PHOTO)
    
    def _handle_profile_edit_callback(self, callback: CallbackQuery):
        """Обработка callback'ов редактирования профиля"""
        user_id = callback.from_user.id
        chat_id = callback.message.chat.id
        action = callback.data.replace('edit_profile_', '')
        
        # Устанавливаем состояние редактирования
        state_mapping = {
            'name': UserStates.EDITING_NAME,
            'phone': UserStates.EDITING_PHONE,
            'address': UserStates.EDITING_ADDRESS,
            'photo': UserStates.EDITING_PHOTO
        }
        
        self.states_manager.set_user_state(user_id, {
            'state': state_mapping.get(action, f'editing_{action}'),
            'message_id': callback.message.message_id,
            'action': action
        })
        
        message_mapping = {
            'name': Messages.PROFILE_EDIT_NAME,
            'phone': Messages.PROFILE_EDIT_PHONE,
            'address': Messages.PROFILE_EDIT_ADDRESS,
            'photo': Messages.PROFILE_EDIT_PHOTO
        }
        
        self.bot.send_message(chat_id, message_mapping.get(action, "Введите новые данные:"))
        self.bot.answer_callback_query(callback.id)
    
    def _handle_profile_photo(self, message: Message):
        """Обработка загрузки фото профиля"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_user_state(user_id)
        
        if not user_state or user_state.get('state') != UserStates.EDITING_PHOTO:
            return
        
        try:
            # Получаем информацию о файле
            file_info = self.bot.get_file(message.photo[-1].file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            # Сжимаем изображение
            compressed_image = self._compress_image(downloaded_file)
            
            # Сохраняем фото через FileManager
            relative_path = self.file_manager.save_user_profile_photo(
                user_id, 
                io.BytesIO(compressed_image), 
                "profile.jpg"
            )
            
            if relative_path:
                # Обновляем путь к фото в базе
                self.db_manager.update_user_info(user_id, photo_path=relative_path)
                
                # Убираем состояние редактирования
                self.states_manager.clear_user_state(user_id)
                
                file_size_kb = len(compressed_image) / 1024
                self.bot.send_message(
                    message.chat.id, 
                    Messages.PROFILE_PHOTO_UPDATE_SUCCESS.format(file_size_kb)
                )
                
                # Показываем обновленный профиль
                self.show_my_profile(message)
            else:
                self.bot.send_message(message.chat.id, Messages.ERROR_PHOTO_SAVE)
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении фото: {e}", exc_info=True)
            self.bot.send_message(message.chat.id, Messages.ERROR_PHOTO_SAVE)
    
    def _handle_profile_text_edit(self, message: Message):
        """Обработка текстового редактирования профиля"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_user_state(user_id)
        
        if not user_state:
            return
        
        state = user_state.get('state', '')
        field = state.replace('editing_', '')
        new_value = message.text.strip()
        
        try:
            validation_result = self._validate_field(field, new_value)
            if not validation_result['valid']:
                self.bot.send_message(message.chat.id, validation_result['message'])
                return
            
            # Обновляем поле в базе данных
            update_data = {self._get_field_mapping(field): new_value}
            self.db_manager.update_user_info(user_id, **update_data)
            
            # Убираем состояние редактирования
            self.states_manager.clear_user_state(user_id)
            
            field_names = {'name': 'Имя', 'phone': 'Телефон', 'address': 'Адрес'}
            self.bot.send_message(
                message.chat.id, 
                Messages.PROFILE_UPDATE_SUCCESS.format(field_names.get(field, 'Данные'))
            )
            
            # Показываем обновленный профиль
            self.show_my_profile(message)
            
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении {field}: {e}", exc_info=True)
            self.bot.send_message(
                message.chat.id, 
                Messages.ERROR_FIELD_UPDATE.format(field)
            )
    
    def _validate_field(self, field: str, value: str) -> dict:
        """Валидация полей профиля"""
        if field == 'name':
            if len(value) < Validation.MIN_NAME_LENGTH:
                return {'valid': False, 'message': Messages.VALIDATION_NAME_TOO_SHORT}
        elif field == 'phone':
            if not any(char.isdigit() for char in value) or len(value) < Validation.MIN_PHONE_DIGITS:
                return {'valid': False, 'message': Messages.VALIDATION_PHONE_INVALID}
        elif field == 'address':
            if len(value) < Validation.MIN_ADDRESS_LENGTH:
                return {'valid': False, 'message': Messages.VALIDATION_ADDRESS_TOO_SHORT}
        
        return {'valid': True}
    
    def _get_field_mapping(self, field: str) -> str:
        """Получить имя поля в базе данных"""
        mapping = {
            'name': 'full_name',
            'phone': 'phone', 
            'address': 'address'
        }
        return mapping.get(field, field)
    
    def _compress_image(self, image_data, max_size=(800, 800), quality=85, max_file_size_kb=500):
        """Сжимает изображение с несколькими этапами сжатия"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Конвертируем в RGB если нужно
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Первое сжатие
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Пытаемся достичь целевого размера файла
            current_quality = quality
            output_buffer = io.BytesIO()
            
            for attempt in range(5):  # Максимум 5 попыток
                output_buffer.seek(0)
                output_buffer.truncate(0)
                
                image.save(output_buffer, format='JPEG', quality=current_quality, optimize=True)
                
                # Проверяем размер
                if len(output_buffer.getvalue()) <= max_file_size_kb * 1024:
                    break
                    
                # Уменьшаем качество для следующей попытки
                current_quality = max(40, current_quality - 15)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            self.logger.error(f"Ошибка при сжатии изображения: {e}")
            return image_data