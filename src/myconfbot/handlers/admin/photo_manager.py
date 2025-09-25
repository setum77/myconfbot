# src/myconfbot/handlers/admin/photo_manager.py
import logging
import os
import uuid
from telebot import types
from telebot.types import Message, CallbackQuery
from .product_states import ProductState
from .product_constants import ProductConstants
from .product_viewer import ProductViewer


logger = logging.getLogger(__name__)

class PhotoManager:
    """Универсальный менеджер фотографий"""
    
    def __init__(self, bot, db_manager, states_manager, photos_dir):
        self.bot = bot
        self.db_manager = db_manager
        self.photos_dir = photos_dir
        self.states_manager = states_manager

    # === ОБРАБОТЧИКИ 
    def register_photo_handlers(self):
        """Регистрация обработчиков фотографий"""
        
        @self.bot.message_handler(
            content_types=['photo'],
            func=lambda message: self.states_manager.get_product_state(message.from_user.id) == ProductState.ADDING_PHOTOS
        )
        def handle_photo_message(message: Message):
            self._handle_photo_message(message)

    def _handle_photo_message(self, message: Message):
        """Обработка сообщения с фото"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_product_state(user_id)
        
        if user_state != ProductState.ADDING_PHOTOS:
            self.bot.send_message(message.chat.id, "❌ Сначала начните процесс добавления фото")
            return
        
        product_data = self.states_manager.get_product_data(user_id)
        product_id = product_data.get('id')
        
        if not product_id:
            self.bot.send_message(message.chat.id, "❌ Ошибка: товар не найден")
            return
        
        # Обрабатываем фото
        success = self.handle_photo_addition(message, product_id)
        
        if success:
            self.bot.send_message(message.chat.id, "✅ Фото добавлено! Отправьте еще фото или нажмите '✅ Готово'")
        else:
            self.bot.send_message(message.chat.id, "❌ Ошибка при добавлении фото")
    
    
    
    # === ОСНОВНЫЕ МЕТОДЫ ===
    
    def ask_add_photos_after_creation(self, message: Message, product_id: int, product_name: str):
        """Спросить о добавлении фото после создания товара"""
        keyboard = self.create_photo_question_keyboard()
        self.bot.send_message(
            message.chat.id,
            f"✅ Товар '{product_name}' сохранен!\n\n"
            "📸 Хотите добавить фотографии сейчас?",
            reply_markup=keyboard
        )

    def show_photo_management(self, message: Message, product_id: int):
        """Показать меню управления фото для товара"""
        photos = self.db_manager.get_product_photos(product_id)
        product = self.db_manager.get_product_by_id(product_id)
        
        if not product:
            self.bot.send_message(message.chat.id, "❌ Товар не найден")
            return
        
        keyboard = self._create_photo_management_keyboard(product_id, photos)
        
        photo_status = self._get_photo_status_text(photos)
        
        self.bot.send_message(
            message.chat.id,
            f"📸 <b>Управление фотографиями</b>\n"
            f"Товар: {product['name']}\n"
            f"{photo_status}\n"
            "Выберите действие:",
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def handle_photo_addition(self, message: Message, product_id: int):
        """Обработка добавления фото"""
        if message.content_type != 'photo':
            self.bot.send_message(message.chat.id, "❌ Пожалуйста, отправьте фото")
            return False
        
        try:
            photo_id = message.photo[-1].file_id
            photo_path = self._save_photo(photo_id, product_id)
            
            if not photo_path:
                self.bot.send_message(message.chat.id, "❌ Ошибка при сохранении фото")
                return False
            
            # Если это первое фото - делаем его главным
            existing_photos = self.db_manager.get_product_photos(product_id)
            is_main = len(existing_photos) == 0
            
            success = self.db_manager.add_product_photo(product_id, photo_path, is_main)
            
            if success:
                # Если установили как главное - обновляем продукт
                if is_main:
                    self.db_manager.update_product_cover_photo(product_id, photo_path)
                
                logger.info(f"Фото успешно добавлено к товару {product_id}, путь: {photo_path}")
                return True
            else:
                logger.error(f"Ошибка при добавлении фото в БД для товара {product_id}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при добавлении фото: {e}")
            self.bot.send_message(message.chat.id, "❌ Ошибка при обработке фото")
            return False

    def set_main_photo(self, product_id: int, photo_number: int):
        """Установить главное фото по номеру"""
        try:
            photos = self.db_manager.get_product_photos(product_id)
            if not 1 <= photo_number <= len(photos):
                return False
                
            selected_photo = photos[photo_number - 1]
            
            # Сбрасываем все фото на не-главные
            for photo in photos:
                self.db_manager.update_photo_main_status(photo['id'], False)
            
            # Устанавливаем выбранное как главное
            self.db_manager.update_photo_main_status(selected_photo['id'], True)
            self.db_manager.update_product_cover_photo(product_id, selected_photo['photo_path'])
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при установке главного фото: {e}")
            return False

    def delete_photo(self, product_id: int, photo_number: int):
        """Удалить фото по номеру"""
        try:
            photos = self.db_manager.get_product_photos(product_id)
            if not 1 <= photo_number <= len(photos):
                return False
                
            photo_to_delete = photos[photo_number - 1]
            
            # Удаляем из БД
            success = self.db_manager.delete_product_photo(photo_to_delete['id'])
            if success:
                # Удаляем файл
                if os.path.exists(photo_to_delete['photo_path']):
                    os.remove(photo_to_delete['photo_path'])
                
                # Если удалили главное фото - установить новое главное
                remaining_photos = self.db_manager.get_product_photos(product_id)
                if remaining_photos:
                    new_main = remaining_photos[0]
                    self.set_main_photo(product_id, 1)  # Первое фото становится главным
                else:
                    # Нет фото - сбрасываем cover_photo
                    self.db_manager.update_product_cover_photo(product_id, None)
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при удалении фото: {e}")
            return False

    def show_photos_for_selection(self, message: Message, product_id: int, mode: str = "main"):
        """Показать фото для выбора (главное/удаление)"""
        photos = self.db_manager.get_product_photos(product_id)
        product = self.db_manager.get_product_by_id(product_id)
        
        if not photos:
            self.bot.send_message(message.chat.id, "❌ У товара нет фотографий")
            return False
        
        photos_text = "\n".join([f"{i+1}. 📸 Фото {i+1}" for i in range(len(photos))])
        
        if mode == "main":
            text = f"📸 Выберите <b>главное фото</b> для товара '{product['name']}':\n\n{photos_text}"
        else:  # delete
            text = f"🗑️ Выберите <b>фото для удаления</b> из товара '{product['name']}':\n\n{photos_text}"
        
        keyboard = self._create_photo_selection_keyboard(photos, product_id, mode)
        
        self.bot.send_message(
            message.chat.id,
            text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        return True
    
    # === МЕТОДЫ ДЛЯ РАБОТЫ С СОСТОЯНИЯМИ ===
    
    def start_photo_addition(self, callback: CallbackQuery, product_id: int):
        """Начать добавление фото"""
        self.states_manager.set_product_state(callback.from_user.id, {
            'state': ProductState.ADDING_PHOTOS,
            'product_data': {'id': product_id}
        })
        
        self.bot.send_message(
            callback.message.chat.id,
            "📸 Отправьте фотографии товара:\n\n"
            "После добавления всех фото нажмите '✅ Готово'",
            reply_markup=ProductConstants.create_photos_done_keyboard()
        )

    def start_photo_addition_after_creation(self, message: Message, product_id: int):
        """Начать добавление фото после создания товара"""
        self.states_manager.set_product_state(message.from_user.id, {
            'state': ProductState.ADDING_PHOTOS,
            'product_data': {'id': product_id}
        })
        
        self.bot.send_message(
            message.chat.id,
            "📸 Отправьте фотографии товара:\n\n"
            "После добавления всех фото нажмите '✅ Готово'",
            reply_markup=ProductConstants.create_photos_done_keyboard()
        )

    def handle_photos_done(self, message: Message):
        """Обработка завершения добавления фото"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_product_state(user_id)

        # Проверяем, что пользователь находится в состоянии добавления фото
        if user_state != ProductState.ADDING_PHOTOS:
            self.bot.send_message(message.chat.id, "❌ Операция не активна")
            self.states_manager.clear_product_state(user_id)
            return None

        product_data = self.states_manager.get_product_data(user_id)
        product_id = product_data.get('id')
        
        try:
            if product_id:
                photos = self.db_manager.get_product_photos(product_id)
                logger.info(f"Фотографии товара {product_id}: {len(photos)} шт.")
                
                if photos:
                    # Если есть фото, устанавливаем первое как главное (если еще не установлено)
                    main_photos = [p for p in photos if p['is_main']]
                    if not main_photos and photos:
                        self.set_main_photo(product_id, 1)
                    
                    product = self.db_manager.get_product_by_id(product_id)
                    
                    # ✅ Показываем сообщение только если есть фото
                    self.bot.send_message(
                        message.chat.id,
                        f"✅ Фотографии добавлены к товару '{product['name']}'!",
                        reply_markup=types.ReplyKeyboardRemove()
                    )

                    # Из ProductViewer вызываем метод вывода информации о товаре
                    product_viewer = ProductViewer(self.bot, self.db_manager, self.photos_dir)
                    product_viewer.show_product_summary(message, product_id)
                else:
                    # ✅ Если фото нет, показываем другое сообщение
                    product = self.db_manager.get_product_by_id(product_id)
                    self.bot.send_message(
                        message.chat.id,
                        f"✅ Товар '{product['name']}' сохранен без фотографий.",
                        reply_markup=types.ReplyKeyboardRemove()
                    )
                    
                    # Показываем информацию о товаре
                    product_viewer = ProductViewer(self.bot, self.db_manager, self.photos_dir)
                    product_viewer.show_product_summary(message, product_id)
                
                return product_id
        
        except Exception as e:
            logger.error(f"Ошибка при завершении добавления фото: {e}")
            self.bot.send_message(message.chat.id, "❌ Ошибка при обработке фотографий")
            return None
        finally:
            # Всегда очищаем состояние
            self.states_manager.clear_product_state(user_id)

    def handle_photo_question(self, message: Message):
        """Обработка ответа на вопрос о фото"""
        user_id = message.from_user.id
        product_data = self.states_manager.get_product_data(user_id)
        product_id = product_data.get('id')
        
        if message.text == "✅ Да, добавить фото":
            # Переходим к добавлению фото
            self.states_manager.set_product_state(user_id, {
                'state': ProductState.ADDING_PHOTOS,
                'product_data': product_data
            })
            
            self.bot.send_message(
                message.chat.id,
                "📸 Отправьте фотографии товара:\n\n"
                "После добавления всех фото нажмите '✅ Готово'",
                reply_markup=ProductConstants.create_photos_done_keyboard()
            )
            
        elif message.text == "⏭️ Пропустить":
            # Завершаем без фото
            self.states_manager.clear_product_state(user_id)
            self.bot.send_message(
                message.chat.id,
                f"✅ Товар готов! Можете добавить фото позже через редактирование.",
                parse_mode='HTML',
                reply_markup=types.ReplyKeyboardRemove()
            )
            return False
        else:
            self.bot.send_message(
                message.chat.id,
                "Пожалуйста, выберите вариант:",
                reply_markup=ProductConstants.create_photo_question_keyboard()
            )
            return None
        
        return True

    # === CALLBACK ОБРАБОТЧИКИ ===
    
    def handle_photo_callbacks(self, callback: CallbackQuery):
        """Обработка callback'ов фото"""
        try:
            data = callback.data
            
            if data.startswith('photo_manage_'):
                product_id = int(data.replace('photo_manage_', ''))
                self.show_photo_management(callback.message, product_id)
            
            elif data.startswith('photo_add_'):
                product_id = int(data.replace('photo_add_', ''))
                self.start_photo_addition(callback, product_id)
            
            elif data.startswith('photo_set_main_'):
                product_id = int(data.replace('photo_set_main_', ''))
                self.show_photos_for_selection(callback.message, product_id, "main")
            
            elif data.startswith('photo_delete_'):
                product_id = int(data.replace('photo_delete_', ''))
                self.show_photos_for_selection(callback.message, product_id, "delete")
            
            elif data.startswith('photo_back_'):
                product_id = int(data.replace('photo_back_', ''))
                # Возврат к редактированию товара
                self._show_edit_options(callback.message, product_id)
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка в photo callback: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при обработке")

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _save_photo(self, photo_file_id: str, product_id: int) -> str:
        """Сохранение фото на диск"""
        try:
            logger.info(f"Начало сохранения фото для товара {product_id}")
            file_info = self.bot.get_file(photo_file_id)
            logger.info(f"Информация о файле: {file_info.file_path}")
            
            downloaded_file = self.bot.download_file(file_info.file_path)
            logger.info(f"Файл скачан, размер: {len(downloaded_file)} байт")
            
            file_extension = os.path.splitext(file_info.file_path)[1] or '.jpg'
            filename = f"{uuid.uuid4().hex}{file_extension}"
            
            product_dir = os.path.join(self.photos_dir, str(product_id))
            os.makedirs(product_dir, exist_ok=True)
            filepath = os.path.join(product_dir, filename)
            
            with open(filepath, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            # ✅ Добавим проверку, что файл действительно создан
            if os.path.exists(filepath):
                logger.info(f"Фото сохранено: {filepath}")
                return filepath
            else:
                logger.error(f"Файл не был создан: {filepath}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении фото: {e}")
            return None

    def _get_photo_status_text(self, photos: list) -> str:
        """Текст статуса фото"""
        if not photos:
            return "📷 Фотографий: нет"
        
        main_photos = [p for p in photos if p['is_main']]
        main_status = "✅ Установлено" if main_photos else "❌ Не установлено"
        
        return f"📷 Фотографий: {len(photos)} шт.\n📌 Главное фото: {main_status}"

    def _create_photo_question_keyboard(self):
        """Клавиатура вопроса о фото"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("✅ Да, добавить фото"))
        keyboard.add(types.KeyboardButton("⏭️ Пропустить"))
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard

    def _create_photo_management_keyboard(self, product_id: int, photos: list):
        """Клавиатура управления фото"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            types.InlineKeyboardButton("➕ Добавить фото", callback_data=f"photo_add_{product_id}"),
            types.InlineKeyboardButton("🖼️ Выбрать главное", callback_data=f"photo_set_main_{product_id}")
        )
        
        if photos:
            keyboard.add(
                types.InlineKeyboardButton("🗑️ Удалить фото", callback_data=f"photo_delete_{product_id}"),
                types.InlineKeyboardButton("👀 Просмотреть все", callback_data=f"photo_view_{product_id}")
            )
        
        keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data=f"photo_back_{product_id}"))
        
        return keyboard

    def _create_photo_selection_keyboard(self, photos: list, product_id: int, mode: str):
        """Клавиатура выбора фото"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        
        # Кнопки с номерами фото
        row = []
        for i in range(1, len(photos) + 1):
            row.append(types.KeyboardButton(str(i)))
            if len(row) == 3:
                keyboard.add(*row)
                row = []
        
        if row:
            keyboard.add(*row)
        
        if mode == "main":
            keyboard.add(types.KeyboardButton("🔙 К управлению фото"))
        else:
            keyboard.add(types.KeyboardButton("❌ Отмена удаления"))
        
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        
        return keyboard

    def _show_edit_options(self, message: Message, product_id: int):
        """Вернуться к редактированию товара (заглушка)"""
        self.bot.send_message(
            message.chat.id,
            f"🔙 Возврат к редактированию товара ID: {product_id}",
            reply_markup=types.ReplyKeyboardRemove()
        )