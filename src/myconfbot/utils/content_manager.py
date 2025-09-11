import os
import logging
from pathlib import Path

class ContentManager:
    def __init__(self):
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)
        
        # Создаем файлы по умолчанию если их нет
        self.ensure_default_files()
    
    def ensure_default_files(self):
        """Создает файлы с содержимым по умолчанию если они не существуют"""
        default_content = {
            'welcome.md': """🎂 Добро пожаловать в кондитерскую мастерскую!

Я помогу вам:
• 📋 Сделать заказ тортов и десертов
• 📖 Посмотреть рецепты
• 💼 Узнать о наших услугах
• 📞 Связаться с мастером

Выберите действие из меню ниже 👇""",
            
            'contacts.md': """📍 Наш адрес: ул. Кондитерская, 15
📞 Телефон: +7 (999) 123-45-67
🕒 Время работы: 9:00 - 21:00
📧 Email: master@myconfbot.ru

Мы всегда рады вашим вопросам и заказам! 🎂"""
        }
        
        for filename, content in default_content.items():
            file_path = self.data_dir / filename
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logging.info(f"Создан файл {filename} с содержимым по умолчанию")
    
    def get_content(self, filename):
        """Получает содержимое файла"""
        try:
            file_path = self.data_dir / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            return None
        except Exception as e:
            logging.error(f"Ошибка чтения файла {filename}: {e}")
            return None
    
    def update_content(self, filename, content):
        """Обновляет содержимое файла"""
        try:
            file_path = self.data_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logging.error(f"Ошибка записи в файл {filename}: {e}")
            return False
    
    def get_file_list(self):
        """Получает список доступных файлов контента"""
        return [f.name for f in self.data_dir.glob('*.md')]

# Глобальный экземпляр
content_manager = ContentManager()