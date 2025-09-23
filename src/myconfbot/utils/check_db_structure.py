# check_db_structure.py
from src.myconfbot.utils.database import DatabaseManager
from sqlalchemy import text

def check_table_structure():
    """Показывает текущую структуру таблицы product_photos"""
    
    with DatabaseManager.connect() as conn:
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'product_photos'
            ORDER BY ordinal_position
        """
        
        result = conn.execute(text(query))
        print("📋 Структура таблицы product_photos:")
        print("-" * 60)
        for row in result:
            print(f"{row[0]:<15} {row[1]:<20} {row[2]:<10} {row[3] or ''}")

if __name__ == "__main__":
    check_table_structure()