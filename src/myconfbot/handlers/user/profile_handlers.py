import logging
import os
import io
from typing import Optional
from PIL import Image
from src.myconfbot.config import Config
from telebot import types
from telebot.types import Message, CallbackQuery

from src.myconfbot.handlers.user.base_user_handler import BaseUserHandler

# Config.setup_logging()
class ProfileHandler(BaseUserHandler):
    """Обработчик управления профилем пользователя"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
        self.logger = logging.getLogger(__name__)
    
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
        @self.bot.message_handler(content_types=['photo'])
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
            # Используем метод get_user_info который возвращает словарь
            user_info = self.db_manager.get_user_info(user_id)
            
            if not user_info:
                self.bot.send_message(chat_id, "❌ Профиль не найден. Попробуйте /start")
                return
            
            # Формируем сообщение с профилем
            profile_text = self._format_profile_text(user_info)
            
            # Создаем клавиатуру для редактирования
            keyboard = self._create_profile_keyboard()
            
            # Отправляем фото если есть
            photo_path = user_info.get('photo_path')
            if  photo_path and os.path.exists(photo_path):
                try:
                    with open(photo_path, 'rb') as photo:
                        self.bot.send_photo(
                            chat_id, photo, 
                            caption=profile_text,
                            parse_mode='Markdown', 
                            reply_markup=keyboard
                        )
                    return # Важно: выходим после отправки фото
                except Exception as e:
                    self.logger.error(f"Ошибка при отправке фото: {e}")
                    self._send_profile_text(chat_id, profile_text, keyboard)
            else:
                self._send_profile_text(chat_id, profile_text, keyboard)
                
        except Exception as e:
            self.logger.error(f"Ошибка при показе профиля: {e}", exc_info=True)
            self.bot.send_message(chat_id, "❌ Ошибка при загрузке профиля")
    
    def _format_profile_text(self, user_info: dict) -> str:
        """Форматирование текста профиля"""
        profile_text = f"👤 *Ваш профиль*\n\n"
        profile_text += f"📛 *Имя:* {user_info.get('full_name') or 'Не указано'}\n"
        profile_text += f"📱 *Username:* @{user_info.get('telegram_username') or 'Не указан'}\n"
        profile_text += f"📞 *Телефон:* {user_info.get('phone') or 'Не указан'}\n"
        profile_text += f"📍 *Адрес:* {user_info.get('address') or 'Не указан'}\n"
        profile_text += f"🎭 *Статус:* {'👑 Администратор' if user_info.get('is_admin') else '👤 Клиент'}\n"
        return profile_text
    
    def _create_profile_keyboard(self) -> types.InlineKeyboardMarkup:
        """Создание клавиатуры для профиля"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("✏️ Изменить имя", callback_data="edit_profile_name"),
            types.InlineKeyboardButton("📞 Изменить телефон", callback_data="edit_profile_phone")
        )
        keyboard.add(
            types.InlineKeyboardButton("📍 Изменить адрес", callback_data="edit_profile_address"),
            types.InlineKeyboardButton("📷 Изменить фото", callback_data="edit_profile_photo")
        )
        return keyboard
    
    def _send_profile_text(self, chat_id: int, profile_text: str, keyboard: types.InlineKeyboardMarkup):
        """Отправка текстового профиля"""
        self.bot.send_message(chat_id, profile_text, parse_mode='Markdown', reply_markup=keyboard)
        self.bot.send_message(chat_id, "🖼️ Фотография не добавлена")
    
    def _handle_profile_edit_callback(self, callback: CallbackQuery):
        """Обработка callback'ов редактирования профиля"""
        user_id = callback.from_user.id
        chat_id = callback.message.chat.id
        action = callback.data.replace('edit_profile_', '')
        
        # Устанавливаем состояние редактирования
        self.states_manager.set_user_state(user_id, {
            'state': f'editing_{action}',
            'message_id': callback.message.message_id
        })
        
        if action == 'name':
            self.bot.send_message(chat_id, "✏️ Введите ваше новое имя:")
        elif action == 'phone':
            self.bot.send_message(chat_id, "📞 Введите ваш новый телефон:")
        elif action == 'address':
            self.bot.send_message(chat_id, "📍 Введите ваш новый адрес:")
        elif action == 'photo':
            self.bot.send_message(chat_id, "📷 Отправьте ваше новое фото:")
        
        self.bot.answer_callback_query(callback.id)
    
    def _handle_profile_photo(self, message: Message):
        """Обработка загрузки фото профиля"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_user_state(user_id)
        
        if not user_state or user_state.get('state') != 'editing_photo':
            return
        
        try:
            # Получаем информацию о файле
            file_info = self.bot.get_file(message.photo[-1].file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            # Сжимаем изображение
            compressed_image = self._compress_image(downloaded_file)
            
            # Создаем директорию для фото пользователя
            user_photo_dir = f"data/users/{user_id}"
            os.makedirs(user_photo_dir, exist_ok=True)
            
            # Сохраняем сжатое фото
            photo_path = f"{user_photo_dir}/profile.jpg"
            with open(photo_path, 'wb') as new_file:
                new_file.write(compressed_image)
            
            # Получаем размер файла для информации
            file_size_kb = len(compressed_image) / 1024

            # Обновляем путь к фото в базе
            # self.auth_service.update_user_info(user_id, photo_path=photo_path)
            self.db_manager.update_user_info(user_id, photo_path=photo_path)
            
            # Убираем состояние редактирования
            self.states_manager.clear_user_state(user_id)
            
            self.bot.send_message(
                message.chat.id, 
                f"✅ Фото профиля обновлено! Размер: {file_size_kb:.1f} KB"
            )
            
            # Показываем обновленный профиль
            self.show_my_profile(message)
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении фото: {e}", exc_info=True)
            self.bot.send_message(message.chat.id, "❌ Ошибка при сохранении фото")
    
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
            if field == 'name':
                if len(new_value) < 2:
                    self.bot.send_message(message.chat.id, "❌ Имя должно быть не короче 2 символов")
                    return
                self.db_manager.update_user_info(user_id, full_name=new_value)
                
            elif field == 'phone':
                if not any(char.isdigit() for char in new_value) or len(new_value) < 5:
                    self.bot.send_message(message.chat.id, "❌ Введите корректный телефон")
                    return
                self.db_manager.update_user_info(user_id, phone=new_value)
                
            elif field == 'address':
                if len(new_value) < 5:
                    self.bot.send_message(message.chat.id, "❌ Адрес должен быть не короче 5 символов")
                    return
                self.db_manager.update_user_info(user_id, address=new_value)
            
            # Убираем состояние редактирования
            self.states_manager.clear_user_state(user_id)
            
            field_names = {'name': 'Имя', 'phone': 'Телефон', 'address': 'Адрес'}
            self.bot.send_message(
                message.chat.id, 
                f"✅ {field_names[field]} успешно обновлено!"
            )
            
            # Показываем обновленный профиль
            self.show_my_profile(message)
            
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении {field}: {e}", exc_info=True)
            self.bot.send_message(message.chat.id, f"❌ Ошибка при обновлении {field}")
    
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