# src\myconfbot\handlers\user\auth_handlers.py

import logging
from telebot.types import Message

from src.myconfbot.handlers.user.base_user_handler import BaseUserHandler
from src.myconfbot.handlers.shared.constants import UserStates, Validation


class AuthHandler(BaseUserHandler):
    """Обработчик аутентификации и регистрации"""
    
    def __init__(self, bot, config, db_manager):
        super().__init__(bot, config, db_manager)
        self.logger = logging.getLogger(__name__)
    
    def register_handlers(self):
        """Регистрация обработчиков аутентификации"""
        self._register_name_input_handler()
        self._register_phone_input_handler()
        self._register_address_input_handler()
    
    def _register_name_input_handler(self):
        """Регистрация обработчика ввода имени"""
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_user_state(message.from_user.id) is not None and
            self.states_manager.get_user_state(message.from_user.id).get('state') == UserStates.AWAITING_NAME
        )
        def handle_name_input(message: Message):
            self._handle_name_input(message)
    
    def _register_phone_input_handler(self):
        """Регистрация обработчика ввода телефона"""
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_user_state(message.from_user.id) is not None and
            self.states_manager.get_user_state(message.from_user.id).get('state') == UserStates.AWAITING_PHONE
        )
        def handle_phone_input(message: Message):
            self._handle_phone_input(message)
    
    def _register_address_input_handler(self):
        """Регистрация обработчика ввода адреса"""
        @self.bot.message_handler(
            func=lambda message: self.states_manager.get_user_state(message.from_user.id) is not None and
            self.states_manager.get_user_state(message.from_user.id).get('state') == UserStates.AWAITING_ADDRESS
        )
        def handle_address_input(message: Message):
            self._handle_address_input(message)
    
    def _handle_name_input(self, message: Message):
        """Обработка ввода имени при регистрации"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        name = message.text.strip()
        
        user_state = self.states_manager.get_user_state(user_id)
        is_admin = user_state.get('is_admin', False)
        username = user_state.get('username')
        
        if len(name) < Validation.MIN_NAME_LENGTH:
            self.bot.send_message(chat_id, "Пожалуйста, введите настоящее имя (минимум 2 символа).")
            return
        
        try:
            self.auth_service.create_user(
                telegram_id=user_id,
                full_name=name,
                telegram_username=username,
                is_admin=is_admin
            )
            
            if is_admin:
                # Для администратора запрашиваем дополнительные данные
                user_state['state'] = UserStates.AWAITING_PHONE
                user_state['name'] = name
                self.states_manager.set_user_state(user_id, user_state)
                self.bot.send_message(chat_id, "Отлично! Теперь укажите ваш телефонный номер:")
            else:
                # Для клиента просто сохраняем и показываем меню
                self.states_manager.clear_user_state(user_id)
                self.bot.send_message(chat_id, f"Приятно познакомиться, {name}! 😊")
                markup = self.show_main_menu(chat_id, False)
                self.bot.send_message(chat_id, "Главное меню", reply_markup=markup)
                
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении имени: {e}", exc_info=True)
            self.bot.send_message(chat_id, "Произошла ошибка при сохранении. Попробуйте еще раз.")
    
    def _handle_phone_input(self, message: Message):
        """Обработка ввода телефона при регистрации"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        phone = message.text.strip()
        
        user_state = self.states_manager.get_user_state(user_id)
        
        # Простая валидация телефона
        if not any(char.isdigit() for char in phone) or len(phone) < Validation.MIN_PHONE_DIGITS:
            self.bot.send_message(chat_id, "Пожалуйста, введите корректный телефонный номер.")
            return
        
        try:
            # Обновляем состояние
            user_state['phone'] = phone
            user_state['state'] = UserStates.AWAITING_ADDRESS
            self.states_manager.set_user_state(user_id, user_state)
            
            self.bot.send_message(chat_id, "Отлично! Теперь укажите ваш адрес:")
                
        except Exception as e:
            self.logger.error(f"Ошибка при обработке телефона: {e}", exc_info=True)
            self.bot.send_message(chat_id, "Произошла ошибка. Попробуйте еще раз.")
    
    def _handle_address_input(self, message: Message):
        """Обработка ввода адреса при регистрации"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        address = message.text.strip()
        
        user_state = self.states_manager.get_user_state(user_id)
        name = user_state.get('name')
        phone = user_state.get('phone')
        
        if len(address) < Validation.MIN_ADDRESS_LENGTH:
            self.bot.send_message(chat_id, "Пожалуйста, введите полный адрес.")
            return
        
        try:
            # Обновляем информацию администратора
            self.auth_service.update_user_info(
                user_id, 
                phone=phone, 
                address=address
            )
            
            # Очищаем состояние
            self.states_manager.clear_user_state(user_id)
            
            success_msg = (
                f"Отлично, {name}! 👑\n"
                f"Ваши данные сохранены. Теперь вы можете управлять кондитерской!"
            )
            self.bot.send_message(chat_id, success_msg)
            
            # Показываем главное меню
            markup = self.show_main_menu(chat_id, True)
            self.bot.send_message(chat_id, "Главное меню", reply_markup=markup)
                
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении адреса: {e}", exc_info=True)
            self.bot.send_message(chat_id, "Произошла ошибка при сохранении. Попробуйте еще раз.")