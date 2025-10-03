# src/myconfbot/utils/file_utils.py

import logging
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class FileManager:
    """Менеджер для работы с файлами"""
    
    def __init__(self, config):
        self.config = config

    def save_user_profile_photo(self, user_id: int, photo_file, filename: str = None) -> Optional[str]:
        """Сохранить фото профиля пользователя с уникальным именем"""
        try:
            # Генерируем уникальное имя с timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"profile_{timestamp}.jpg"
            
            # Получаем путь для сохранения
            save_path = self.config.files.get_user_path(user_id, new_filename)
            
            # Сохраняем файл
            if hasattr(photo_file, 'read'):
                photo_file.seek(0)
                with open(save_path, 'wb') as f:
                    f.write(photo_file.read())
            else:
                with open(save_path, 'wb') as f:
                    f.write(photo_file)
            
            # Удаляем старое фото (опционально)
            self._cleanup_old_profile_photos(user_id, keep_current=new_filename)
            
            relative_path = str(save_path.relative_to(self.config.files.base_dir))
            logger.info(f"Фото профиля сохранено: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении фото профиля: {e}")
            return None

    def _cleanup_old_profile_photos(self, user_id: int, keep_current: str):
        """Очистка старых фото профиля (оставляет только текущее)"""
        try:
            user_dir = self.config.files.get_user_path(user_id)
            for file_path in user_dir.glob("profile_*.jpg"):
                if file_path.name != keep_current:
                    file_path.unlink()  # Удаляем файл
                    logger.debug(f"Удалено старое фото: {file_path}")
        except Exception as e:
            logger.warning(f"Ошибка при очистке старых фото: {e}")

    def get_user_profile_photo_path(self, user_id: int, relative_path: str) -> Optional[Path]:
        """Получить актуальное фото профиля пользователя"""
        try:
            # Если передан валидный путь из БД, используем его
            if relative_path:
                path = self.config.files.resolve_relative_path(relative_path)
                if path and path.exists():
                    return path
            
            # Ищем самое свежее фото в папке пользователя
            user_dir = self.config.files.get_user_path(user_id)
            profile_photos = list(user_dir.glob("profile_*.jpg"))
            
            if profile_photos:
                # Возвращаем самый новый файл (по имени с timestamp)
                latest_photo = sorted(profile_photos, key=lambda x: x.name, reverse=True)[0]
                return latest_photo
            
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении пути к фото профиля: {e}")
            return None
    
    def save_order_status_photo(self, order_id: int, photo_file, filename: str) -> Optional[str]:
        """Сохранить фото статуса заказа и вернуть относительный путь"""
        try:
            # Генерируем уникальное имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = Path(filename).suffix if filename else '.jpg'
            new_filename = f"status_photo_{timestamp}{ext}"
            
            # Получаем путь для сохранения
            save_path = self.config.files.get_order_status_photos_path(order_id, new_filename)
            
            # Сохраняем файл
            if hasattr(photo_file, 'save'):
                photo_file.save(save_path)
            else:
                with open(save_path, 'wb') as f:
                    f.write(photo_file.read())
            
            # Возвращаем относительный путь для хранения в БД
            relative_path = str(save_path.relative_to(self.config.files.base_dir))
            logger.info(f"Фото статуса сохранено: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении фото статуса: {e}")
            return None
    
    def get_order_status_photo_path(self, order_id: int, relative_path: str) -> Optional[Path]:
        """Получить абсолютный путь к фото статуса заказа"""
        try:
            return self.config.files.resolve_relative_path(relative_path)
        except Exception as e:
            logger.error(f"Ошибка при получении пути к фото: {e}")
            return None
    
    def file_exists(self, relative_path: str) -> bool:
        """Проверить существование файла"""
        try:
            path = self.config.files.resolve_relative_path(relative_path)
            return path.exists() and path.is_file()
        except Exception as e:
            logger.error(f"Ошибка при проверке файла: {e}")
            return False