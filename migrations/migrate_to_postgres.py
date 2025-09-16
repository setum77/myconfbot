#!/usr/bin/env python3
"""
Миграционный скрипт для переноса данных из SQLite в PostgreSQL
Использование: python migrate_to_postgres.py
"""

import sqlite3
import psycopg2
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import shutil
import json
from pathlib import Path

# Загрузка переменных окружения
load_dotenv()

class DatabaseMigrator:
    def __init__(self):
        self.migration_start = datetime.now()
        self.migration_id = self.migration_start.strftime("%Y%m%d_%H%M%S")
        self.log_file = f"migrations/migration_log_{self.migration_id}.txt"
        
        # Путь к SQLite базе
        self.sqlite_path = os.path.join('data', 'confbot.db')
        
        self.setup_logging()
        self.connect_databases()
    
    def setup_logging(self):
        """Настройка логирования"""
        self.log("=" * 60)
        self.log(f"НАЧАЛО МИГРАЦИИ: {self.migration_start}")
        self.log(f"SQLite база: {self.sqlite_path}")
        self.log("=" * 60)
    
    def log(self, message):
        """Запись в лог-файл и вывод в консоль"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def connect_databases(self):
        """Подключение к обеим базам данных"""
        try:
            # Проверяем существование SQLite файла
            if not os.path.exists(self.sqlite_path):
                raise FileNotFoundError(f"SQLite файл не найден: {self.sqlite_path}")
            
            # Подключение к SQLite (исходная БД)
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            self.log("✓ Подключение к SQLite успешно")
            
            # Подключение к PostgreSQL (целевая БД)
            self.pg_conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'confectioner_bot'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', ''),
                port=os.getenv('DB_PORT', '5432')
            )
            self.log("✓ Подключение к PostgreSQL успешно")
            
        except Exception as e:
            self.log(f"✗ Ошибка подключения: {e}")
            raise
    
    def backup_sqlite(self):
        """Создание резервной копии SQLite"""
        # Создаем папку для бэкапов если нет
        os.makedirs('migrations/backups', exist_ok=True)
        
        backup_path = f"migrations/backups/sqlite_backup_{self.migration_id}.db"
        shutil.copy2(self.sqlite_path, backup_path)
        self.log(f"✓ Резервная копия SQLite создана: {backup_path}")
        return backup_path
    
    def get_table_list(self):
        """Получение списка таблиц из SQLite"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        self.log(f"Найдены таблицы: {tables}")
        return tables
    
    def migrate_table(self, table_name, custom_query=None):
        """Миграция конкретной таблицы"""
        self.log(f"Миграция таблицы: {table_name}")
        
        try:
            # Получаем данные из SQLite
            with self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                if custom_query:
                    cursor.execute(custom_query)
                else:
                    cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
            
            if not rows:
                self.log(f"  Таблица {table_name} пуста, пропускаем")
                return 0
            
            # Получаем структуру таблицы для правильного порядка колонок
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            column_names = [col['name'] for col in columns_info]
            
            # Мигрируем в PostgreSQL
            migrated_count = 0
            with self.pg_conn.cursor() as pg_cur:
                for row in rows:
                    try:
                        # Формируем значения в правильном порядке
                        values = [row[col] for col in column_names]
                        placeholders = ', '.join(['%s'] * len(column_names))
                        
                        insert_query = f"""
                            INSERT INTO {table_name} ({', '.join(column_names)})
                            VALUES ({placeholders})
                            ON CONFLICT DO NOTHING
                        """
                        
                        pg_cur.execute(insert_query, values)
                        migrated_count += 1
                        
                    except Exception as e:
                        self.log(f"  Ошибка в строке {migrated_count + 1}: {e}")
                        self.log(f"  Данные: {dict(row)}")
                        continue
            
            self.pg_conn.commit()
            self.log(f"  ✓ Перенесено записей: {migrated_count}/{len(rows)}")
            return migrated_count
            
        except Exception as e:
            self.log(f"  ✗ Ошибка миграции таблицы {table_name}: {e}")
            self.pg_conn.rollback()
            return 0
    
    def migrate_users(self):
        """Специфичная миграция пользователей"""
        return self.migrate_table('users')
    
    def migrate_products(self):
        """Специфичная миграция продуктов"""
        return self.migrate_table('products')
    
    def migrate_orders(self):
        """Специфичная миграция заказов"""
        return self.migrate_table('orders')
    
    def migrate_all_tables(self):
        """Миграция всех таблиц"""
        tables = self.get_table_list()
        migration_stats = {}
        
        # Определяем порядок миграции для избежания foreign key constraints
        migration_order = [
            'users',  # Сначала пользователи
            'product_categories',  # Затем категории
            'products',  # Потом продукты
            'order_statuses',  # Статусы заказов
            'orders',  # Затем заказы
            'reviews',  # Отзывы
            'recipe_categories',  # Категории рецептов
            'recipes',  # Рецепты
            'recipe_ingredients'  # Ингредиенты
        ]
        
        # Добавляем остальные таблицы в конец
        for table in tables:
            if table not in migration_order and not table.startswith('sqlite_'):
                migration_order.append(table)
        
        for table in migration_order:
            if table in tables and not table.startswith('sqlite_'):
                count = self.migrate_table(table)
                migration_stats[table] = count
        
        return migration_stats
    
    def verify_migration(self):
        """Проверка целостности миграции"""
        self.log("Проверка целостности данных...")
        
        verification_results = {}
        
        # Проверяем количество записей в основных таблицах
        tables_to_check = ['users', 'products', 'orders']
        
        for table in tables_to_check:
            try:
                # SQLite count
                with self.sqlite_conn:
                    cursor = self.sqlite_conn.cursor()
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    sqlite_count = cursor.fetchone()['count']
                
                # PostgreSQL count
                with self.pg_conn.cursor() as pg_cur:
                    pg_cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                    pg_count = pg_cur.fetchone()['count']
                
                verification_results[table] = {
                    'sqlite': sqlite_count,
                    'postgresql': pg_count,
                    'match': sqlite_count == pg_count
                }
                
                status = "✓" if sqlite_count == pg_count else "✗"
                self.log(f"  {table}: SQLite={sqlite_count}, PostgreSQL={pg_count} {status}")
                
            except Exception as e:
                self.log(f"  ✗ Ошибка проверки таблицы {table}: {e}")
                verification_results[table] = {'error': str(e)}
        
        return verification_results
    
    def generate_report(self, migration_stats, verification_results):
        """Генерация отчета о миграции"""
        report = {
            'migration_id': self.migration_id,
            'start_time': self.migration_start.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - self.migration_start).total_seconds(),
            'migration_stats': migration_stats,
            'verification_results': verification_results,
            'success': all(result.get('match', False) for result in verification_results.values() 
                          if isinstance(result, dict) and 'match' in result)
        }
        
        # Сохраняем отчет в JSON
        report_file = f"migrations/migration_report_{self.migration_id}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log(f"Отчет сохранен: {report_file}")
        return report
    
    def cleanup(self):
        """Очистка ресурсов"""
        if hasattr(self, 'sqlite_conn'):
            self.sqlite_conn.close()
        if hasattr(self, 'pg_conn'):
            self.pg_conn.close()
        self.log("Ресурсы очищены")

