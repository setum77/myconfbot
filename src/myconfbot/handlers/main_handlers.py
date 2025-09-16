import os
import logging
from PIL import Image
import io
from telebot import types
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

#from src.myconfbot.models import Customer, Admin, CustomerCharacteristic
from src.myconfbot.models import Base, Order, Product, Category, OrderStatus, User
from src.myconfbot.utils.database import db_manager
from src.myconfbot.config import Config
from src.myconfbot.utils.content_manager import content_manager

def register_main_handlers(bot):
    
    # Создаем директорию для пользовательских данных
    os.makedirs('data/users', exist_ok=True)
    
    # Словарь для хранения состояния пользователей
    user_states = {}
    
    def is_user_admin(telegram_id):
        """Проверка, является ли пользователь администратором"""
        # try:
        #     config = Config.load()
        #     return telegram_id in config.admin_ids
        # except Exception as e:
        #     logging.error(f"Ошибка при проверке администратора: {e}")
        #     return False
        try:
            user = db_manager.get_user_by_telegram_id(telegram_id)
            if user:
                # Получаем значение атрибута ДО закрытия сессии
                #print(f"DEBUG: User {telegram_id} is_admin = {user.is_admin}") # Отладочная информация
                return user.is_admin
            #print(f"DEBUG: User {telegram_id} not found") # Отладочная информация
            return False

        except Exception as e:
            logging.error(f"Ошибка при проверке администратора: {e}")
            return False
    
    def show_main_menu(chat_id, is_admin=False):
        """Показывает главное меню с reply-кнопками"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        
        # Базовые кнопки для всех пользователей
        buttons = [
            '🎂 Сделать заказ',
            '📖 Рецепты', 
            '💼 Услуги',
            '📞 Контакты',
            '🐱 Мой профиль'
        ]
        
        # Добавляем кнопки администратора
        if is_admin:
            buttons.extend([
                '📦 Заказы',
                '📊 Статистика',
                '🏪 Управление'
            ])
        
        markup.add(*[types.KeyboardButton(btn) for btn in buttons])
        
        # welcome_text = "🎂 Главное меню\nВыберите действие:" # За не надобностью закоментировал
        # bot.send_message(chat_id, welcome_text, reply_markup=markup)
        # bot.send_message(chat_id, "🎂 ", reply_markup=markup)
        return markup
    
    @bot.message_handler(commands=['start', 'help'])
    def handle_start(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        full_name = message.from_user.first_name
        username = message.from_user.username
        
        try:
            config = Config.load()
            config_is_admin = user_id in config.admin_ids
            
            #is_admin = is_user_admin(user_id)
            
            # Проверяем, есть ли пользователь в базе
            # customer = db_manager.get_customer_by_telegram_id(user_id)
            # admin = db_manager.get_admin_by_telegram_id(user_id) if is_admin else None
            # Проверяем, есть ли пользователь в базе
            user = db_manager.get_user_by_telegram_id(user_id)

            if user:
                # Получаем значения атрибутов ДО любых операций с сессией
                user_name = user.full_name
                user_is_admin = user.is_admin
                
                
                # Пользователь уже в базе
                status = "администратор" if user.is_admin else "клиент"
                bot.send_message(chat_id, f"С возвращением, {user.full_name}! 👋\nРады снова видеть. Ваш статус: {status}!")
                #show_main_menu(chat_id, user.is_admin)
                bot.send_message(chat_id, "Главное меню", reply_markup=show_main_menu(chat_id, user_is_admin))
            else:                
                # Создаем пользователя
                db_manager.add_user(
                    telegram_id=user_id,
                    full_name=full_name,
                    telegram_username=username,
                    is_admin=config_is_admin
                )

                # Получаем созданного пользователя
                user = db_manager.get_user_by_telegram_id(user_id)
                
                if user:
                    if config_is_admin:
                        bot.send_message(chat_id, "Добро пожаловать, администратор! 👑")
                        bot.send_message(chat_id, "Пожалуйста, укажите ваш телефонный номер:")
                        user_states[user_id] = {'state': 'awaiting_phone'}
                    else:
                        bot.send_message(chat_id, f"Приятно познакомиться, {full_name}! 😊")
                        bot.send_message(chat_id, "Главное меню", reply_markup=show_main_menu(chat_id, False))
                else:
                    bot.send_message(chat_id, "❌ Ошибка при создании профиля. Попробуйте еще раз.")
            
            # Загрузка приветственного текста
            welcome_text = content_manager.get_content('welcome.md')
            if not welcome_text:
                welcome_text = "Добро пожаловать\\! Я бот\\-помощник мастера кондитера\\!"
            
            try:
                bot.send_message(chat_id, welcome_text, parse_mode='MarkdownV2')
            except Exception as e:
                if "400" in str(e) and "parse entities" in str(e):
                    # Ошибка форматирования - отправляем как plain text
                    error_msg = "⚠️ Ошибка форматирования текста. Отображаю как обычный текст."
                    bot.send_message(chat_id, error_msg)
                    bot.send_message(chat_id, welcome_text)  # plain text
                    logging.warning(f"Ошибка MarkdownV2 форматирования: {e}")
                else:
                    # Другая ошибка
                    bot.send_message(chat_id, "Произошла ошибка при загрузке приветствия.")
                    logging.error(f"Ошибка отправки сообщения: {e}")
                            
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка. Попробуйте позже.")
            logging.error(f"Ошибка при обработке /start: {e}")
    
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'awaiting_name')
    def handle_name_input(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        name = message.text.strip()
        
        user_state = user_states.get(user_id, {})
        is_admin = user_state.get('is_admin', False)
        username = user_state.get('username')
        
        if len(name) < 2:
            bot.send_message(chat_id, "Пожалуйста, введите настоящее имя (минимум 2 символа).")
            return
        
        try:
            
            db_manager.add_user(
                telegram_id=user_id,
                full_name=name,  # используем full_name вместо first_name
                telegram_username=username,
                is_admin=is_admin
            )
            # if is_admin:
            #     # Для администратора запрашиваем дополнительные данные
            #     db_manager.add_admin(
            #         telegram_id=user_id,
            #         first_name=name,
            #         username=username
            #     )
            #     user_states[user_id]['state'] = 'awaiting_phone'
            #     user_states[user_id]['name'] = name
            #     bot.send_message(chat_id, "Отлично! Теперь укажите ваш телефонный номер:")
            # else:
            #     # Для клиента просто сохраняем
            #     db_manager.add_customer(
            #         telegram_id=user_id,
            #         first_name=name,
            #         username=username
            #     )
            user_states.pop(user_id, None)
            bot.send_message(chat_id, f"Приятно познакомиться, {name}! 😊")
            # show_main_menu(chat_id, False) # переход на постгре
            bot.send_message(chat_id, "Главное меню", reply_markup=show_main_menu(chat_id, False))
                
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка при сохранении. Попробуйте еще раз.")
            logging.error(f"Ошибка при сохранении: {e}")
    
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'awaiting_phone')
    def handle_phone_input(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        phone = message.text.strip()
        
        user_state = user_states.get(user_id, {})
        name = user_state.get('name')
        
        # Простая валидация телефона
        if not any(char.isdigit() for char in phone) or len(phone) < 5:
            bot.send_message(chat_id, "Пожалуйста, введите корректный телефонный номер.")
            return
        
        try:
            user_states[user_id]['state'] = 'awaiting_address'
            user_states[user_id]['phone'] = phone
            bot.send_message(chat_id, "Отлично! Теперь укажите ваш адрес:")
                
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка. Попробуйте еще раз.")
            logging.error(f"Ошибка при обработке телефона: {e}")
    
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'awaiting_address')
    def handle_address_input(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        address = message.text.strip()
        
        user_state = user_states.get(user_id, {})
        name = user_state.get('name')
        phone = user_state.get('phone')
        username = user_state.get('username')
        
        if len(address) < 5:
            bot.send_message(chat_id, "Пожалуйста, введите полный адрес.")
            return
        
        try:
            # Обновляем администратора с полными данными
            db_manager.update_user_info(user_id, phone=phone, address=address)
            user_states.pop(user_id, None)
            
            bot.send_message(
                chat_id, 
                f"Отлично, {name}! 👑\n"
                f"Ваши данные сохранены. Теперь вы можете управлять кондитерской!"
            )
            # show_main_menu(chat_id, True) # переход на постгре
            bot.send_message(chat_id, "Главное меню", reply_markup=show_main_menu(chat_id, True))
                
        except Exception as e:
            bot.send_message(chat_id, "Произошла ошибка при сохранении. Попробуйте еще раз.")
            logging.error(f"Ошибка при сохранении адреса: {e}")
    
    @bot.message_handler(commands=['menu'])
    def show_menu(message):
        """Показывает главное меню"""
        user_id = message.from_user.id
        is_admin = is_user_admin(user_id)
        #show_main_menu(message.chat.id, is_admin) # переход на постгре
        bot.send_message(message.chat.id, "Главное меню", reply_markup=show_main_menu(message.chat.id, is_admin))
    
    @bot.message_handler(func=lambda message: message.text == '🐱 Мой профиль')
    def show_my_profile(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        try:
            user_info = db_manager.get_user_by_telegram_id(user_id)

            # Отладочная информация
            # print(f"DEBUG: User ID {user_id}")
            # print(f"DEBUG: User found: {user_info is not None}")
            # if user_info:
            #     print(f"DEBUG: User data: {user_info.__dict__}")
            
            # if not user_info:
            #     bot.send_message(chat_id, "❌ Профиль не найден. Попробуйте /start")
            #     return            

            # Формируем сообщение с профилем
            profile_text = f"👤 *Ваш профиль*\n\n"
            profile_text += f"📛 *Имя:* {user_info.full_name or 'Не указано'}\n"
            profile_text += f"📱 *Username:* @{user_info.telegram_username or 'Не указан'}\n"
            profile_text += f"📞 *Телефон:* {user_info.phone or 'Не указан'}\n"
            profile_text += f"📍 *Адрес:* {user_info.address or 'Не указан'}\n"
            profile_text += f"🎭 *Статус:* {'👑 Администратор' if user_info.is_admin else '👤 Клиент'}\n"
            
            # Создаем клавиатуру для редактирования
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton("✏️ Изменить имя", callback_data="edit_profile_name"),
                types.InlineKeyboardButton("📞 Изменить телефон", callback_data="edit_profile_phone")
            )
            keyboard.add(
                types.InlineKeyboardButton("📍 Изменить адрес", callback_data="edit_profile_address"),
                types.InlineKeyboardButton("📷 Изменить фото", callback_data="edit_profile_photo")
            )
            
            # Отправляем фото если есть
            if user_info.photo_path and os.path.exists(user_info.photo_path):
                try:
                    with open(user_info.photo_path, 'rb') as photo:
                        bot.send_photo(chat_id, photo, caption=profile_text, 
                                    parse_mode='Markdown', reply_markup=keyboard)
                except Exception as e:
                    bot.send_message(chat_id, profile_text, parse_mode='Markdown', reply_markup=keyboard)
                    bot.send_message(chat_id, "❌ Не удалось загрузить фото профиля")
            else:
                # Отправляем placeholder вместо фото
                placeholder_text = "🖼️ Фотография не добавлена"
                bot.send_message(chat_id, profile_text, parse_mode='Markdown', reply_markup=keyboard)
                bot.send_message(chat_id, placeholder_text)
                
        except Exception as e:
            logging.error(f"Ошибка при показе профиля: {e}")
            bot.send_message(chat_id, "❌ Ошибка при загрузке профиля")
                
    
    # Обработчики для администраторских кнопок
    @bot.message_handler(func=lambda message: message.text in ['📦 Заказы', '📊 Статистика', '🏪 Управление'])
    def handle_admin_buttons(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not is_user_admin(user_id):
            bot.send_message(chat_id, "❌ У вас нет прав администратора.")
            return
        
        # Используем inline-кнопки для административных функций
        if message.text == '📦 Заказы':
            show_orders_management(message)
        elif message.text == '📊 Статистика':
            show_statistics(message)
        elif message.text == '🏪 Управление':
            show_management_panel(message)
    
    def show_orders_management(message):
        """Показывает управление заказами через inline-кнопки"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("📋 Активные заказы", callback_data="admin_orders_active"),
            types.InlineKeyboardButton("📊 Все заказы", callback_data="admin_orders_all")
        )
        keyboard.add(
            types.InlineKeyboardButton("🔄 Изменить статус", callback_data="admin_orders_change_status"),
            types.InlineKeyboardButton("📈 Статистика заказов", callback_data="admin_orders_stats")
        )
        
        bot.send_message(
            message.chat.id,
            "📦 Управление заказами\nВыберите действие:",
            reply_markup=keyboard
        )
    
    def show_statistics(message):
        """Показывает статистику через inline-кнопки"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("📊 Общая статистика", callback_data="admin_stats_general"),
            types.InlineKeyboardButton("💰 Финансовая", callback_data="admin_stats_financial")
        )
        keyboard.add(
            types.InlineKeyboardButton("👥 Клиентская", callback_data="admin_stats_clients"),
            types.InlineKeyboardButton("🎂 Товарная", callback_data="admin_stats_products")
        )
        
        bot.send_message(
            message.chat.id,
            "📊 Статистика\nВыберите раздел:",
            reply_markup=keyboard
        )
    
    def show_management_panel(message):
        """Показывает панель управления через inline-кнопки"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("🎂 Продукция", callback_data="admin_manage_products"),
            types.InlineKeyboardButton("📖 Рецепты", callback_data="admin_manage_recipes")
        )
        keyboard.add(
            types.InlineKeyboardButton("💼 Услуги", callback_data="admin_manage_services"),
            types.InlineKeyboardButton("📞 Контакты", callback_data="admin_manage_contacts")
        )
        keyboard.add(
            types.InlineKeyboardButton("📄 Контент", callback_data="admin_manage_content"),
            types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_manage_users")
        )
        
        bot.send_message(
            message.chat.id,
            "🏪 Панель управления\nВыберите раздел:",
            reply_markup=keyboard
        )
    
    # Базовые обработчики для клиентов
    @bot.message_handler(func=lambda message: message.text == '📞 Контакты')
    def send_contacts(message):
        # contacts_text = """
        # 📍 Наш адрес: ул. Кондитерская, 15
        # 📞 Телефон: +7 (999) 123-45-67
        # 🕒 Время работы: 9:00 - 21:00
        # 📧 Email: master@myconfbot.ru
        
        # Мы всегда рады вашим вопросам и заказам! 🎂
        # """
        # bot.send_message(message.chat.id, contacts_text)
        contacts_text = content_manager.get_content('contacts.md')
        if not contacts_text:
            contacts_text = "Контактная информация пока не добавлена"
                
        try:
            bot.send_message(message.chat.id, contacts_text, parse_mode='MarkdownV2')
        except Exception as e:
            if "400" in str(e) and "parse entities" in str(e):
                # Ошибка форматирования - отправляем как plain text
                error_msg = "⚠️ Ошибка форматирования текста. Отображаю как обычный текст."
                bot.send_message(message.chat.id, error_msg)
                bot.send_message(message.chat.id, contacts_text)  # plain text
                logging.warning(f"Ошибка MarkdownV2 форматирования: {e}")
            else:
                # Другая ошибка
                bot.send_message(message.chat.id, "Произошла ошибка при загрузке приветствия.")
                logging.error(f"Ошибка отправки сообщения: {e}")
    
    @bot.message_handler(func=lambda message: message.text == '💼 Услуги')
    def send_services(message):
        # Загрузка текста описывающего услуги
        services_text = content_manager.get_content('services.md')
        if not services_text:
            services_text = "🎁 Информация по услугам пока не добавлена"
                
        try:
            bot.send_message(message.chat.id, services_text, parse_mode='MarkdownV2')
        except Exception as e:
            if "400" in str(e) and "parse entities" in str(e):
                # Ошибка форматирования - отправляем как plain text
                error_msg = "⚠️ Ошибка форматирования текста. Отображаю как обычный текст."
                bot.send_message(message.chat.id, error_msg)
                bot.send_message(message.chat.id, services_text)  # plain text
                logging.warning(f"Ошибка MarkdownV2 форматирования: {e}")
            else:
                # Другая ошибка
                bot.send_message(message.chat.id, "Произошла ошибка при загрузке приветствия.")
                logging.error(f"Ошибка отправки сообщения: {e}")
    
    @bot.message_handler(func=lambda message: message.text == '📖 Рецепты')
    def show_recipes(message):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("🍰 Торты", callback_data="recipes_cakes"),
            types.InlineKeyboardButton("🧁 Капкейки", callback_data="recipes_cupcakes")
        )
        keyboard.add(
            types.InlineKeyboardButton("🍪 Печенье", callback_data="recipes_cookies"),
            types.InlineKeyboardButton("🎂 Сезонные", callback_data="recipes_seasonal")
        )
        
        bot.send_message(
            message.chat.id,
            "📖 Наши рецепты\nВыберите категорию:",
            reply_markup=keyboard
        )
    
    # Обработчики callback для редактирования профиля
    @bot.callback_query_handler(func=lambda call: call.data.startswith('edit_profile_'))
    def handle_profile_edit(callback: CallbackQuery):
        user_id = callback.from_user.id
        chat_id = callback.message.chat.id
        action = callback.data.replace('edit_profile_', '')
        
        user_states[user_id] = {
            'state': f'editing_{action}',
            'message_id': callback.message.message_id
        }
        
        if action == 'name':
            bot.send_message(chat_id, "✏️ Введите ваше новое имя:")
        elif action == 'phone':
            bot.send_message(chat_id, "📞 Введите ваш новый телефон:")
        elif action == 'address':
            bot.send_message(chat_id, "📍 Введите ваш новый адрес:")
        elif action == 'photo':
            bot.send_message(chat_id, "📷 Отправьте ваше новое фото:")
        
        bot.answer_callback_query(callback.id)

    # Обработчик для фото
    @bot.message_handler(content_types=['photo'])
    def handle_profile_photo(message: Message):
        user_id = message.from_user.id
        
        if user_states.get(user_id, {}).get('state') != 'editing_photo':
            return
        
        try:
            # Получаем информацию о файле
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # Сжимаем изображение
            compressed_image = compress_image(downloaded_file)
            
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
            db_manager.update_user_info(user_id, photo_path=photo_path)
            
            # Убираем состояние редактирования
            user_states.pop(user_id, None)
            
            bot.send_message(message.chat.id, f"✅ Фото профиля обновлено! Размер: {file_size_kb:.1f} KB")
            show_my_profile(message)  # Показываем обновленный профиль
            
        except Exception as e:
            logging.error(f"Ошибка при сохранении фото: {e}")
            bot.send_message(message.chat.id, "❌ Ошибка при сохранении фото")

    # Обработчик для текстовых изменений
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state', '').startswith('editing_'))
    def handle_profile_text_edit(message: Message):
        user_id = message.from_user.id
        user_state = user_states.get(user_id, {})
        state = user_state.get('state', '')
        
        if not state.startswith('editing_'):
            return
        
        field = state.replace('editing_', '')
        new_value = message.text.strip()
        
        try:
            if field == 'name':
                if len(new_value) < 2:
                    bot.send_message(message.chat.id, "❌ Имя должно быть не короче 2 символов")
                    return
                db_manager.update_user_info(user_id, full_name=new_value)
                
            elif field == 'phone':
                if not any(char.isdigit() for char in new_value) or len(new_value) < 5:
                    bot.send_message(message.chat.id, "❌ Введите корректный телефон")
                    return
                db_manager.update_user_info(user_id, phone=new_value)
                
            elif field == 'address':
                if len(new_value) < 5:
                    bot.send_message(message.chat.id, "❌ Адрес должен быть не короче 5 символов")
                    return
                db_manager.update_user_info(user_id, address=new_value)
            
            # Убираем состояние редактирования
            user_states.pop(user_id, None)
            
            bot.send_message(message.chat.id, f"✅ {['Имя', 'Телефон', 'Адрес'][['name', 'phone', 'address'].index(field)]} успешно обновлено!")
            show_my_profile(message)  # Показываем обновленный профиль
            
        except Exception as e:
            logging.error(f"Ошибка при обновлении {field}: {e}")
            bot.send_message(message.chat.id, f"❌ Ошибка при обновлении {field}")

    # Ниже еще один метод сжатия с учетом размера файла не более 500 на выходе. Пока первый метод закоментил
    # def compress_image(image_data, max_size=(800, 800), quality=85):
    #     """Сжимает изображение до указанных размеров и качества"""
    #     try:
    #         # Открываем изображение
    #         image = Image.open(io.BytesIO(image_data))
            
    #         # Конвертируем в RGB если нужно (для JPEG)
    #         if image.mode in ('RGBA', 'P'):
    #             image = image.convert('RGB')
            
    #         # Изменяем размер сохраняя пропорции
    #         image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
    #         # Сохраняем в буфер с сжатием
    #         output_buffer = io.BytesIO()
    #         image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            
    #         return output_buffer.getvalue()
            
    #     except Exception as e:
    #         logging.error(f"Ошибка при сжатии изображения: {e}")
    #         return image_data  # Возвращаем оригинал если не удалось сжать

    def compress_image(image_data, max_size=(800, 800), quality=85, max_file_size_kb=500):
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
            logging.error(f"Ошибка при сжатии изображения: {e}")
            return image_data