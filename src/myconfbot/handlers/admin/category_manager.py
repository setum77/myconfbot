# category_manager.py
import logging
from telebot import types
from telebot.types import Message, CallbackQuery
from ..shared.product_constants import ProductConstants
from .admin_base import BaseAdminHandler
from src.myconfbot.services.auth_service import AuthService

logger = logging.getLogger(__name__)

class CategoryManager:
    """Полноценный менеджер для работы с категориями"""
    
    def __init__(self, bot, db_manager, states_manager, auth_service: AuthService):
        self.bot = bot
        self.db_manager = db_manager
        self.states_manager = states_manager
        self.auth_service = auth_service

    # === ОСНОВНЫЕ ПУБЛИЧНЫЕ МЕТОДЫ ===
    
    def handle_category_callbacks(self, callback: CallbackQuery):
        """Главный обработчик callback'ов категорий"""
        logger.info(f"Received category callback: {callback.data}")
        
        if not self._check_admin_access(callback=callback):
            return
        
        try:
            data = callback.data
            logger.info(f"Processing callback data: {data}")
            
            if data == 'category_manage':
                self._show_category_management(callback)
            elif data == 'category_add':
                self.start_creation(callback)
            elif data == 'category_edit_list':
                self.start_editing(callback)
            elif data.startswith('category_edit_'):
                # category_edit_123 - редактирование конкретной категории
                category_id = int(data.replace('category_edit_', ''))
                self.show_edit_options(callback, category_id)
            elif data.startswith('category_rename_'):
                category_id = int(data.replace('category_rename_', ''))
                self._start_category_rename(callback, category_id)
            elif data.startswith('category_desc_'):
                category_id = int(data.replace('category_desc_', ''))
                self._start_category_desc_edit(callback, category_id)
            elif data.startswith('category_delete_ask_'):
                category_id = int(data.replace('category_delete_ask_', ''))
                self._show_delete_confirmation(callback, category_id)
            elif data.startswith('category_delete_confirm_'):
                category_id = int(data.replace('category_delete_confirm_', ''))
                self._delete_category(callback, category_id)
            elif data == 'category_back_manage':
                # Назад к управлению категориями
                self._show_category_management(callback)
            elif data == 'category_back_list':
                # Назад к списку категорий для редактирования
                self.start_editing(callback)
            elif data == 'category_manadge_product_back_list':
                # Назад к управлению продукцией
                self.back_to_product_management(callback)
            else:
                logger.warning(f"Unknown callback data: {data}")
                self.bot.answer_callback_query(callback.id, "❌ Неизвестная команда")
                return
                
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка в category callback: {e}", exc_info=True)
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при обработке")

    def handle_category_states(self, message: Message):
        """Главный обработчик состояний категорий"""
        if not self._check_admin_access(message=message):
            return  

        user_id = message.from_user.id
        user_state = self.states_manager.get_management_state(user_id)
        
        if not user_state:
            return
        
        state = user_state.get('state', '')
        
        if state == 'category_adding_name':
            self._handle_category_name(message)
        elif state == 'category_adding_description':
            self._handle_category_description(message)
        elif state.startswith('category_editing_name_'):
            self._handle_category_rename(message, state)
        elif state.startswith('category_editing_desc_'):
            self._handle_category_desc_edit(message, state)

    # === СОЗДАНИЕ КАТЕГОРИЙ ===
    
    def start_creation(self, callback: CallbackQuery):
        """Начало создания категории"""
        logger.info(f'Starting category creation for user {callback.from_user.id}')
        
        self.states_manager.set_management_state(callback.from_user.id, {
            'state': 'category_adding_name',
            'category_data': {}
        })
        
        try:
            self.bot.delete_message(callback.message.chat.id, callback.message.message_id)
        except:
            pass
        
        self.bot.send_message(
            callback.message.chat.id,
            "📁 <b>Добавление новой категории</b>\n\n"
            "📝 Введите <b>название</b> категории (избегайте кавычки, эмодзи, спецсимволы):",
            parse_mode='HTML',
            reply_markup=ProductConstants.create_cancel_keyboard()
        )

    def _handle_category_name(self, message: Message):
        """Обработка названия категории"""
        if message.text == "❌ Отмена":
            self.states_manager.clear_management_state(message.from_user.id)
            self.bot.send_message(
                message.chat.id,
                "❌ Добавление категории отменено",
                reply_markup=types.ReplyKeyboardRemove()
            )
            self._show_category_management_message(message)
            return
        
        user_id = message.from_user.id
        user_state = self.states_manager.get_management_state(user_id)
        
        if not user_state or user_state.get('state') != 'category_adding_name':
            return
        
        category_data = user_state.get('category_data', {})
        
        # Валидация названия
        is_valid, error_msg = self.validate_category_name(message.text)
        if not is_valid:
            self.bot.send_message(message.chat.id, error_msg)
            return
        
        category_data['name'] = message.text
        
        # Обновляем состояние
        self.states_manager.set_management_state(user_id, {
            'state': 'category_adding_description',
            'category_data': category_data
        })
        
        self.bot.send_message(
            message.chat.id,
            "📄 Введите <b>описание</b> категории (или нажмите 'Пропустить'):",
            parse_mode='HTML',
            reply_markup=ProductConstants.create_skip_keyboard()
        )

    def _handle_category_description(self, message: Message):
        """Обработка описания категории"""
        if message.text == "❌ Отмена":
            self.states_manager.clear_management_state(message.from_user.id)
            self.bot.send_message(
                message.chat.id,
                "❌ Добавление описания отменено",
                reply_markup=types.ReplyKeyboardRemove()
            )
            self._show_category_management_message(message)
            return
        
        user_id = message.from_user.id
        user_state = self.states_manager.get_management_state(user_id)
        
        if not user_state or user_state.get('state') != 'category_adding_description':
            return
        
        category_data = user_state.get('category_data', {})
        
        if message.text.lower() == '⏭️ пропустить':
            category_data['description'] = ''
        else:
            category_data['description'] = message.text
        
        # Сохраняем категорию
        if self._save_category(category_data):
            self.states_manager.clear_management_state(user_id)
            
            self.bot.send_message(
                message.chat.id,
                f"✅ Категория <b>'{category_data['name']}'</b> успешно добавлена!",
                parse_mode='HTML',
                reply_markup=types.ReplyKeyboardRemove()
            )
            
            # Возвращаемся к управлению категориями
            self._show_category_management_message(message)
        else:
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка при сохранении категории. Попробуйте еще раз.",
                reply_markup=ProductConstants.create_cancel_keyboard()
            )

    # === РЕДАКТИРОВАНИЕ КАТЕГОРИЙ ===
    
    def start_editing(self, callback: CallbackQuery):
        """Начало редактирования - список категорий"""
        categories = self.db_manager.get_all_categories()
        
        if not categories:
            self.bot.send_message(
                callback.message.chat.id,
                "📭 Нет доступных категорий для редактирования."
            )
            return
        
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        for category in categories:
            product_count = len(self.db_manager.get_products_by_category(category['id']))
            
            keyboard.add(types.InlineKeyboardButton(
                f"📁 {category['name']} ({product_count} товаров)",
                callback_data=f"category_edit_{category['id']}"
            ))
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад",
            callback_data="category_back_manage"
        ))
        
        try:
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="✏️ <b>Редактирование категорий</b>\n\nВыберите категорию:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except:
            self.bot.send_message(
                callback.message.chat.id,
                "✏️ <b>Редактирование категорий</b>\n\nВыберите категорию:",
                parse_mode='HTML',
                reply_markup=keyboard
            )

    def show_edit_options(self, callback: CallbackQuery, category_id: int):
        """Показать опции редактирования категории"""
        category = self.db_manager.get_category_by_id(category_id)
        if not category:
            self.bot.answer_callback_query(callback.id, "❌ Категория не найдена")
            return
        
        product_count = len(self.db_manager.get_products_by_category(category_id))
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("✏️ Изменить название", callback_data=f"category_rename_{category_id}"),
            types.InlineKeyboardButton("📄 Изменить описание", callback_data=f"category_desc_{category_id}")
        )
        keyboard.add(
            types.InlineKeyboardButton("🗑️ Удалить категорию", callback_data=f"category_delete_ask_{category_id}"),
            types.InlineKeyboardButton("🔙 Назад к списку", callback_data="category_back_list")
        )
        
        category_info = (
            f"📁 <b>Редактирование категории</b>\n\n"
            f"📝 <b>Название:</b> {category['name']}\n"
            f"📄 <b>Описание:</b> {category['description'] or 'Не указано'}\n"
            f"📦 <b>Товаров в категории:</b> {product_count}\n"
            f"📅 <b>Создана:</b> {category['created_at'].strftime('%d.%m.%Y')}\n\n"
            f"Выберите действие:"
        )
        
        try:
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=category_info,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except:
            self.bot.send_message(
                callback.message.chat.id,
                category_info,
                parse_mode='HTML',
                reply_markup=keyboard
            )

    def _start_category_rename(self, callback: CallbackQuery, category_id: int):
        """Начать переименование категории"""
        self.states_manager.set_management_state(callback.from_user.id, {
            'state': f'category_editing_name_{category_id}',
            'category_id': category_id
        })
        
        category = self.db_manager.get_category_by_id(category_id)
        if not category:
            self.bot.answer_callback_query(callback.id, "❌ Категория не найдена")
            return
        
        self.bot.send_message(
            callback.message.chat.id,
            f"✏️ <b>Переименование категории</b>\n\n"
            f"Текущее название: <b>{category['name']}</b>\n"
            f"Введите новое название:",
            parse_mode='HTML',
            reply_markup=ProductConstants.create_cancel_keyboard()
        )

    def _start_category_desc_edit(self, callback: CallbackQuery, category_id: int):
        """Начать изменение описания категории"""
        self.states_manager.set_management_state(callback.from_user.id, {
            'state': f'category_editing_desc_{category_id}',
            'category_id': category_id
        })
        
        category = self.db_manager.get_category_by_id(category_id)
        if not category:
            self.bot.answer_callback_query(callback.id, "❌ Категория не найдена")
            return
        
        self.bot.send_message(
            callback.message.chat.id,
            f"📄 <b>Изменение описания категории</b>\n\n"
            f"Текущее описание: <b>{category['description'] or 'Не указано'}</b>\n"
            f"Введите новое описание (или 'Пропустить' для очистки):",
            parse_mode='HTML',
            reply_markup=ProductConstants.create_skip_keyboard()
        )

    def _handle_category_rename(self, message: Message, state: str):
        """Обработка переименования категории"""
        if message.text == "❌ Отмена":
            self.states_manager.clear_management_state(message.from_user.id)
            self.bot.send_message(
                message.chat.id,
                "❌ Переименование категории отменено",
                reply_markup=types.ReplyKeyboardRemove()
            )
            self._show_category_management_message(message)
            return
        
        category_id = int(state.replace('category_editing_name_', ''))
        success, message_text = self.update_category_name(category_id, message.text)
        
        self.bot.send_message(message.chat.id, message_text)
        if success:
            self.states_manager.clear_management_state(message.from_user.id)
            self._show_category_management_message(message)

    def _handle_category_desc_edit(self, message: Message, state: str):
        """Обработка изменения описания категории"""
        if message.text == "❌ Отмена":
            self.states_manager.clear_management_state(message.from_user.id)
            self.bot.send_message(
                message.chat.id,
                "❌ Обработка описания категории отменено",
                reply_markup=types.ReplyKeyboardRemove()
            )
            self._show_category_management_message(message)
            return
        
        category_id = int(state.replace('category_editing_desc_', ''))
        new_description = '' if message.text.lower() == '⏭️ пропустить' else message.text
        success, message_text = self.update_category_description(category_id, new_description)
        
        self.bot.send_message(message.chat.id, message_text)
        if success:
            self.states_manager.clear_management_state(message.from_user.id)
            self._show_category_management_message(message)

    # === УДАЛЕНИЕ КАТЕГОРИЙ ===
    
    def _show_delete_confirmation(self, callback: CallbackQuery, category_id: int):
        """Показать подтверждение удаления"""
        category = self.db_manager.get_category_by_id(category_id)
        if not category:
            self.bot.answer_callback_query(callback.id, "❌ Категория не найдена")
            return
        
        product_count = len(self.db_manager.get_products_by_category(category_id))
        
        if product_count > 0:
            # Если в категории есть товары, показываем предупреждение
            warning_text = (
                f"\n⚠️ <b>Внимание!</b> В категории <b>{category['name']} - {product_count}</b> товаров.\n"
                f"Необходимо удалить эти товары или поменять категорию у этих товаров.\n\n"
                f"❌ <b>Удаление категории невозможно</b>"
            )
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton("✏️ Редактировать товары", callback_data=f"category_edit_products_{category_id}"),
                types.InlineKeyboardButton("🔙 Назад", callback_data=f"category_edit_{category_id}")
            )
            
            try:
                self.bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text=warning_text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            except:
                self.bot.send_message(
                    callback.message.chat.id,
                    warning_text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
        else:
                  
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton("✅ Да, удалить", callback_data=f"category_delete_confirm_{category_id}"),
                types.InlineKeyboardButton("❌ Отменить", callback_data=f"category_edit_{category_id}")
            )
            
            confirmation_text = (
                f"🗑️ <b>Подтверждение удаления категории</b>\n\n"
                f"📝 <b>Название:</b> {category['name']}\n"
                f"📄 <b>Описание:</b> {category['description'] or 'Не указано'}\n"
                f"📦 <b>Товаров:</b> {product_count}\n\n"
                f"Вы уверены, что хотите удалить эту категорию?"
            )
            
            try:
                self.bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text=confirmation_text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            except:
                self.bot.send_message(
                    callback.message.chat.id,
                    confirmation_text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )

    # def _delete_category_handler(self, callback: CallbackQuery, category_id: int):
    #     """Удаление категории"""
    #     success, message_text = self.delete_category(category_id)
        
    #     try:
    #         self.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    #     except:
    #         pass
            
    #     self.bot.send_message(callback.message.chat.id, message_text)
    #     self._show_category_management(callback)

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _save_category(self, category_data: dict) -> bool:
        """Сохранение категории в БД"""
        try:
            return self.db_manager.add_category(
                name=category_data['name'],
                description=category_data.get('description', '')
            )
        except Exception as e:
            logger.error(f"Ошибка при сохранении категории: {e}")
            return False

    def update_category_name(self, category_id: int, new_name: str) -> tuple[bool, str]:
        """Обновление названия категории"""
        is_valid, error_msg = self.validate_category_name(new_name, exclude_category_id=category_id)
        if not is_valid:
            return False, error_msg
        
        try:
            success = self.db_manager.update_category_field(category_id, 'name', new_name)
            return success, "✅ Название категории обновлено!" if success else "❌ Ошибка при обновлении"
        except Exception as e:
            logger.error(f"Ошибка при обновлении названия категории: {e}")
            return False, "❌ Ошибка при обновлении"

    def update_category_description(self, category_id: int, new_description: str) -> tuple[bool, str]:
        """Обновление описания категории"""
        try:
            success = self.db_manager.update_category_field(category_id, 'description', new_description)
            return success, "✅ Описание категории обновлено!" if success else "❌ Ошибка при обновлении"
        except Exception as e:
            logger.error(f"Ошибка при обновлении описания категории: {e}")
            return False, "❌ Ошибка при обновлении"

    def _delete_category(self, callback: CallbackQuery, category_id: int) -> tuple[bool, str]:
        """Удаление категории (только если нет товаров)"""
        try:
            # Проверяем еще раз на случай, если что-то изменилось
            product_count = len(self.db_manager.get_products_by_category(category_id))
            
            if product_count > 0:
                # Если вдруг появились товары - показываем ошибку
                self.bot.send_message(
                    callback.message.chat.id,
                    f"❌ Нельзя удалить категорию! В ней осталось {product_count} товаров."
                )
                # Возвращаем к редактированию категории
                self.show_edit_options(callback, category_id)
                return
            
            # Получаем информацию о категории для сообщения
            category = self.db_manager.get_category_by_id(category_id)
            if not category:
                self.bot.answer_callback_query(callback.id, "❌ Категория не найдена")
                return
            
            # Удаляем категорию
            success = self.db_manager._delete_category(category_id)
            
            if success:
                message_text = f"✅ Категория '{category['name']}' успешно удалена!"
            else:
                message_text = "❌ Ошибка при удалении категории"
                
        except Exception as e:
            logger.error(f"Ошибка при удалении категории: {e}")
            message_text = "❌ Ошибка при удалении категории"
        
        # Удаляем сообщение с подтверждением
        try:
            self.bot.delete_message(callback.message.chat.id, callback.message.message_id)
        except:
            pass
            
        # Показываем результат
        self.bot.send_message(callback.message.chat.id, message_text)
        
        # Возвращаемся к управлению категориями
        self._show_category_management(callback)

    def validate_category_name(self, name: str, exclude_category_id: int = None) -> tuple[bool, str]:
        """Валидация названия категории"""
        if not name or len(name.strip()) == 0:
            return False, "❌ Название категории не может быть пустым"
        
        if len(name) > 100:
            return False, "❌ Название категории слишком длинное (макс. 100 символов)"
        
        categories = self.db_manager.get_all_categories()
        existing_names = []
        
        for cat in categories:
            if exclude_category_id and cat['id'] == exclude_category_id:
                continue
            existing_names.append(cat['name'].lower())
        
        if name.lower() in existing_names:
            return False, "❌ Категория с таким названием уже существует"
        
        return True, "✅ Название корректно"

    def get_categories_keyboard(self, include_cancel=True):
        """Клавиатура с категориями"""
        categories = self.db_manager.get_all_categories()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        
        for category in categories:
            keyboard.add(types.KeyboardButton(category['name']))
        
        if include_cancel:
            keyboard.add(types.KeyboardButton("❌ Отмена"))
            
        return keyboard

    def create_management_keyboard(self):
        """Клавиатура управления категориями"""
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("➕ Добавить категорию", callback_data="category_add"),
            types.InlineKeyboardButton("✏️ Редактировать категории", callback_data="category_edit_list")
        )
        keyboard.add(
            types.InlineKeyboardButton("🔙 Назад", callback_data="category_back_manage"),
            types.InlineKeyboardButton("🎂 В управление продукцией", callback_data="category_manadge_product_back_list")
                     )
        return keyboard

    def _show_category_management(self, callback: CallbackQuery):
        """Показать меню управления категориями (для callback)"""
        self._show_category_management_message(callback.message)

    def _show_category_management_message(self, message: Message):
        """Показать меню управления категориями (для message)"""
        keyboard = self.create_management_keyboard()
        
        categories = self.db_manager.get_all_categories()
        stats_text = f"📊 <b>Статистика категорий</b>\n\n📁 Всего категорий: {len(categories)}\n"
        
        for category in categories:
            product_count = len(self.db_manager.get_products_by_category(category['id']))
            stats_text += f"• {category['name']}: {product_count} товаров\n"
        
        self.bot.send_message(
            message.chat.id,
            stats_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def _check_admin_access(self, callback: CallbackQuery = None, message: Message = None) -> bool:
        """Проверка прав администратора с отправкой сообщения об ошибке"""
        
        # Определяем, откуда пришел запрос
        if callback:
            user_id = callback.from_user.id
            chat_id = callback.message.chat.id if callback.message else callback.from_user.id
        elif message:
            user_id = message.from_user.id
            chat_id = message.chat.id
        else:
            return False
        
        # Пропускаем проверку для сообщений от самого бота
        if user_id == self.bot.get_me().id:
            return True
        
        # Используем AuthService для проверки прав
        is_admin = self.auth_service.is_admin(user_id)
        
        if not is_admin:
            error_msg = "❌ Нет прав администратора"
            if callback:
                self.bot.answer_callback_query(callback.id, error_msg)
            else:
                self.bot.send_message(chat_id, error_msg)
            return False
        
        return True
    
    def back_to_product_management(self, callback: CallbackQuery):
        """Возврат в меню управления продукцией"""
        try:
            # Удаляем текущее сообщение
            self.bot.delete_message(callback.message.chat.id, callback.message.message_id)
        except:
            pass
        self.bot.send_message(
            callback.message.chat.id,
            "🏪 <b>Управление продукцией</b>\n\nВыберите действие:",
            reply_markup=ProductConstants.create_management_keyboard(),
            parse_mode='HTML'
        )