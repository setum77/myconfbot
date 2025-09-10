#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
"""

import os
import sys

# Добавляем путь к проекту
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

from src.myconfbot.utils.database import db_manager

def main():
    """Основная функция инициализации БД"""
    print("🎂 Инициализация базы данных кондитера...")
    
    try:
        # Инициализируем БД
        db_manager.init_db()
        
        print("✅ База данных успешно создана!")
        print("📁 Файл БД: data/confbot.db")
        
        # Создаем базовый .env файл если его нет
        env_file = os.path.join(project_root, '.env')
        if not os.path.exists(env_file):
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write("TELEGRAM_BOT_TOKEN=your_bot_token_here\n")
                f.write("ADMIN_IDS=123456789\n")
                f.write("DATABASE_URL=data/confbot.db\n")
                f.write("LOG_LEVEL=INFO\n")
            print("📝 Создан файл .env - заполните TELEGRAM_BOT_TOKEN вашим токеном")
            
    except Exception as e:
        print(f"❌ Ошибка при инициализации БД: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()