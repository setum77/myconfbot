#!/usr/bin/env python3
"""
Скрипт для инициализации PostgreSQL базы данных
"""

import os
import sys
import argparse
from pathlib import Path

# Добавляем путь к проекту
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.myconfbot.utils.database import DatabaseManager
from src.myconfbot.config import Config

def init_database():
    """Инициализация базы данных"""
    print("🎂 Инициализация PostgreSQL базы данных...")
    
    try:
        config = Config.load()
        db_manager = DatabaseManager(config)
        
        # Инициализируем БД
        db_manager.init_db()
        
        print("✅ База данных успешно инициализирована!")
        print(f"📊 Database URL: {config.db.url}")
        
    except Exception as e:
        print(f"❌ Ошибка при инициализации БД: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def create_env_file():
    """Создание .env файла с примером"""
    env_file = project_root / '.env'
    if not env_file.exists():
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# Telegram Bot Configuration\n")
            f.write("TELEGRAM_BOT_TOKEN=your_bot_token_here\n\n")
            f.write("# Admin Configuration\n")
            f.write("ADMIN_IDS=123456789\n\n")
            f.write("# Database Configuration\n")
            f.write("USE_POSTGRES=true\n")
            f.write("DB_HOST=localhost\n")
            f.write("DB_PORT=5432\n")
            f.write("DB_NAME=confectioner_bot\n")
            f.write("DB_USER=postgres\n")
            f.write("DB_PASSWORD=your_password_here\n")
            f.write("# или используйте DATABASE_URL напрямую:\n")
            f.write("# DATABASE_URL=postgresql://user:password@host:port/dbname\n\n")
            f.write("# Logging\n")
            f.write("LOG_LEVEL=INFO\n")
        
        print("📝 Создан файл .env.example - настройте параметры базы данных")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Инициализация PostgreSQL базы данных")
    parser.add_argument('--create-env', action='store_true', help="Создать .env файл")
    
    args = parser.parse_args()
    
    if args.create_env:
        create_env_file()
    else:
        init_database()