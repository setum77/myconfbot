# src/myconfbot/handlers/user/order_processor.py

import logging
import os
from datetime import datetime, timedelta
from telebot import types
from telebot.types import Message, CallbackQuery

from src.myconfbot.handlers.user.order_constants import OrderConstants

logger = logging.getLogger(__name__)

class OrderProcessor:
    """Процессор оформления заказа - реализует все 8 шагов"""
    
    def __init__(self, bot, db_manager, order_states):
        self.bot = bot
        self.db_manager = db_manager
        self.order_states = order_states
    
    def start_order_process(self, callback: CallbackQuery):
        """Начало оформления заказа - Шаг 1: Проверка доступности"""
        if callback.from_user.is_bot:
            logger.warning(f"⚠️ Пропускаем callback от бота: {callback.from_user.id}")
            return
        
        try:
            product_id = int(callback.data.replace('order_start_', ''))
            user_id = callback.from_user.id
            
            # Получаем информацию о товаре
            product = self.db_manager.get_product_by_id(product_id)
            
            if not product:
                self.bot.answer_callback_query(callback.id, "❌ Товар не найден")
                return
            
            # Шаг 1: Проверка доступности товара
            if not product['is_available']:
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton(
                    "🔙 Назад к товарам",
                    callback_data=f"order_back_to_category_{product['category_id']}"
                ))
                
                self.bot.send_message(
                    callback.message.chat.id,
                    "❌ <b>К сожалению, данный кондитерский продукт временно недоступен.</b>\n\n"
                    "Мы работаем над его возвращением — следите за обновлениями! 🍰",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                self.bot.answer_callback_query(callback.id)
                return
            
            # Товар доступен - начинаем процесс заказа 
            logger.info(f"✅ Товар доступен, начинаем процесс заказа с шага количества")
            self._start_order_creation(user_id, product_id, callback.message)
            # self.order_states.start_order(user_id, product_id, callback.message)
            
            # Переходим к шагу 2: Запрос количества
            #self._ask_quantity(callback.message, product_id)
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при начале заказа: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при начале заказа")

    def _start_order_creation(self, user_id: int, product_id: int, message: Message):
        """Начало непосредственного оформления заказа (после проверки доступности)"""
        logger.info(f"✅ Товар доступен, начинаем оформление заказа для пользователя {user_id}")
        
        # Начинаем процесс заказа с шага количества
        self.order_states.start_order(user_id, product_id)

        # ПРОВЕРЯЕМ состояние после установки
        order_data = self.order_states.get_order_data(user_id)
        logger.info(f"🔍 Состояние после start_order: {order_data}")
        
        # Переходим к шагу 2: Запрос количества
        self._ask_quantity(message, product_id)
    
    def _ask_quantity(self, message: Message, product_id: int):
        """Шаг 2: Запрос количества товара"""
        product = self.db_manager.get_product_by_id(product_id)
        
        if not product:
            self.bot.send_message(message.chat.id, "❌ Товар не найден")
            return
        
        # Определяем тип измерения
        measurement_unit = product['measurement_unit'] or 'шт'
        is_weight_based = 'грамм' in measurement_unit.lower()
        
        question = f"🎂 <b>{product['name']}</b>\n\n"
        
        if is_weight_based:
            question += f"⚖️ <b>Товар измеряется по весу</b>\n"
            question += f"💰 Цена: {product['price']} руб. за {product['quantity']} {measurement_unit}\n\n"
            #question += " \n\n" 
            question += "➡️ <b>Введите вес в граммах:</b>"
        else:
            question += f"💰 Цена: {product['price']} руб. за {product['quantity']} {measurement_unit}\n\n"
            #question += " \n\n"            
            question += "➡️ <b>Введите количество:</b>"
        
        keyboard = OrderConstants.create_back_keyboard("order_cancel_quantity")
        
        self.bot.send_message(
            message.chat.id,
            question,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        # Обновляем состояние
        self.order_states.set_order_step(message.from_user.id, 'order_quantity')

    def process_quantity_input(self, message: Message, order_data: dict):
        """Обработка ввода количества/веса - Шаг 2"""
        logger.info(f"✅ Обработка ввода количества/веса - Шаг 2")
        if message.from_user.is_bot:
            logger.warning(f"⚠️ Пропускаем сообщение от бота: {message.from_user.id}")
            return

        try:
            logger.info(f"🔍 Обработка ввода количества/веса: {message.text}")

            product_id = order_data['product_id']
            product = self.db_manager.get_product_by_id(product_id)
            
            if not product:
                self.bot.send_message(message.chat.id, "❌ Товар не найден")
                self.order_states.cancel_order(message.from_user.id)
                return
            
            measurement_unit = product['measurement_unit'] or 'шт'
            is_weight_based = 'грамм' in measurement_unit.lower()

            logger.info(f"🔍 Товар: {product['name']}, измерение: {measurement_unit}, по весу: {is_weight_based}")
            
            # Парсим ввод
            input_value = message.text.strip()
            logger.info(f"🔍 Введенное значение: '{input_value}'")

            # Парсим ввод
            if is_weight_based:
                weight_grams = float(message.text)
                logger.info(f"🔍 Распознан вес: {weight_grams} г")

                if weight_grams <= 0:
                    self.bot.send_message(message.chat.id, "❌ Введите положительное число")
                    return
                
                # Сохраняем вес
                self.order_states.update_order_data(
                    message.from_user.id,
                    weight_grams=weight_grams,
                    state='order_date'
                )
            else:
                quantity = float(message.text)
                if quantity <= 0:
                    self.bot.send_message(message.chat.id, "❌ Введите положительное число")
                    return
                                               
                # Сохраняем количество
                self.order_states.update_order_data(
                    message.from_user.id,
                    quantity=quantity,
                    state='order_date'
                )
            
            # Переходим к шагу 3: Дата приготовления
            self._ask_date(message, product_id)
            
        except ValueError:
            self.bot.send_message(message.chat.id, "❌ Введите число")

    def _ask_date(self, message: Message, product_id: int):
        """Шаг 3: Запрос даты и времени приготовления"""
        # Минимальная дата - завтра
        min_date = datetime.now() + timedelta(days=1)
        
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        
        # Предлагаем ближайшие даты
        for i in range(1, 6):
            date = min_date + timedelta(days=i)
            keyboard.add(types.InlineKeyboardButton(
                date.strftime("%d.%m"),
                callback_data=f"order_date_{date.strftime('%Y-%m-%d')}"
            ))
        
        keyboard.add(types.InlineKeyboardButton(
            "📅 Другая дата",
            callback_data="order_custom_date"
        ))
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад",
            callback_data="order_back_quantity"
        ))
        
        self.bot.send_message(
            message.chat.id,
            "📅 <b>Выберите дату приготовления:</b>\n\n"
            "Минимальный срок - завтра.",
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def handle_date_selection(self, callback: CallbackQuery):
        """Обработка выбора даты из предложенных"""
        if callback.from_user.is_bot:
            logger.warning(f"⚠️ Пропускаем callback от бота: {callback.from_user.id}")
            return
        
        try:
            date_str = callback.data.replace('order_date_', '')
            selected_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Сохраняем дату
            self.order_states.update_order_data(
                callback.from_user.id,
                ready_date=selected_date.isoformat(),
                state='order_time'  # Теперь переходим к выбору времени, а не доставки
            )
            
            # Переходим к шагу 4: Время
            self._ask_time(callback.message)
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при выборе даты: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при выборе даты")

    # Обновить метод process_custom_date_input для перехода к выбору времени
    def process_custom_date_input(self, message: Message, order_data: dict):
        """Обработка ручного ввода даты"""
        try:
            date_str = message.text.strip()
            selected_date = datetime.strptime(date_str, '%d.%m.%Y')
            
            # Проверяем что дата не в прошлом
            min_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if selected_date < min_date:
                self.bot.send_message(message.chat.id, "❌ Дата не может быть в прошлом")
                return
            
            # Сохраняем дату
            self.order_states.update_order_data(
                message.from_user.id,
                ready_date=selected_date.isoformat(),
                state='order_time'  # Теперь переходим к выбору времени, а не доставки
            )
            
            # Переходим к шагу 4: Время
            self._ask_time(message)
            
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ (например: 25.12.2024)"
            )

    def handle_custom_date(self, callback: CallbackQuery):
        """Обработка запроса ручного ввода даты"""
        if callback.from_user.is_bot:
            logger.warning(f"⚠️ Пропускаем callback от бота: {callback.from_user.id}")
            return
        
        self.order_states.set_order_step(callback.from_user.id, 'order_date_custom')
        
        keyboard = OrderConstants.create_back_keyboard("order_back_date")
        
        self.bot.send_message(
            callback.message.chat.id,
            "📅 <b>Введите дату приготовления в формате ДД.ММ.ГГГГ:</b>\n\n"
            "Например: 25.12.2024\n"
            "Минимальный срок - завтра.",
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        self.bot.answer_callback_query(callback.id)


    def _ask_time(self, message: Message):
        """Шаг 4: Запрос времени готовности"""
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        
        # Предлагаем стандартные временные интервалы
        times = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", 
                "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"]
        
        # Создаем кнопки по 3 в ряд
        for i in range(0, len(times), 3):
            row_times = times[i:i + 3]
            row_buttons = []
            for time in row_times:
                row_buttons.append(types.InlineKeyboardButton(
                    time,
                    callback_data=f"order_time_{time}"
                ))
            keyboard.add(*row_buttons)
        
        keyboard.add(types.InlineKeyboardButton(
            "⏰ Другое время",
            callback_data="order_custom_time"
        ))
        
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к дате",
            callback_data="order_back_date"
        ))
        
        self.bot.send_message(
            message.chat.id,
            "⏰ <b>Выберите время готовности:</b>\n\n"
            "Время указывается в формате ЧЧ:MM",
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def handle_time_selection(self, callback: CallbackQuery):
        """Обработка выбора времени из предложенных"""
        if callback.from_user.is_bot:
            logger.warning(f"⚠️ Пропускаем callback от бота: {callback.from_user.id}")
            return
        
        try:
            time_str = callback.data.replace('order_time_', '')
            
            # Валидация формата времени
            from datetime import datetime
            try:
                datetime.strptime(time_str, '%H:%M')
            except ValueError:
                self.bot.answer_callback_query(callback.id, "❌ Неверный формат времени")
                return
            
            # Сохраняем время
            self.order_states.update_order_data(
                callback.from_user.id,
                ready_time=time_str,
                state='order_delivery'
            )
            
            # Переходим к шагу 5: Доставка
            self._ask_delivery(callback.message)
            
            self.bot.answer_callback_query(callback.id)
            
        except Exception as e:
            logger.error(f"Ошибка при выборе времени: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при выборе времени")

    def handle_custom_time(self, callback: CallbackQuery):
        """Обработка запроса ручного ввода времени"""
        if callback.from_user.is_bot:
            logger.warning(f"⚠️ Пропускаем callback от бота: {callback.from_user.id}")
            return
        
        self.order_states.set_order_step(callback.from_user.id, 'order_time_custom')
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад к выбору времени",
            callback_data="order_back_time"
        ))
        
        self.bot.send_message(
            callback.message.chat.id,
            "⏰ <b>Введите время готовности в формате ЧЧ:MM</b>\n\n"
            "Например:\n"
            "• 14:30 - половина третьего\n"
            "• 09:00 - девять утра\n"
            "• 18:45 - без пятнадцати семь вечера\n\n"
            "Рабочее время: с 09:00 до 21:00",
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        self.bot.answer_callback_query(callback.id)

    def process_custom_time_input(self, message: Message, order_data: dict):
        """Обработка ручного ввода времени"""
        try:
            time_str = message.text.strip()
            
            # Валидация формата времени
            from datetime import datetime
            try:
                datetime.strptime(time_str, '%H:%M')
            except ValueError:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Неверный формат времени. Используйте ЧЧ:MM (например: 14:30)"
                )
                return
            
            # Проверяем рабочее время (9:00 - 21:00)
            hour = int(time_str.split(':')[0])
            if hour < 9 or hour > 21:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Время должно быть в рабочем интервале с 09:00 до 21:00"
                )
                return
            
            # Сохраняем время
            self.order_states.update_order_data(
                message.from_user.id,
                ready_time=time_str,
                state='order_delivery'
            )
            
            # Переходим к шагу 5: Доставка
            self._ask_delivery(message)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке времени: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка при обработке времени. Попробуйте еще раз."
            )

    def process_delivery_continue(self, callback: CallbackQuery):
        """Продолжение после информации о доставке"""
        if callback.from_user.is_bot:
            logger.warning(f"⚠️ Пропускаем callback от бота: {callback.from_user.id}")
            return
        
        self.order_states.update_order_data(
            callback.from_user.id,
            delivery_type="самовывоз",
            state='order_payment'
        )
        
        # Переходим к шагу 5: Оплата
        order_data = self.order_states.get_order_data(callback.from_user.id)
        self._ask_payment(callback.message, order_data['product_id'])
        self.bot.answer_callback_query(callback.id)

    def _ask_payment(self, message: Message, product_id: int):
        """Шаг 5: Информация по оплате"""

        product = self.db_manager.get_product_by_id(product_id)
        
        if not product:
            self.bot.send_message(message.chat.id, "❌ Товар не найден")
            return
        
        prepayment_conditions = product.get('prepayment_conditions', '')
        payment_message = "💳 <b>Информация по оплате</b>\n\n"
        
        if "50% предоплата" in prepayment_conditions:
            payment_message += (
                "Чтобы забронировать ваш заказ, необходимо внести предоплату 50%. "
                "Оставшаяся сумма — при самовывозе. \n\nОплату можно произвести способами, "
                "описанными в разделе «Контакты»."
            )
        elif "100% предоплата" in prepayment_conditions:
            payment_message += (
                "Ваш заказ требует полной предоплаты для оформления.\n\n"
                "После оплаты мы сразу начнём готовить вашу сладость — и сообщим о готовности к самовывозу. \n\n"
                "Оплату можно произвести способами, описанными в разделе «Контакты»."
            )
        else:  # Постоплата
            payment_message += (
                "Оплата производится при получении товара — никаких предоплат! \n\n"
                "Просто заберите заказ в указанное время — и оплатите наличными или картой на месте. 🎁"
            )
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "✅ Понятно, продолжаем",
            callback_data="order_payment_continue"
        ))
        keyboard.add(types.InlineKeyboardButton(
            "🔙 Назад",
            callback_data="order_back_delivery"
        ))
        
        self.bot.send_message(
            message.chat.id,
            payment_message,
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def process_payment_continue(self, callback: CallbackQuery):
        """Продолжение после информации об оплате"""
        if callback.from_user.is_bot:
            logger.warning(f"⚠️ Пропускаем callback от бота: {callback.from_user.id}")
            return
        
        self.order_states.set_order_step(callback.from_user.id, 'order_notes')
        
        # Переходим к шагу 6: Примечания
        self._ask_notes(callback.message)
        self.bot.answer_callback_query(callback.id)

    def _ask_notes(self, message: Message):
        """Шаг 6: Добавление примечаний к заказу"""
        keyboard = OrderConstants.create_back_keyboard("order_back_payment")
        
        self.bot.send_message(
            message.chat.id,
            "📝 <b>Добавление примечаний к заказу</b>\n\n"
            "Здесь вы можете указать дополнительную информацию:\n"
            "• Пожелания по оформлению\n"
            "• Особенности аллергии\n"
            "• Другие важные детали\n\n"
            "➡️ <b>Введите ваши примечания:</b>\n"
            "Или отправьте '-' если примечаний нет.",
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def process_notes_input(self, message: Message, order_data: dict):
        """Обработка ввода примечаний - Шаг 6"""
        notes_text = message.text.strip()
        
        if notes_text != '-':
            # Сохраняем примечание во временный буфер
            self.order_states.add_order_note(
                message.from_user.id,
                notes_text,
                is_admin=False
            )
        
        # Переходим к шагу 7: Подтверждение
        self.order_states.set_order_step(message.from_user.id, 'order_confirmation')
        self._show_order_summary(message, order_data)

    def _show_order_summary(self, message: Message, order_data: dict):
        """Шаг 7: Подтверждение заказа"""
        product = self.db_manager.get_product_by_id(order_data['product_id'])
        
        if not product:
            self.bot.send_message(message.chat.id, "❌ Товар не найден")
            return
        
        # Вычисляем стоимость
        measurement_unit = product['measurement_unit'] or 'шт'
        is_weight_based = 'грамм' in measurement_unit.lower()
        
        if is_weight_based:
            weight_grams = order_data.get('weight_grams', 0)
            approximate_cost = float(product['price']) * weight_grams / float(product['quantity'])
            quantity_display = f"{weight_grams} г"
            cost_note = "  Стоимость, указанная выше, является ориентировочной и рассчитана на основе стандартных параметров "
            cost_note += "(вес, декор, базовые ингредиенты)\n\n"
            cost_note += "Окончательная цена будет уточнена после согласования всех деталей"
        else:
            quantity = order_data.get('quantity', 0)
            approximate_cost = float(product['price']) * quantity
            quantity_display = f"{quantity} {measurement_unit}"
            cost_note = ""
        
        # Определяем статус оплаты
        prepayment_conditions = product.get('prepayment_conditions', '')
        if "предоплата" in prepayment_conditions:
            payment_status = "Ожидает предоплату"
        else:
            payment_status = "Не оплачен"
        
        # Формируем сводку
        summary = "📋 <b>Сводка заказа</b>\n\n"
        summary += f"🎂 <b>Товар:</b> {product['name']}\n"
        summary += f"📦 <b>Количество:</b> {quantity_display}\n"
        summary += f"💰 <b>Стоимость:</b> {approximate_cost:.2f} руб.{cost_note}\n"
        
        # Добавляем дату и время готовности
        if 'ready_date' in order_data:
            ready_date = datetime.fromisoformat(order_data['ready_date'])
            date_str = ready_date.strftime('%d.%m.%Y')
            
            if 'ready_time' in order_data:
                time_str = order_data['ready_time']
                summary += f"📅 <b>Дата и время готовности:</b> {date_str} в {time_str}\n"
            else:
                summary += f"📅 <b>Дата готовности:</b> {date_str}\n"
        
        summary += f"🚚 <b>Доставка:</b> {order_data.get('delivery_type', 'самовывоз')}\n"
        summary += f"💳 <b>Вид расчета:</b> {prepayment_conditions or 'не указан'}\n"
        summary += f"🔄 <b>Статус оплаты:</b> {payment_status}\n"
        summary += f"📊 <b>Статус заказа:</b> Новый\n"
        
        # Примечания
        notes = order_data.get('notes', [])
        if notes:
            user_notes = [note for note in notes if not note.get('is_admin', False)]
            if user_notes:
                summary += f"📝 <b>Примечания:</b> {user_notes[0]['text']}\n"
        
        summary += f"\n<b>Время создания:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        # Создаем временный ID для подтверждения
        temp_order_id = f"temp_{message.from_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        keyboard = OrderConstants.create_order_confirmation_keyboard(temp_order_id)
        
        self.bot.send_message(
            message.chat.id,
            summary,
            parse_mode='HTML',
            reply_markup=keyboard
        )

    def complete_order(self, callback: CallbackQuery):
        """Подтверждение заказа - Шаг 8: Сохранение и информирование"""
        if callback.from_user.is_bot:
            logger.warning(f"⚠️ Пропускаем callback от бота: {callback.from_user.id}")
            return
        
        try:
            user_id = callback.from_user.id
            order_data = self.order_states.complete_order(user_id)
            
            if not order_data:
                self.bot.answer_callback_query(callback.id, "❌ Данные заказа не найдены")
                return
            
            # Создаем заказ в базе данных
            order_success = self._create_order_in_db(user_id, order_data)
            
            if order_success:
                self.bot.answer_callback_query(callback.id, "✅ Заказ создан!")
                
                # Шаг 8: Финальное сообщение
                self.bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text="🎉 <b>Спасибо! Ваш заказ принят.</b>\n\n"
                         "Всё, что нужно знать о заказе — вы найдёте в разделе «Мои заказы»:\n\n"
                         "🔹 1. Детальная информация — состав, цена, дата и время\n"
                         "🔹 2. Статус заказа — история всех изменений и этапов подготовки\n"
                         "🔹 3. Примечания к заказу — переписка с нами и ваши пожелания\n\n"
                         "Следите за обновлениями — мы скоро свяжемся с вами! 🍰💛",
                    parse_mode='HTML'
                )
                
                # TODO: Уведомление администраторов
                
            else:
                self.bot.answer_callback_query(callback.id, "❌ Ошибка при создании заказа")
                
        except Exception as e:
            logger.error(f"Ошибка при подтверждении заказа: {e}")
            self.bot.answer_callback_query(callback.id, "❌ Ошибка при создании заказа")

    def _create_order_in_db(self, user_id: int, order_data: dict) -> bool:
        """Создание заказа в базе данных с учетом новых полей"""
        try:
            product = self.db_manager.get_product_by_id(order_data['product_id'])
            
            if not product:
                return False
            
            # Вычисляем стоимость
            measurement_unit = product['measurement_unit'] or 'шт'
            is_weight_based = 'грамм' in measurement_unit.lower()
            
            if is_weight_based:
                weight_grams = order_data.get('weight_grams', 0)
                total_cost = float(product['price']) * weight_grams / float(product['quantity'])
                quantity = None
            else:
                quantity = order_data.get('quantity', 0)
                total_cost = float(product['price']) * quantity
                weight_grams = None
            
            # Формируем дату и время готовности
            ready_at = None
            if 'ready_date' in order_data:
                ready_date = datetime.fromisoformat(order_data['ready_date'])
                
                if 'ready_time' in order_data:
                    # Объединяем дату и время
                    time_str = order_data['ready_time']
                    hour, minute = map(int, time_str.split(':'))
                    ready_at = ready_date.replace(hour=hour, minute=minute)
                else:
                    ready_at = ready_date

            # Определяем статус оплаты
            prepayment_conditions = product.get('prepayment_conditions', '')
            if "предоплата" in prepayment_conditions:
                payment_status = "Ожидает предоплату"
            else:
                payment_status = "Не оплачен"
            
            order_db_data = {
                'user_id': user_id,
                'product_id': order_data['product_id'],
                'quantity': quantity,
                'weight_grams': weight_grams,
                'total_cost': total_cost,
                'delivery_type': order_data.get('delivery_type', 'самовывоз'),
                'payment_type': prepayment_conditions,
                'payment_status': payment_status,
                'admin_notes': '',
                'ready_at': ready_at.isoformat() if ready_at else None
            }
            
            # Создаем заказ
            order_id = self.db_manager.create_order_and_get_id(order_db_data)
            
            if order_id:
                # Сохраняем примечания пользователя
                if 'notes' in order_data:
                    user_notes = [note for note in order_data['notes'] if not note.get('is_admin', False)]
                    if user_notes:
                        for note in user_notes:
                            self.db_manager.add_order_note(
                                order_id,
                                user_id,
                                note['text']
                            )
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при создании заказа в БД: {e}")
            return False

    def cancel_order(self, callback: CallbackQuery):
        """Отмена заказа"""
        if callback.from_user.is_bot:
            logger.warning(f"⚠️ Пропускаем callback от бота: {callback.from_user.id}")
            return
        
        user_id = callback.from_user.id
        self.order_states.cancel_order(user_id)
        
        self.bot.answer_callback_query(callback.id, "❌ Заказ отменен")
        
        self.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="❌ <b>Заказ отменен</b>",
            parse_mode='HTML'
        )