def main():
    """Основная функция миграции"""
    migrator = None
    try:
        migrator = DatabaseMigrator()
        
        # 1. Резервное копирование
        backup_path = migrator.backup_sqlite()
        
        # 2. Миграция данных
        migrator.log("Начало миграции данных...")
        migration_stats = migrator.migrate_all_tables()
        
        # 3. Проверка целостности
        migrator.log("Проверка целостности...")
        verification_results = migrator.verify_migration()
        
        # 4. Генерация отчета
        report = migrator.generate_report(migration_stats, verification_results)
        
        # 5. Итоговый статус
        if report['success']:
            migrator.log("🎉 МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
            migrator.log(f"Общее время: {report['duration_seconds']:.2f} секунд")
        else:
            migrator.log("❌ МИГРАЦИЯ ЗАВЕРШЕНА С ОШИБКАМИ!")
            migrator.log("Проверьте лог-файл для деталей")
            sys.exit(1)
            
    except Exception as e:
        if migrator:
            migrator.log(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        else:
            print(f"Критическая ошибка при инициализации: {e}")
        sys.exit(1)
        
    finally:
        if migrator:
            migrator.cleanup()

if __name__ == "__main__":
    # Проверяем существование исходной БД
    sqlite_path = os.path.join('data', 'confbot.db')
    if not os.path.exists(sqlite_path):
        print(f"❌ Файл {sqlite_path} не найден!")
        print("Запустите скрипт из корневой директории проекта")
        sys.exit(1)
    
    # Запрос подтверждения
    print("⚠️  ВНИМАНИЕ: Это миграционный скрипт для переноса данных")
    print("⚠️  Убедитесь, что:")
    print("  1. Сделана резервная копия всего проекта")
    print("  2. PostgreSQL база создана и настроена")
    print("  3. Бот остановлен на время миграции")
    print(f"  4. Будет перенесена база: {sqlite_path}")
    
    confirmation = input("Продолжить миграцию? (y/N): ")
    if confirmation.lower() != 'y':
        print("Миграция отменена")
        sys.exit(0)
    
    main()