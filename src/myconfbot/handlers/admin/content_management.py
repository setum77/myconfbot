import logging
import os
import tempfile
from telebot import types
from telebot.types import Message, CallbackQuery

from .admin_base import BaseAdminHandler
from src.myconfbot.utils.content_manager import ContentManager


class ContentManagementHandler(BaseAdminHandler):
    """Обработчик управления контентом"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
        self.logger = logging.getLogger(__name__)
        self.content_manager = ContentManager()
    
    def register_handlers(self):
        """Регистрация обработчиков управления контентом"""
        self._register_content_edit_handlers()
        self._register_content_preview_handlers()
        self._register_download_handlers()
        self._register_content_state_handlers()
    
    def _register_content_edit_handlers(self):
        """Регистрация обработчиков редактирования контента"""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('content_edit_'))
        def edit_content_callback(callback: CallbackQuery):
            self._edit_content_callback(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('keep_original_'))
        def keep_original_callback(callback: CallbackQuery):
            self._keep_original_callback(callback)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_edit_'))
        def cancel_editing_callback(callback: CallbackQuery):
            self._cancel_editing_callback(callback)
    
    def _register_content_preview_handlers(self):
        """Регистрация обработчиков предпросмотра контента"""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('content_preview_'))
        def preview_content_callback(callback: CallbackQuery):
            self._preview_content_callback(callback)
    
    def _register_download_handlers(self):
        """Регистрация обработчиков скачивания"""
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('download_'))
        def download_file_callback(callback: CallbackQuery):
            self._download_file_callback(callback)
    
    def _register_content_state_handlers(self):
        """Регистрация обработчиков состояний контента"""
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_management_state(message.from_user.id) is not None and
            self.states_manager.get_management_state(message.from_user.id).get('state') == 'editing_content'
        )
        def handle_content_edit(message: Message):
            self._handle_content_edit(message)
    
    def manage_content(self, message: Message):
        """Управление контентом"""
        if not self._check_admin_access(message=message):
            return
        
        keyboard = types.InlineKeyboardMarkup()
        
        files = self.content_manager.get_file_list()
        for filename in files:
            keyboard.add(
                types.InlineKeyboardButton(f"✏️ {filename}", callback_data=f"content_edit_{filename}"),
                types.InlineKeyboardButton(f"👀 {filename}", callback_data=f"content_preview_{filename}")
            )
        
        help_text = """
🎨 <b>Редактор текста</b>

Просто выберите файл для редактирования и напишите текст как в обычном сообщении.

<b>Доступные оформления:</b>
✅ <b>Жирный</b> - оберните текст двойными звёздочками **жирный текст**
✅ <i>Курсив</i> - оберните текст в нижние подчеркивания _курсивный текст_
✅ <code>Код</code> - оберните текст в `код`, символ на клавише "ё" в английской раскладке
✅ ✦ Списки проще начинать с эмодзи. Например - ▫️, или ✦ 
✅ Эмодзи 🎂 📞 💼 - вставляйте как есть. Искать подходящие, например <a href="https://getemoji.com/">тут</a>. Находим подходящий, щелкаем по нему, он скопируется в буфер обмена. В нужно месте вставляем <code>Ctrl + V</code>

