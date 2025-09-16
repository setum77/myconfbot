import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    try:
        # Подключение к базовой базе данных
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', '5432')
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Создание базы данных
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'confectioner_bot'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE confectioner_bot")
            print("База данных создана успешно")
        else:
            print("База данных уже существует")
        
        cursor.close()
        conn.close()
        
        # Подключение к новой базе данных и выполнение скрипта
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database='confectioner_bot',
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', '5432')
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Чтение и выполнение SQL скрипта
        with open('database.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        cursor.execute(sql_script)
        print("Таблицы созданы успешно")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Ошибка при создании базы данных: {e}")

if __name__ == "__main__":
    create_database()