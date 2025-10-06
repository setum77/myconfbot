# product_viewer.py
import logging
import os
from telebot import types
from telebot.types import Message, CallbackQuery
from ..shared.product_constants import ProductConstants

logger = logging.getLogger(__name__)

class ProductViewer:
    """Обработчик просмотра продукции"""
    
    def __init__(self, bot, db_manager, photos_dir):
        self.bot = bot
        self.db_manager = db_manager
        self.photos_dir = photos_dir

    def start_viewing(self, message: Message):
        """Начало просмотра - выбор категории"""
        self._view_products(message)

    def handle_view_callbacks(self, callback: CallbackQuery):
        """Обработка callback'ов просмотра"""
        try:
            data = callback.data
            
            if data.startswith('view_category_'):
                category_id = int(data.replace('view_category_', ''))
                self._handle_view_category(callback, category_id)
                
            elif data.startswith('view_product_'):
                product_id = int(data.replace('view_product_', ''))
                self._handle_view_product(callback, product_id)
                
            elif data.startswith('view_back_'):
                self._handle_view_back(callback)
                
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка в view callback: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при обработке")

    def _view_products(self, message: Message):
        """Просмотр товаров - выбор категории"""
        categories = self.db_manager.get_all_categories()
        
        if not categories:
            self.bot.send_message(
                message.chat.id,
                "📭 Нет доступных категорий.",
                reply_markup=self._create_back_to_products_keyboard()
            )
            return
        
        # ИСПРАВЛЕНИЕ: Используем InlineKeyboardMarkup вместо ReplyKeyboardMarkup
        keyboard = ProductConstants.create_categories_keyboard_inline(
            categories=categories,
            db_manager=self.db_manager,
            back_callback="view_back_products"
        )
        
        self.bot.send_message(
            message.chat.id,
            "📂 <b>Просмотр товаров</b>\n\nВыберите категорию:",
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def _handle_view_category(self, callback: CallbackQuery, category_id: int):
        """Обработка выбора категории для просмотра"""
        products = self.db_manager.get_products_by_category(category_id)
        
        if not products:
            self.bot.send_message(
                callback.message.chat.id,
                "📭 В этой категории нет товаров.",
                reply_markup=self._create_back_to_categories_keyboard()
            )
            return
        
        # Получаем информацию о категории
        categories = self.db_manager.get_all_categories()
        category_name = next((cat['name'] for cat in categories if cat['id'] == category_id), 'Неизвестно')
        
        # keyboard = ProductConstants.create_product_details_keyboard_inline(
        #     product=product,
        #     db_manager=self.db_manager,
        #     back_callback="view_back_categories"
        # )
        keyboard = types.InlineKeyboardMarkup()
        
        for product in products:
            # Получаем количество фотографий для товара
            photos_count = len(self.db_manager.get_product_photos(product['id']))
            status_emoji = "✅" if product['is_available'] else "❌"
            keyboard.add(types.InlineKeyboardButton(
                f"{status_emoji} {product['name']} - {product['price']} руб. 📸 {photos_count}",
                callback_data=f"view_product_{product['id']}"
            ))
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к категориям",
            callback_data="view_back_categories"
        ))
        
        try:
            self.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=f"📂 <b>Товары в категории:</b> {category_name}\n\nВыберите товар:",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except:
            self.bot.send_message(
                callback.message.chat.id,
                f"📂 <b>Товары в категории:</b> {category_name}\n\nВыберите товар:",
                parse_mode='HTML',
                reply_markup=keyboard
            )

    def _handle_view_product(self, callback: CallbackQuery, product_id: int):
        """Обработка просмотра - все фото в одной медиагруппе"""
        product = self.db_manager.get_product_by_id(product_id)
        
        if not product:
            self.bot.answer_callback_query(callback.id, "❌ Товар не найден")
            return
        
        # Форматируем информацию о товаре
        product_text = self._format_product_details(product)
        
        # Получаем фотографии товара
        photos = self.db_manager.get_product_photos(product_id)
        
        keyboard = types.InlineKeyboardMarkup()
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
                    self.bot.send_media_group(callback.message.chat.id, media_group)
                    
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
                    product_text,
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
                product_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        
        self.bot.answer_callback_query(callback.id)

    def _handle_view_back(self, callback: CallbackQuery):
        """Обработка кнопки назад при просмотре"""
        try:
            data = callback.data
            
            if data == 'view_back_products':
                # Возврат в меню управления продукцией
                from ..shared.product_constants import ProductConstants
                # Нужно будет передать управление обратно в основной класс
                self.bot.send_message(
                    callback.message.chat.id,
                    ProductConstants.PRODUCT_MANAGEMENT_TITLE,
                    reply_markup=ProductConstants.create_management_keyboard(),
                    parse_mode='HTML'
                )
                
            elif data == 'view_back_categories':
                # Возврат к списку категорий
                self._view_products(callback.message)
                
            elif data.startswith('view_back_to_category_'):
                # Возврат к товарам конкретной категории
                category_id = int(data.replace('view_back_to_category_', ''))
                self._show_products_in_category(callback.message, category_id)
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке назад: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка")

    def _show_products_in_category(self, message: Message, category_id: int):
        """Показать товары в категории"""
        products = self.db_manager.get_products_by_category(category_id)
        categories = self.db_manager.get_all_categories()
        category_name = next((cat['name'] for cat in categories if cat['id'] == category_id), 'Неизвестно')
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        
        for product in products:
            photos_count = len(self.db_manager.get_product_photos(product['id']))
            status_emoji = "✅" if product['is_available'] else "❌"
            keyboard.add(types.InlineKeyboardButton(
                f"{status_emoji} {product['name']} - {product['price']} руб. 📸 {photos_count}",
                callback_data=f"view_product_{product['id']}"
            ))
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к категориям",
            callback_data="view_back_categories"
        ))
        
        self.bot.send_message(
            message.chat.id,
            f"📂 <b>Товары в категории:</b> {category_name}\n\nВыберите товар:",
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def _format_product_details(self, product: dict) -> str:
        """Форматирование детальной информации о товаре (ТОЛЬКО текст)"""
        
        product_text = "🎂 <b>Информация о товаре</b>\n\n"
        product_text += f"🆔 <b>ID:</b> {product['id']}\n"
        product_text += f"📝 <b>Название:</b> {product['name']}\n"
        product_text += f"📁 <b>Категория:</b> {product['category_name']}\n"
        product_text += f"📄 <b>Описание:</b> {product['short_description'] or 'Не указано'}\n"
        product_text += f"🔄 <b>Доступен:</b> {'✅ Да' if product['is_available'] else '❌ Нет'}\n"
        product_text += f"⚖️ <b>Количество:</b> {product['quantity']} {product['measurement_unit']}\n"
        product_text += f"💰 <b>Цена:</b> {product['price']} руб.\n"
        product_text += f"💳 <b>Условия оплаты:</b> {product['prepayment_conditions'] or 'Не указано'}\n"
        product_text += f"📅 <b>Создан:</b> {product['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
        product_text += f"🔄 <b>Обновлен:</b> {product['updated_at'].strftime('%d.%m.%Y %H:%M') if product['updated_at'] else 'Не обновлялся'}\n"
        
        # Информация о фотографиях
        photos = self.db_manager.get_product_photos(product['id'])
        if photos:
            product_text += f"\n📸 <b>Фотографии:</b> {len(photos)} шт.\n"
        else:
            product_text += "\n📸 <b>Фотографии:</b> Нет\n"
        
        return product_text

    def _create_back_to_products_keyboard(self):
        """Клавиатура для возврата к управлению продукцией"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "🔙 В меню продукции",
            callback_data="view_back_products"
        ))
        return keyboard

    def _create_back_to_categories_keyboard(self):
        """Клавиатура для возврата к категориям"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "🔙 К категориям",
            callback_data="view_back_categories"
        ))
        return keyboard
    
    def show_product_summary(self, message: Message, product_id: int):
        """Показать сводную информацию о товаре (для использования в других модулях)"""
        
        product = self.db_manager.get_product_by_id(product_id)
        
        print(f'Выводим информацию о продукте {product['name']}')
        
        if not product:
            self.bot.send_message(message.chat.id, "❌ Товар не найден")
            return
        
        # Форматируем информацию о товаре
        product_text = self._format_product_details(product)
        
        # Получаем фотографии товара
        photos = self.db_manager.get_product_photos(product_id)
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("🔙 В меню продукции",
            callback_data=f"view_back_products"))
        
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
                                caption=product_text,
                                parse_mode='HTML'
                            ))
                        else:  # Остальные фото без подписи
                            media_group.append(types.InputMediaPhoto(file_obj))
                
                if media_group:
                    # Отправляем медиагруппу. Нужно будет реализовать в случае если фотографий >10
                    self.bot.send_media_group(message.chat.id, media_group)
                    
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
                    product_text,
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
                product_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        
        # self.bot.answer_callback_query(callback.id)