<b>Важно:</b> если текст содержит символы _ * [ ] ( ) ~ ` > # + - = | { } . !, экранируйте их обратным слэшем \.
<b>Например</b>, чтобы написать 5 * 5 = 25, нужно ввести 5 \* 5 \= 25
И даже точку . и восклицательный знак !, нужно экранировать \. и \!
"""

        self.bot.send_message(
            message.chat.id,
            help_text,
            parse_mode='HTML',  # Меняем на HTML
            reply_markup=keyboard
        )
    
    def _edit_content_callback(self, callback: CallbackQuery):
        """Обработчик редактирования контента"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            filename = callback.data.replace('content_edit_', '')
            current_content = self.content_manager.get_content(filename)
            
            if current_content is None:
                return self.bot.answer_callback_query(callback.id, "❌ Файл не найден")
            
            # Создаем клавиатуру с кнопками
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("❌ Отменить редактирование", callback_data=f"cancel_edit_{filename}"),
                types.InlineKeyboardButton("💾 Сохранить без изменений", callback_data=f"keep_original_{filename}")
            )
            
            # Сохраняем состояние и оригинальный текст
            self.states_manager.set_management_state(callback.from_user.id, {
                'state': 'editing_content',
                'filename': filename,
                'original_content': current_content,
                'chat_id': callback.message.chat.id,
                'message_id': callback.message.message_id
            })
            
            # Редактируем сообщение с текущим содержимым
            self.bot.edit_message_text(
                f"📝 Редактирование {filename}\n\n"
                f"Текущее содержимое:\n\n"
                f"{current_content}\n\n"
                f"Отправьте новый текст или выберите действие:",
                callback.message.chat.id,
                callback.message.message_id,
                reply_markup=keyboard
            )
            
            self.bot.answer_callback_query(callback.id)
        except Exception as e:
            self.logger.error(f"Ошибка в edit_content_callback: {e}", exc_info=True)
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при открытии редактора")
    
    def _keep_original_callback(self, callback: CallbackQuery):
        """Обработчик сохранения без изменений"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            filename = callback.data.replace('keep_original_', '')
            user_id = callback.from_user.id
            
            # Получаем оригинальный текст из состояния
            user_state = self.states_manager.get_management_state(user_id)
            original_content = user_state.get('original_content')
            
            if original_content:
                # "Сохраняем" оригинальный текст (фактически ничего не меняем)
                self.states_manager.clear_management_state(user_id)
                
                self.bot.edit_message_text(
                    f"✅ Файл '{filename}' сохранен без изменений.",
                    callback.message.chat.id,
                    callback.message.message_id
                )
                self.bot.answer_callback_query(callback.id, "✅ Сохранено без изменений")
            else:
                self.bot.answer_callback_query(callback.id, "❌ Ошибка: не найден оригинальный текст")
                
        except Exception as e:
            self.logger.error(f"Ошибка в keep_original_callback: {e}", exc_info=True)
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при сохранении")
    
    def _cancel_editing_callback(self, callback: CallbackQuery):
        """Обработчик отмены редактирования"""
        user_id = callback.from_user.id
        filename = callback.data.replace('cancel_edit_', '')
        
        self.states_manager.clear_management_state(user_id)
        
        self.bot.edit_message_text(
            f"❌ Редактирование файла '{filename}' отменено.",
            callback.message.chat.id,
            callback.message.message_id
        )
        self.bot.answer_callback_query(callback.id, "❌ Редактирование отменено")
    
    def _preview_content_callback(self, callback: CallbackQuery):
        """Обработчик предпросмотра контента"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            filename = callback.data.replace('content_preview_', '')
            content = self.content_manager.get_content(filename)
            
            if content is None:
                return self.bot.answer_callback_query(callback.id, "❌ Файл не найден")
            
            # Создаем клавиатуру с кнопкой скачивания
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("📥 Скачать файл", callback_data=f"download_{filename}")
            )

            # Отправляем предпросмотр новым сообщением
            preview_text = f"👀 Предпросмотр {filename}:\n\n{content}"
            
            # Обрезаем если слишком длинное (ограничение Telegram)
            if len(preview_text) > 4000:
                preview_text = preview_text[:4000] + "..."
            
            self.bot.send_message(callback.message.chat.id, preview_text, reply_markup=keyboard)
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            self.logger.error(f"Ошибка в preview_content_callback: {e}", exc_info=True)
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при предпросмотре")
    
    def _handle_content_edit(self, message: Message):
        """Обработка ввода нового контента"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_management_state(user_id)
        filename = user_state.get('filename')
        chat_id = user_state.get('chat_id')
        message_id = user_state.get('message_id')
        
        # Проверяем команды отмены
        if message.text.lower() in ['отмена', 'cancel', 'назад', '❌', 'отменить']:
            self.states_manager.clear_management_state(user_id)
            self.bot.send_message(message.chat.id, "❌ Редактирование отменено.")
            return
        
        # Проверяем команду сохранения без изменений
        if message.text.lower() in ['без изменений', 'оставить', 'сохранить', '💾']:
            self.states_manager.clear_management_state(user_id)
            self.bot.send_message(message.chat.id, f"✅ Файл '{filename}' сохранен без изменений.")
            return

        if not filename:
            self.bot.send_message(message.chat.id, "❌ Ошибка: не найден файл для редактирования")
            return
        
        try:
            if self.content_manager.update_content(filename, message.text):
                # Удаляем состояние редактирования
                self.states_manager.clear_management_state(user_id)
                
                # Отправляем подтверждение
                self.bot.send_message(message.chat.id, f"✅ Файл `{filename}` успешно обновлен!", parse_mode='Markdown')
                
                # Возвращаемся к управлению контентом
                self.manage_content(message)
            else:
                self.bot.send_message(message.chat.id, "❌ Ошибка при сохранении файла")
                
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении контента: {e}", exc_info=True)
            self.bot.send_message(message.chat.id, "❌ Ошибка при сохранении файла")
    
    def _download_file_callback(self, callback: CallbackQuery):
        """Обработчик скачивания файла"""
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            filename = callback.data.replace('download_', '')
            content = self.content_manager.get_content(filename)
            
            if content is None:
                return self.bot.answer_callback_query(callback.id, "❌ Файл не найден")
            
            # Создаем временный файл для отправки
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Отправляем файл
            try:
                with open(temp_file_path, 'rb') as file:
                    self.bot.send_document(
                        callback.message.chat.id, 
                        file, 
                        caption=f"📄 Файл: {filename}"
                    )
                self.bot.answer_callback_query(callback.id, "✅ Файл отправлен")
            except Exception as e:
                self.logger.error(f"Ошибка при отправке файла: {e}")
                self.bot.answer_callback_query(callback.id, "❌ Ошибка при отправке")
            finally:
                # Удаляем временный файл
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    self.logger.error(f"Ошибка при удалении временного файла: {e}")
                
        except Exception as e:
            self.logger.error(f"Ошибка при скачивании файла: {e}", exc_info=True)
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при скачивании")