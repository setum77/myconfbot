# product_editor.py
import logging
import os
from telebot import types
from telebot.types import Message, CallbackQuery
from ..shared.product_constants import ProductConstants

logger = logging.getLogger(__name__)

class ProductEditor:
    """Обработчик редактирования продукции"""
    
    def __init__(self, bot, db_manager, states_manager, photos_dir):
        self.bot = bot
        self.db_manager = db_manager
        self.states_manager = states_manager
        self.photos_dir = photos_dir

    def start_editing(self, callback: CallbackQuery):
        """Начало редактирования - выбор категории"""
        if not self._check_admin_access(callback):
            return
        
        categories = self.db_manager.get_all_categories()
        
        if not categories:
            self.bot.send_message(
                callback.message.chat.id,
                "📭 Нет доступных категорий для редактирования.",
                reply_markup=self._create_back_to_products_keyboard()
            )
            return
        
        # keyboard = ProductConstants.create_categories_keyboard_inline(
        #     categories=categories,
        #     db_manager=self.db_manager,
        #     back_callback="edit_select_category_{category['id']"
        # )

        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        for category in categories:
            product_count = len(self.db_manager.get_products_by_category(category['id']))
            keyboard.add(types.InlineKeyboardButton(
                f"📁 {category['name']} ({product_count})",
                callback_data=f"edit_select_category_{category['id']}"
            ))
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад",
            callback_data="edit_back_to_products"
        ))
        
        try:
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="📂 <b>Редактирование товаров</b>\n\nВыберите категорию:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except:
            self.bot.send_message(
                callback.message.chat.id,
                "📂 <b>Редактирование товаров</b>\n\nВыберите категорию:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        
        self.bot.answer_callback_query(callback.id)

    def handle_edit_callbacks(self, callback: CallbackQuery):
        """Обработка callback'ов редактирования"""
        if not self._check_admin_access(callback):
            return
        
        try:
            data = callback.data
            
            if data.startswith('edit_select_category_'):
                category_id = int(data.replace('edit_select_category_', ''))
                self._show_products_for_editing(callback, category_id)
                
            elif data.startswith('edit_product_'):
                product_id = int(data.replace('edit_product_', ''))
                self._show_edit_options(callback, product_id)
                
            elif data.startswith('edit_option_'):
                parts = data.split('_')
                if len(parts) >= 4:
                    product_id = int(parts[2])
                    option = '_'.join(parts[3:])
                    self._start_editing_option(callback, product_id, option)
                else:
                    self.bot.answer_callback_query(callback.id, "❌ Неверный формат callback")

            elif data.startswith('edit_photo_manage_'):
                product_id = int(data.replace('edit_photo_manage_', ''))
                self._show_photo_management(callback, product_id)
                
            elif data == 'edit_back_to_categories':
                self.start_editing(callback)
                
            elif data == 'edit_back_to_categories':
                self.start_editing(callback)
                
            elif data == 'edit_back_to_products':
                user_state = self.states_manager.get_management_state(callback.from_user.id)
                if user_state and 'category_id' in user_state:
                    category_id = user_state.get('category_id')
                    self._show_products_for_editing(callback, category_id)
                else:
                    self.start_editing(callback)
                
            elif data == 'edit_back_to_products_menu':
                self._back_to_products_menu(callback.message)

            elif data.startswith('edit_delete_option_'):
                product_id = int(data.replace('edit_delete_option_', ''))
                self._show_delete_confirmation(callback, product_id)
            
            elif data.startswith('edit_delete_confirm_'):
                product_id = int(data.replace('edit_delete_confirm_', ''))
                self._delete_product(callback, product_id)
                
            elif data.startswith('edit_back_to_options_'):
                product_id = int(data.replace('edit_back_to_options_', ''))
                self._show_edit_options(callback, product_id)
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка в edit callback: {e}", exc_info=True)
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при обработке")

    def handle_edit_states(self, message: Message):
        """Обработка состояний редактирования"""
        user_id = message.from_user.id
        user_state = self.states_manager.get_management_state(user_id)
        
        if not user_state:
            return
        
        state = user_state.get('state')
        product_id = user_state.get('product_id')
        
        if not product_id:
            self.bot.send_message(message.chat.id, "❌ Ошибка: товар не найден")
            return
        
        try:
            if state == 'editing_name':
                self._update_product_name(message, product_id)
                
            elif state == 'editing_description':
                self._update_product_description(message, product_id)
                
            elif state == 'editing_quantity':
                self._update_product_quantity(message, product_id)
                
            elif state == 'editing_price':
                self._update_product_price(message, product_id)
                
            elif state == 'editing_category':
                self._update_product_category(message, product_id)
                
            elif state == 'editing_unit':
                self._update_product_unit(message, product_id)
                
            elif state == 'editing_prepayment':
                self._update_product_prepayment(message, product_id)
                
            elif state == 'editing_availability':
                self._update_product_availability(message, product_id)
                
            elif state == 'editing_add_photo':
                self._add_product_photo(message, product_id)
                
            elif state == 'editing_main_photo':
                self._select_main_photo(message, product_id)
                
        except Exception as e:
            logger.error(f"Ошибка при редактировании: {e}")
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении товара")

    def _show_products_for_editing(self, callback: CallbackQuery, category_id: int):
        """Показать товары категории для редактирования"""
        products = self.db_manager.get_products_by_category(category_id)
        
        if not products:
            self.bot.send_message(
                callback.message.chat.id,
                "📭 В этой категории нет товаров для редактирования.",
                reply_markup=self._create_edit_back_keyboard()
            )
            return
        
        # Сохраняем category_id в состоянии для возврата
        current_state = self.states_manager.get_management_state(callback.from_user.id) or {}
        current_state.update({
            'state': 'editing_category',
            'category_id': category_id
        })
        self.states_manager.set_management_state(callback.from_user.id, current_state)
        
        # Получаем информацию о категории
        categories = self.db_manager.get_all_categories()
        category_name = next((cat['name'] for cat in categories if cat['id'] == category_id), 'Неизвестно')
        
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        for product in products:
            status_emoji = "✅" if product['is_available'] else "❌"
            photo_count = len(self.db_manager.get_product_photos(product['id']))
            keyboard.add(types.InlineKeyboardButton(
                f"{status_emoji} #{product['id']} {product['name']} - {product['price']} руб. 📸 {photo_count}",
                callback_data=f"edit_product_{product['id']}"
            ))
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к категориям",
            callback_data="edit_back_to_categories"
        ))
        
        try:
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"📦 <b>Товары в категории:</b> {category_name}\n\nВыберите товар для редактирования:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except:
            self.bot.send_message(
                callback.message.chat.id,
                f"📦 <b>Товары в категории:</b> {category_name}\n\nВыберите товар для редактирования:",
                parse_mode='HTML',
                reply_markup=keyboard
            )

    def _show_edit_options(self, callback: CallbackQuery, product_id: int):
        """Показать опции редактирования для товара"""
        product = self.db_manager.get_product_by_id(product_id)
        
        if not product:
            self.bot.answer_callback_query(callback.id, "❌ Товар не найден")
            return
        
        # Сохраняем product_id в состоянии
        self.states_manager.set_management_state(callback.from_user.id, {
            'state': 'editing_product',
            'product_id': product_id
        })
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        # Основные опции
        keyboard.add(
            types.InlineKeyboardButton("✏️ Имя", callback_data=f"edit_option_{product_id}_name"),
            types.InlineKeyboardButton("📁 Категория", callback_data=f"edit_option_{product_id}_category")
        )
        keyboard.add(
            types.InlineKeyboardButton("📄 Описание", callback_data=f"edit_option_{product_id}_description"),
            types.InlineKeyboardButton("📏 Единица", callback_data=f"edit_option_{product_id}_unit")
        )
        keyboard.add(
            types.InlineKeyboardButton("⚖️ Количество", callback_data=f"edit_option_{product_id}_quantity"),
            types.InlineKeyboardButton("💰 Цена", callback_data=f"edit_option_{product_id}_price")
        )
        keyboard.add(
            types.InlineKeyboardButton("💳 Оплата", callback_data=f"edit_option_{product_id}_prepayment"),
            types.InlineKeyboardButton("🔄 Доступность", callback_data=f"edit_option_{product_id}_availability")
        )
        
        # Фото опции
        keyboard.add(
            types.InlineKeyboardButton("📸 Работа с фото", callback_data=f"photo_manage_{product_id}"),
            # types.InlineKeyboardButton("🖼️ Выбрать основное", callback_data=f"edit_option_{product_id}_main_photo")
        )
        
        keyboard.add(
            types.InlineKeyboardButton("🗑️ Удалить товар", callback_data=f"edit_delete_option_{product_id}"),
            types.InlineKeyboardButton("🔙 Назад к товарам", callback_data="edit_back_to_products")
        )
        
        product_text = self._format_product_details(product)
        
        # Получаем фотографии товара
        photos = self.db_manager.get_product_photos(product_id)
        
        # keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к товарам",
            callback_data=f"view_back_to_category_{product['category_id']}"
        ))
        keyboard.add(types.InlineKeyboardButton(
            "🔙 В меню",
            callback_data="view_back_products"
        ))
        
        # Если есть фото, отправляем их все в одной медиагруппе
        if photos and any(os.path.exists(p['photo_path']) for p in photos):
            media_group = []
            file_objects = []  # Для отслеживания открытых файлов
            
            try:
                # Сортируем фото: основное первое
                main_photos = [p for p in photos if p.get('is_main')]
                other_photos = [p for p in photos if not p.get('is_main')]
                sorted_photos = main_photos + other_photos
                
                for i, photo_info in enumerate(sorted_photos[:10]):  # Ограничение Telegram
                    if os.path.exists(photo_info['photo_path']):
                        file_obj = open(photo_info['photo_path'], 'rb')
                        file_objects.append(file_obj)
                        
                        if i == 0:  # Первое фото с описанием
                            media_group.append(types.InputMediaPhoto(
                                file_obj,
                                caption=product_text,  # Используем отформатированный текст
                                parse_mode='HTML'
                            ))
                        else:  # Остальные фото без подписи
                            media_group.append(types.InputMediaPhoto(file_obj))
                
                if media_group:
                    # Отправляем медиагруппу
                    self.bot.send_media_group(
                        callback.message.chat.id, 
                        media_group, 
                    )
                    
                    # Отправляем клавиатуру отдельным сообщением
                    self.bot.send_message(
                        callback.message.chat.id,
                        "📸 Все фотографии товара",
                        reply_markup=keyboard
                    )
                    
            except Exception as e:
                logger.error(f"Ошибка отправки медиагруппы: {e}")
                # Fallback: отправляем описание товара
                self.bot.send_message(
                    callback.message.chat.id,
                    text=product_text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            finally:
                # Закрываем все файлы
                for file_obj in file_objects:
                    try:
                        file_obj.close()
                    except:
                        pass
        else:
            # Если фото нет, отправляем просто текст
            self.bot.send_message(
                callback.message.chat.id,
                text=product_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )

        # try:
        #     self.bot.edit_message_text(
        #         chat_id=callback.message.chat.id,
        #         message_id=callback.message.message_id,
        #         text=product_text,
        #         parse_mode='HTML',
        #         reply_markup=keyboard
        #     )
        # except:
        #     self.bot.send_message(
        #         callback.message.chat.id,
        #         product_text,
        #         parse_mode='HTML',
        #         reply_markup=keyboard
        #     )

    def _format_product_details(self, product: dict) -> str:
        """Форматирование детальной информации о товаре"""
        text = "🎂 <b>Информация о товаре</b>\n\n"
        text += f"🆔 <b>ID:</b> {product['id']}\n"
        text += f"📝 <b>Название:</b> {product['name']}\n"
        text += f"📁 <b>Категория:</b> {product['category_name']}\n"
        text += f"📄 <b>Описание:</b> {product['short_description'] or 'Не указано'}\n"
        text += f"🔄 <b>Доступен:</b> {'✅ Да' if product['is_available'] else '❌ Нет'}\n"
        text += f"⚖️ <b>Количество:</b> {product['quantity'] } {product['measurement_unit']}\n"
        text += f"💰 <b>Цена:</b> {product['price']} руб.\n"
        text += f"💳 <b>Условия оплаты:</b> {product['prepayment_conditions'] or 'Не указано'}\n"
        text += f"📅 <b>Создан:</b> {product['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
        text += f"🔄 <b>Обновлен:</b> {product['updated_at'].strftime('%d.%m.%Y %H:%M') if product['updated_at'] else 'Не обновлялся'}\n"
        
        # Информация о фотографиях
        photos = self.db_manager.get_product_photos(product['id'])
        if photos:
            main_photos = [p for p in photos if p['is_main']]
            text += f"\n📸 <b>Фотографии:</b> {len(photos)} шт.\n"
            if main_photos:
                text += f"📌 <b>Основное фото:</b> Установлено\n"
        else:
            text += "\n📸 <b>Фотографии:</b> Нет\n"
        
        return text
    
    def _start_editing_option(self, callback: CallbackQuery, product_id: int, option: str):
        """Начать редактирование конкретной опции"""
        product = self.db_manager.get_product_by_id(product_id)
        
        if not product:
            self.bot.answer_callback_query(callback.id, "❌ Товар не найден")
            return
        
        # Сохраняем состояние редактирования
        self.states_manager.set_management_state(callback.from_user.id, {
            'state': f'editing_{option}',
            'product_id': product_id
        })
        
        messages = {
            'name': "✏️ Введите новое название товара:",
            'category': "📁 Выберите новую категорию:",
            'description': "📄 Введите новое описание товара:",
            'unit': "📏 Выберите новую единицу измерения:",
            'quantity': "⚖️ Введите новое количество товара:",
            'price': "💰 Введите новую цену товара:",
            'prepayment': "💳 Выберите новые условия оплаты:",
            'availability': "🔄 Товар доступен для заказа?",
            'add_photo': "📸 Отправьте новое фото товара:",
            'main_photo': "🖼️ Выберите основное фото:"
        }
        
        if option in ['category', 'unit', 'availability', 'prepayment']:
            # Для этих опций показываем клавиатуру
            if option == 'category':
                keyboard = self._create_categories_keyboard(row_width=2)
            elif option == 'unit':
                keyboard = ProductConstants.create_measurement_units_keyboard()
            elif option == 'availability':
                keyboard = ProductConstants.create_availability_keyboard()
            elif option == 'prepayment':
                keyboard = ProductConstants.create_prepayment_keyboard()
            
            self.bot.send_message(
                callback.message.chat.id,
                messages[option],
                parse_mode='HTML',
                reply_markup=keyboard
            )
        elif option == 'main_photo':
            # Показываем список фото для выбора основного
            photos = self.db_manager.get_product_photos(product_id)
            if not photos:
                self.bot.send_message(callback.message.chat.id, "❌ У товара нет фотографий")
                self._return_to_edit_options(callback.message, product_id)
                return
            
            photos_text = "\n".join([f"{i}. 📸 Фото {i}" for i in range(1, len(photos) + 1)])
            self.bot.send_message(
                callback.message.chat.id,
                f"📸 Выберите <b>главное фото</b>:\n\n{photos_text}",
                parse_mode='HTML',
                reply_markup=self._create_photo_selection_keyboard(photos)
            )
        else:
            # Для текстовых опций
            self.bot.send_message(
                callback.message.chat.id,
                messages[option],
                parse_mode='HTML',
                reply_markup=ProductConstants.create_cancel_keyboard()
            )

    def _check_cancellation(self, message: Message, product_id: int = None) -> bool:
        """Проверка нажатия кнопки отмены"""
        if message.text == "❌ Отмена":
            self._cancel_creation(message, product_id)
            return True
        return False

    def _cancel_creation(self, message: Message, product_id: int = None):
        """Отмена редактирования товара"""
        self.states_manager.clear_management_state(message.from_user.id)
        self.bot.send_message(
            message.chat.id,
            "❌ Редактирование товара отменено.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        # Возвращаем к опциям редактирования только если передан product_id
        if product_id:
            self._back_to_products_menu(message)
   
    # Методы обновления полей товара
    def _update_product_name(self, message: Message, product_id: int):
        """Обновление названия товара"""
        # Проверка на отмену операции
        if self._check_cancellation(message, product_id):
            return

        new_name = message.text
        logger.info(f"Попытка обновления названия товара {product_id} на: {new_name}")
        
        if self.db_manager.update_product_field(product_id, 'name', new_name):
            logger.info(f"Название товара {product_id} успешно обновлено")
            self.states_manager.clear_management_state(message.from_user.id)
            self.bot.send_message(message.chat.id, "✅ Название товара обновлено!")
            self._return_to_edit_options(message, product_id)
        else:
            logger.error(f"Ошибка при обновлении названия товара {product_id}")
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении названия")

    def _update_product_description(self, message: Message, product_id: int):
        """Обновление описания товара"""
        # Проверка на отмену операции
        if self._check_cancellation(message, product_id):
            return

        new_description = message.text
        if self.db_manager.update_product_field(product_id, 'short_description', new_description):
            self.states_manager.clear_management_state(message.from_user.id)
            self.bot.send_message(message.chat.id, "✅ Описание товара обновлено!")
            self._return_to_edit_options(message, product_id)
        else:
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении описания")

    def _update_product_quantity(self, message: Message, product_id: int):
        """Обновление количества товара"""
        # Проверка на отмену операции
        if self._check_cancellation(message, product_id):
            return

        try:
            new_quantity = float(message.text)
            if self.db_manager.update_product_field(product_id, 'quantity', new_quantity):
                self.states_manager.clear_management_state(message.from_user.id)
                self.bot.send_message(message.chat.id, "✅ Количество товара обновлено!")
                self._return_to_edit_options(message, product_id)
            else:
                self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении количества")
        except ValueError:
            self.bot.send_message(message.chat.id, "❌ Введите число для количества")

    def _update_product_price(self, message: Message, product_id: int):
        """Обновление цены товара"""
        # Проверка на отмену операции
        if self._check_cancellation(message, product_id):
            return

        try:
            new_price = float(message.text)
            if self.db_manager.update_product_field(product_id, 'price', new_price):
                self.states_manager.clear_management_state(message.from_user.id)
                self.bot.send_message(message.chat.id, "✅ Цена товара обновлена!")
                self._return_to_edit_options(message, product_id)
            else:
                self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении цены")
        except ValueError:
            self.bot.send_message(message.chat.id, "❌ Введите число для цены")

    def _update_product_category(self, message: Message, product_id: int):
        """Обновление категории товара"""
        # Проверка на отмену операции
        if self._check_cancellation(message, product_id):
            return

        categories = self.db_manager.get_all_categories()
        category_names = [cat['name'].lower() for cat in categories]
        
        if message.text.lower() not in category_names:
            self.bot.send_message(
                message.chat.id,
                "❌ Категория не найдена. Выберите из предложенных:",
                reply_markup=self._create_categories_keyboard()
            )
            return
        
        category_id = next((cat['id'] for cat in categories if cat['name'].lower() == message.text.lower()), None)
        
        if category_id and self.db_manager.update_product_field(product_id, 'category_id', category_id):
            self.states_manager.clear_management_state(message.from_user.id)
            self.bot.send_message(
                message.chat.id, "✅ Категория товара обновлена!",
                reply_markup=types.ReplyKeyboardRemove()
                )
            self._return_to_edit_options(message, product_id)
        else:
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении категории")

    def _update_product_unit(self, message: Message, product_id: int):
        """Обновление единицы измерения"""
        # Проверка на отмену операции
        if self._check_cancellation(message, product_id):
            return

        valid_units = ProductConstants.MEASUREMENT_UNITS
        
        if message.text not in valid_units:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, выберите единицу измерения из предложенных:",
                reply_markup=self._create_measurement_units_keyboard()
            )
            return
        
        if self.db_manager.update_product_field(product_id, 'measurement_unit', message.text):
            self.states_manager.clear_management_state(message.from_user.id)
            self.bot.send_message(
                message.chat.id, "✅ Единица измерения обновлена!",
                reply_markup=types.ReplyKeyboardRemove()
                )
            self._return_to_edit_options(message, product_id)
        else:
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении единицы измерения")

    def _update_product_prepayment(self, message: Message, product_id: int):
        """Обновление условий оплаты"""
        # Проверка на отмену операции
        if self._check_cancellation(message, product_id):
            return

        valid_options = ProductConstants.PREPAYMENT_OPTIONS
        
        if message.text not in valid_options:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, выберите вариант из предложенных:",
                reply_markup=self._create_prepayment_keyboard()
            )
            return
        
        if self.db_manager.update_product_field(product_id, 'prepayment_conditions', message.text):
            self.states_manager.clear_management_state(message.from_user.id)
            self.bot.send_message(
                message.chat.id, "✅ Условия оплаты обновлены!",
                reply_markup=types.ReplyKeyboardRemove())
            self._return_to_edit_options(message, product_id)
        else:
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении условий оплаты")

    def _update_product_availability(self, message: Message, product_id: int):
        """Обновление доступности товара"""
        # Проверка на отмену операции
        if self._check_cancellation(message, product_id):
            return

        if message.text == "✅ Да":
            new_availability = True
        elif message.text == "❌ Нет":
            new_availability = False
        else:
            self.bot.send_message(
                message.chat.id,
                "❌ Пожалуйста, выберите вариант:",
                reply_markup=self._create_availability_keyboard()
            )
            return
        
        if self.db_manager.update_product_field(product_id, 'is_available', new_availability):
            self.states_manager.clear_management_state(message.from_user.id)
            status = "доступен" if new_availability else "не доступен"
            self.bot.send_message(
                message.chat.id, f"✅ Товар теперь {status} для заказа!",
                reply_markup=types.ReplyKeyboardRemove())
            self._return_to_edit_options(message, product_id)
        else:
            self.bot.send_message(message.chat.id, "❌ Ошибка при обновлении доступности")

    def _show_photo_management(self, callback: CallbackQuery, product_id: int):
        """Показать меню управления фото для товара"""
        product = self.db_manager.get_product_by_id(product_id)
        
        if not product:
            self.bot.answer_callback_query(callback.id, "❌ Товар не найден")
            return
        
        # Используем PhotoManager для показа управления фото
        from .photo_manager import PhotoManager
        photo_manager = PhotoManager(self.bot, self.db_manager, self.states_manager, self.photos_dir)
        photo_manager.show_photo_management(callback.message, product_id)
        
        self.bot.answer_callback_query(callback.id)

    # def _add_product_photo(self, message: Message, product_id: int):
    #     """Добавление фото к товару"""
    #     # Проверка на отмену операции
    #     if self._check_cancellation(message, product_id):
    #         return

    #     if message.content_type != 'photo':
    #         self.bot.send_message(message.chat.id, "❌ Пожалуйста, отправьте фото")
    #         return
        
    #     try:
    #         photo_id = message.photo[-1].file_id
    #         photo_path = self._save_photo(photo_id, product_id)
            
    #         if photo_path and self.db_manager.add_product_photo(product_id, photo_path, is_main=False):
    #             self.bot.send_message(message.chat.id, "✅ Фото добавлено к товару!")
    #             self._return_to_edit_options(message, product_id)
    #         else:
    #             self.bot.send_message(message.chat.id, "❌ Ошибка при добавлении фото")
    #     except Exception as e:
    #         logger.error(f"Ошибка при добавлении фото: {e}")
    #         self.bot.send_message(message.chat.id, "❌ Ошибка при обработке фото")

    # def _select_main_photo(self, message: Message, product_id: int):
    #     """Выбор основного фото"""
    #     # Проверка на отмену операции
    #     if self._check_cancellation(message, product_id):
    #         return

    #     photos = self.db_manager.get_product_photos(product_id)
        
    #     if not photos:
    #         self.bot.send_message(message.chat.id, "❌ У товара нет фотографий")
    #         self._return_to_edit_options(message, product_id)
    #         return
        
    #     try:
    #         photo_number = int(message.text)
    #         if 1 <= photo_number <= len(photos):
    #             selected_photo = photos[photo_number - 1]
                
    #             # Устанавливаем выбранное фото как основное
    #             if self.db_manager.set_main_photo(product_id, selected_photo['photo_path']):
    #                 self.bot.send_message(message.chat.id, "✅ Основное фото установлено!")
    #                 self._return_to_edit_options(message, product_id)
    #             else:
    #                 self.bot.send_message(message.chat.id, "❌ Ошибка при установке основного фото")
    #         else:
    #             self.bot.send_message(
    #                 message.chat.id,
    #                 f"❌ Неверный номер. Введите число от 1 до {len(photos)}:",
    #                 reply_markup=self._create_photo_selection_keyboard(photos)
    #             )
    #     except ValueError:
    #         self.bot.send_message(
    #             message.chat.id,
    #             "❌ Пожалуйста, введите номер фото:",
    #             reply_markup=self._create_photo_selection_keyboard(photos)
            # )

    def _show_delete_confirmation(self, callback: CallbackQuery, product_id: int):
        """Показать подтверждение удаления товара"""
        product = self.db_manager.get_product_by_id(product_id)
        
        if not product:
            self.bot.answer_callback_query(callback.id, "❌ Товар не найден")
            return
        
        product_text = self._format_product_details(product)
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("✅ Да, удалить", callback_data=f"edit_delete_confirm_{product_id}"),
            types.InlineKeyboardButton("❌ Нет, отменить", callback_data=f"edit_back_to_options_{product_id}")
        )
        
        try:
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"🗑️ <b>Подтверждение удаления товара</b>\n\n{product_text}\n\n"
                    "Вы действительно хотите удалить этот товар?",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except:
            self.bot.send_message(
                callback.message.chat.id,
                f"🗑️ <b>Подтверждение удаления товара</b>\n\n{product_text}\n\n"
                "Вы действительно хотите удалить этот товар?",
                parse_mode='HTML',
                reply_markup=keyboard
            )

    def _delete_product(self, callback: CallbackQuery, product_id: int):
        """Удаление товара"""
        try:
            product = self.db_manager.get_product_by_id(product_id)
            
            if not product:
                self.bot.answer_callback_query(callback.id, "❌ Товар не найден")
                return
            
            # 1. Удаляем фотографии товара с диска
            photos = self.db_manager.get_product_photos(product_id)
            for photo in photos:
                try:
                    if os.path.exists(photo['photo_path']):
                        os.remove(photo['photo_path'])
                except Exception as e:
                    logger.error(f"Ошибка при удалении фото: {e}")
            
            # 2. Удаляем папку товара
            product_dir = os.path.join(self.photos_dir, str(product_id))
            try:
                if os.path.exists(product_dir):
                    import shutil
                    shutil.rmtree(product_dir)
            except Exception as e:
                logger.error(f"Ошибка при удалении папки товара: {e}")
            
            # 3. Удаляем товар из базы данных
            if self.db_manager.delete_product(product_id):
                try:
                    self.bot.delete_message(callback.message.chat.id, callback.message.message_id)
                except:
                    pass
                    
                self.bot.send_message(
                    callback.message.chat.id,
                    f"✅ Товар '{product['name']}' успешно удален!"
                )
                
                # Возвращаемся к списку товаров категории
                user_state = self.states_manager.get_management_state(callback.from_user.id)
                if user_state and 'category_id' in user_state:
                    category_id = user_state.get('category_id')
                    self._show_products_for_editing(callback, category_id)
                else:
                    self.start_editing(callback)
            else:
                self.bot.answer_callback_query(callback.id, "❌ Ошибка при удалении из базы данных")
                        
        except Exception as e:
            logger.error(f"Ошибка при удалении товара: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при удалении")

    def _return_to_edit_options(self, message: Message, product_id: int):
        """Вернуться к опциям редактирования после изменения"""
        self.states_manager.clear_management_state(message.from_user.id)
        
        product = self.db_manager.get_product_by_id(product_id)
        
        if not product:
            self.bot.send_message(message.chat.id, "❌ Товар не найден")
            self._back_to_products_menu(message)
            return
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        keyboard.add(
            types.InlineKeyboardButton("✏️ Имя", callback_data=f"edit_option_{product_id}_name"),
            types.InlineKeyboardButton("📁 Категория", callback_data=f"edit_option_{product_id}_category")
        )
        keyboard.add(
            types.InlineKeyboardButton("📄 Описание", callback_data=f"edit_option_{product_id}_description"),
            types.InlineKeyboardButton("📏 Единица", callback_data=f"edit_option_{product_id}_unit")
        )
        keyboard.add(
            types.InlineKeyboardButton("⚖️ Количество", callback_data=f"edit_option_{product_id}_quantity"),
            types.InlineKeyboardButton("💰 Цена", callback_data=f"edit_option_{product_id}_price")
        )
        keyboard.add(
            types.InlineKeyboardButton("💳 Оплата", callback_data=f"edit_option_{product_id}_prepayment"),
            types.InlineKeyboardButton("🔄 Доступность", callback_data=f"edit_option_{product_id}_availability")
        )
        
        keyboard.add(
            types.InlineKeyboardButton("📸 Работа с фото", callback_data=f"photo_manage_{product_id}")
            # types.InlineKeyboardButton("📸 Добавить фото", callback_data=f"edit_option_{product_id}_add_photo"),
            # types.InlineKeyboardButton("🖼️ Выбрать основное", callback_data=f"edit_option_{product_id}_main_photo")
        )
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к товарам",
            callback_data="edit_back_to_products"
        ))
        
        product_text = self._format_product_details(product)
        
        # Получаем фотографии товара
        photos = self.db_manager.get_product_photos(product_id)
        
        # keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к товарам",
            callback_data=f"view_back_to_category_{product['category_id']}"
        ))
        keyboard.add(types.InlineKeyboardButton(
            "🔙 В меню",
            callback_data="view_back_products"
        ))
        
        # Если есть фото, отправляем их все в одной медиагруппе
        if photos and any(os.path.exists(p['photo_path']) for p in photos):
            media_group = []
            file_objects = []  # Для отслеживания открытых файлов
            
            try:
                # Сортируем фото: основное первое
                main_photos = [p for p in photos if p.get('is_main')]
                other_photos = [p for p in photos if not p.get('is_main')]
                sorted_photos = main_photos + other_photos
                
                for i, photo_info in enumerate(sorted_photos[:10]):  # Ограничение Telegram
                    if os.path.exists(photo_info['photo_path']):
                        file_obj = open(photo_info['photo_path'], 'rb')
                        file_objects.append(file_obj)
                        
                        if i == 0:  # Первое фото с описанием
                            media_group.append(types.InputMediaPhoto(
                                file_obj,
                                caption=product_text,  # Используем отформатированный текст
                                parse_mode='HTML'
                            ))
                        else:  # Остальные фото без подписи
                            media_group.append(types.InputMediaPhoto(file_obj))
                
                if media_group:
                    # Отправляем медиагруппу
                    self.bot.send_media_group(
                        message.chat.id, 
                        media_group, 
                    )
                    
                    # Отправляем клавиатуру отдельным сообщением
                    self.bot.send_message(
                        message.chat.id,
                        "📸 Все фотографии товара",
                        reply_markup=keyboard
                    )
                    
            except Exception as e:
                logger.error(f"Ошибка отправки медиагруппы: {e}")
                # Fallback: отправляем описание товара
                self.bot.send_message(
                    message.chat.id,
                    text=product_text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            finally:
                # Закрываем все файлы
                for file_obj in file_objects:
                    try:
                        file_obj.close()
                    except:
                        pass
        else:
            # Если фото нет, отправляем просто текст
            self.bot.send_message(
                message.chat.id,
                text=product_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )

    # Вспомогательные методы
    def _check_admin_access(self, callback: CallbackQuery = None, message: Message = None) -> bool:
        """Проверка прав администратора"""
        # Эта функция должна быть реализована в основном классе
        # Здесь возвращаем True для совместимости
        return True

    def _save_photo(self, photo_file_id: str, product_id: int) -> str:
        """Сохранение фото на диск"""
        import uuid
        try:
            file_info = self.bot.get_file(photo_file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            file_extension = os.path.splitext(file_info.file_path)[1] or '.jpg'
            filename = f"{uuid.uuid4().hex}{file_extension}"
            
            product_dir = os.path.join(self.photos_dir, str(product_id))
            os.makedirs(product_dir, exist_ok=True)
            filepath = os.path.join(product_dir, filename)
            
            with open(filepath, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            return filepath if os.path.exists(filepath) else None
                
        except Exception as e:
            logger.error(f"Ошибка при сохранении фото: {e}")
            return None

    def _back_to_products_menu(self, message: Message):
        """Возврат в меню продукции"""
        from ..shared.product_constants import ProductConstants
        self.bot.send_message(
            message.chat.id,
            ProductConstants.PRODUCT_MANAGEMENT_TITLE,
            reply_markup=ProductConstants.create_management_keyboard(),
            parse_mode='HTML'
        )

    # Методы создания клавиатур

    def _create_categories_keyboard(self, row_width: int=2):
        """Создание клавиатуры с категориями для выбора"""
        categories = self.db_manager.get_all_categories()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        
        buttons = []
        for category in categories:
            buttons.append(types.KeyboardButton(category['name']))
        
        for i in range(0, len(buttons), row_width):
                    row_buttons = buttons[i:i + row_width]
                    keyboard.add(*row_buttons)
        
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard

    # def _create_measurement_units_keyboard(self):
    #     """Создание клавиатуры с единицами измерения"""
    #     keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    #     units = ['шт', 'кг', 'г', 'л', 'мл', 'уп', 'пачка', 'упаковка', 'набор']
        
    #     for unit in units:
    #         keyboard.add(types.KeyboardButton(unit))
        
    #     keyboard.add(types.KeyboardButton("❌ Отмена"))
    #     return keyboard

    # def _create_availability_keyboard(self):
    #     """Создание клавиатуры с опциями доступности"""
    #     keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    #     keyboard.add(
    #         types.KeyboardButton("✅ Да"),
    #         types.KeyboardButton("❌ Нет")
    #     )
    #     keyboard.add(types.KeyboardButton("❌ Отмена"))
    #     return keyboard

    # def _create_prepayment_keyboard(self):
    #     """Создание клавиатуры с условиями оплаты"""
    #     keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    #     options = ["50% предоплата", "100% предоплата", "Постоплата"]
        
    #     for option in options:
    #         keyboard.add(types.KeyboardButton(option))
        
    #     keyboard.add(types.KeyboardButton("❌ Отмена"))
    #     return keyboard

    def _create_photo_selection_keyboard(self, photos):
        """Создание клавиатуры для выбора фото"""
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        
        for i in range(1, len(photos) + 1):
            keyboard.add(types.KeyboardButton(str(i)))
        
        keyboard.add(types.KeyboardButton("❌ Отмена"))
        return keyboard

    # def _create_cancel_edit_keyboard(self):
    #     """Создание клавиатуры для отмены редактирования"""
    #     keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    #     keyboard.add(types.KeyboardButton("❌ Отмена"))
    #     return keyboard

    def _create_edit_back_keyboard(self):
        """Создание клавиатуры для возврата"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="edit_back_to_categories"))
        return keyboard

    def _create_back_to_products_keyboard(self):
        """Создание клавиатуры для возврата к продукции"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="edit_back_to_products_menu"))
        return keyboard