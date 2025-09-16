#!/usr/bin/env python3
"""
Утилита для проверки готовности к миграции
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_requirements():
    print("🔍 Проверка требований для миграции...")
    
    # Проверка существования SQLite БД
    if not os.path.exists('data/confbot.db'):
        print("❌ data.db не найден")
        return False
    
    # Проверка подключения к PostgreSQL
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        conn.close()
        print("✓ Подключение к PostgreSQL OK")
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return False
    
    # Проверка переменных окружения
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    for var in required_vars:
        if not os.getenv(var):
            print(f"❌ Переменная окружения {var} не установлена")
            return False
    
    print("✓ Все проверки пройдены успешно!")
    return True

if __name__ == "__main__":
    check_requirements()