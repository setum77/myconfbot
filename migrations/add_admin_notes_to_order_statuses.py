"""
Миграция для добавления поля admin_notes в таблицу order_statuses
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.myconfbot.utils.database import db_manager

def upgrade():
    """Добавляем поле admin_notes в order_statuses"""
    try:
        # Для SQLite
        if db_manager.get_db_type() == 'sqlite':
            # Проверяем существование поля
            check_query = """
                PRAGMA table_info(order_statuses);
            """
            columns = db_manager.execute_query(check_query)
            
            # Ищем поле admin_notes
            has_admin_notes = any(col['name'] == 'admin_notes' for col in columns)
            
            if not has_admin_notes:
                # Добавляем поле
                alter_query = """
                    ALTER TABLE order_statuses 
                    ADD COLUMN admin_notes TEXT;
                """
                db_manager.execute_query(alter_query)
                print("✅ Поле admin_notes добавлено в order_statuses (SQLite)")
            else:
                print("✅ Поле admin_notes уже существует (SQLite)")
                
        # Для PostgreSQL
        else:
            # Проверяем существование поля
            check_query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'order_statuses' AND column_name = 'admin_notes';
            """
            result = db_manager.execute_query(check_query)
            
            if not result:
                # Добавляем поле
                alter_query = """
                    ALTER TABLE order_statuses 
                    ADD COLUMN admin_notes TEXT;
                """
                db_manager.execute_query(alter_query)
                print("✅ Поле admin_notes добавлено в order_statuses (PostgreSQL)")
            else:
                print("✅ Поле admin_notes уже существует (PostgreSQL)")
                
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
        raise

def downgrade():
    """Удаляем поле admin_notes из order_statuses"""
    try:
        if db_manager.get_db_type() == 'sqlite':
            # SQLite не поддерживает DROP COLUMN, нужно создать новую таблицу
            print("⚠️ SQLite не поддерживает DROP COLUMN. Пропускаем downgrade.")
        else:
            # Для PostgreSQL
            alter_query = """
                ALTER TABLE order_statuses 
                DROP COLUMN IF EXISTS admin_notes;
            """
            db_manager.execute_query(alter_query)
            print("✅ Поле admin_notes удалено из order_statuses (PostgreSQL)")
            
    except Exception as e:
        print(f"❌ Ошибка при откате миграции: {e}")
        raise

if __name__ == "__main__":
    upgrade()