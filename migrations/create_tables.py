#!/usr/bin/env python3
"""
Скрипт для создания таблиц в PostgreSQL
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def execute_sql_file(filename):
    """Выполнение SQL файла"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Разделяем скрипт на отдельные команды
        commands = sql_script.split(';')
        
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'confectioner_bot'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', '5432')
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Выполняем каждую команду отдельно
        for command in commands:
            command = command.strip()
            if command:  # Пропускаем пустые команды
                try:
                    cursor.execute(command)
                    print(f"✓ Выполнено: {command[:50]}...")
                except Exception as e:
                    print(f"⚠️  Ошибка в команде: {e}")
                    continue
        
        cursor.close()
        conn.close()
        print(f"✅ SQL скрипт {filename} выполнен успешно")
        return True
        
    except FileNotFoundError:
        print(f"❌ Файл {filename} не найден")
        return False
    except Exception as e:
        print(f"❌ Ошибка при выполнении SQL: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Создание таблиц в PostgreSQL...")
    
    # Сначала создаем структуру таблиц
    if execute_sql_file('database.sql'):
        print("🎉 Таблицы созданы успешно!")
    else:
        print("❌ Не удалось создать таблицы")
