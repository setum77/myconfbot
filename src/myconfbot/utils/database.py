import os
import sqlite3
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from dotenv import load_dotenv

# Импортируем модели для создания таблиц
from src.myconfbot.models import Base, Order, Product, Category, OrderStatus, User

from src.myconfbot.config import Config

# Загрузка переменных окружения
load_dotenv()

class DatabaseManager:
    _instance = None
    _engine = None
    _Session = None
    _current_db_type = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.use_postgres = os.getenv('USE_POSTGRES', 'false').lower() == 'true'
            self._initialize_engine()
            self._initialized = True
    
    def _initialize_engine(self):
        """Инициализация движка БД в зависимости от настроек"""
        if self.use_postgres:
            self._setup_postgresql()
            self._current_db_type = 'postgresql'
        else:
            self._setup_sqlite()
            self._current_db_type = 'sqlite'
    
    def _setup_postgresql(self):
        """Настройка PostgreSQL соединения"""
        try:
            self._engine = create_engine(
                f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
                f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
            )
            self._Session = scoped_session(sessionmaker(bind=self._engine))
            # self._Session = sessionmaker(bind=self.engine)  # Должно быть self.Session
            # Base.metadata.create_all(self.engine)

            print("✓ Используется PostgreSQL база данных")
        except Exception as e:
            print(f"❌ Ошибка подключения к PostgreSQL: {e}")
            print("⚠️  Переключаюсь на SQLite...")
            self.use_postgres = False
            self._setup_sqlite()
    
    def _setup_sqlite(self):
        """Настройка SQLite соединения"""
        os.makedirs('data', exist_ok=True)
        self._engine = create_engine('sqlite:///data/confbot.db')
        self._Session = scoped_session(sessionmaker(bind=self._engine))
        print("✓ Используется SQLite база данных")
    
    def switch_to_postgresql(self):
        """Переключение на PostgreSQL (для миграции)"""
        if self._current_db_type == 'postgresql':
            print("⚠️  Уже используется PostgreSQL")
            return False
        
        print("🔄 Переключение на PostgreSQL...")
        self.use_postgres = True
        old_session = self._Session
        self._initialize_engine()
        
        if old_session:
            old_session.remove()
        
        return self._current_db_type == 'postgresql'
    
    def switch_to_sqlite(self):
        """Переключение на SQLite (для отката)"""
        if self._current_db_type == 'sqlite':
            print("⚠️  Уже используется SQLite")
            return False
        
        print("🔄 Переключение на SQLite...")
        self.use_postgres = False
        old_session = self._Session
        self._initialize_engine()
        
        if old_session:
            old_session.remove()
        
        return self._current_db_type == 'sqlite'
    
    def get_db_type(self):
        """Получение типа текущей БД"""
        return self._current_db_type
    
    def init_db(self):
        """Инициализация базы данных"""
        Base.metadata.create_all(self._engine)
        print(f"✓ Таблицы созданы в {self._current_db_type}")
    
    def get_session(self):
        """Получение сессии БД"""
        return self._Session()
    
    def close_session(self):
        """Закрытие сессии"""
        self._Session.remove()
    
    @contextmanager
    def session_scope(self):
        """Контекстный менеджер для сессий"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session()
    
    # --- RAW SQL методы для совместимости ---
    
    def raw_execute(self, query, params=None):
        """Выполнение raw SQL запроса"""
        if self.use_postgres:
            return self._raw_postgres(query, params)
        else:
            return self._raw_sqlite(query, params)
    
    def _raw_postgres(self, query, params):
        """Raw запрос для PostgreSQL"""
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return cur.fetchall()
                else:
                    conn.commit()
                    return cur.rowcount
        finally:
            conn.close()
    
    def _raw_sqlite(self, query, params):
        """Raw запрос для SQLite"""
        conn = sqlite3.connect('data/confbot.db')
        conn.row_factory = sqlite3.Row
        
        try:
            cur = conn.cursor()
            cur.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                result = cur.fetchall()
                return [dict(row) for row in result]
            else:
                conn.commit()
                return cur.rowcount
        finally:
            conn.close()
    
    def get_user_raw(self, telegram_id):
        """Получение пользователя через raw SQL"""
        if self.use_postgres:
            query = "SELECT * FROM customers WHERE telegram_id = %s"
        else:
            query = "SELECT * FROM customers WHERE telegram_id = ?"
        
        result = self.raw_execute(query, (telegram_id,))
        return result[0] if result else None
    
    # Старый блок работы с Юзерами с разбивкой на клиентов и админов
    # def add_customer(self, telegram_id, first_name, username=None, phone=None):
    #     """Добавление нового клиента"""
    #     with self.session_scope() as session:
    #         customer = Customer(
    #             telegram_id=telegram_id,
    #             first_name=first_name,
    #             username=username,
    #             phone=phone,
    #             characteristic=CustomerCharacteristic.NEW
    #         )
    #         session.add(customer)
    #         return customer
    
    # def get_customer_by_telegram_id(self, telegram_id):
    #     """Поиск клиента по telegram_id"""
    #     with self.session_scope() as session:
    #         return session.query(Customer).filter_by(telegram_id=telegram_id).first()

    # def add_admin(self, telegram_id, first_name, username=None, phone=None, address=None):
    #     """Добавление нового администратора"""
    #     with self.session_scope() as session:
    #         from src.myconfbot.models import Admin
    #         admin = Admin(
    #             telegram_id=telegram_id,
    #             first_name=first_name,
    #             username=username,
    #             phone=phone,
    #             address=address
    #         )
    #         session.add(admin)
    #         return admin
    
    # def get_admin_by_telegram_id(self, telegram_id):
    #     """Поиск администратора по telegram_id"""
    #     with self.session_scope() as session:
    #         from src.myconfbot.models import Admin
    #         return session.query(Admin).filter_by(telegram_id=telegram_id).first()
    
    # def is_admin(self, telegram_id):
    #     """Проверка, является ли пользователь администратором"""
    #     return self.get_admin_by_telegram_id(telegram_id) is not None
    
    # def update_admin_info(self, telegram_id, phone, address):
    #     """Обновление информации администратора"""
    #     with self.session_scope() as session:
    #         from src.myconfbot.models import Admin
    #         admin = session.query(Admin).filter_by(telegram_id=telegram_id).first()
    #         if admin:
    #             admin.phone = phone
    #             admin.address = address
    #             return True
    #         return False
    
    # def update_customer_characteristic(self, telegram_id, characteristic):
    #     """Обновление характеристики клиента"""
    #     with self.session_scope() as session:
    #         customer = session.query(Customer).filter_by(telegram_id=telegram_id).first()
    #         if customer:
    #             customer.characteristic = characteristic
    #             return True
    #         return False
    
    # Новый блок работы с юзерами с учетом новой таблицы Postgres
    def add_user(self, telegram_id, full_name, telegram_username=None, phone=None, is_admin=False):
        """Добавление нового пользователя"""
        with self.session_scope() as session:
            user = User(
                telegram_id=telegram_id,
                full_name=full_name,
                telegram_username=telegram_username,
                phone=phone,
                is_admin=is_admin
            )
            session.add(user)
            return user

    def get_user_by_telegram_id(self, telegram_id):
        """Поиск пользователя по telegram_id"""
        with self.session_scope() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                session.expunge(user)  # Отключаем объект от сессии
            return user

    def is_admin(self, telegram_id):
        """Проверка, является ли пользователь администратором"""
        with self.session_scope() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            return user.is_admin if user else False

    def update_user_info(self, telegram_id, full_name=None, phone=None, address=None, characteristics=None, photo_path=None):
        """Обновление информации пользователя"""
        with self.session_scope() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                if full_name: user.full_name = full_name
                if phone: user.phone = phone
                if address: user.address = address
                if characteristics: user.characteristics = characteristics
                if photo_path: user.photo_path = photo_path
                return True
            return False
    
    def get_orders_by_status(self, status_list):
        """Получение заказов по статусу"""
        with self.session_scope() as session:
            return session.query(Order).filter(Order.status.in_(status_list)).all()
    
    def get_orders_statistics(self):
        """Получение статистики заказов"""
        with self.session_scope() as session:
            from sqlalchemy import func
            from src.myconfbot.models import OrderStatus
            
            stats = {
                'total': session.query(Order).count(),
                'completed': session.query(Order).filter_by(status=OrderStatus.COMPLETED).count(),
                'in_progress': session.query(Order).filter_by(status=OrderStatus.IN_PROGRESS).count(),
                'new': session.query(Order).filter_by(status=OrderStatus.NEW).count(),
                'total_amount': session.query(func.sum(Order.total_amount)).scalar() or 0
            }
            return stats

    def test_connection(self):
        """Тестирование подключения к БД"""
        try:
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))
            print("✅ Подключение к БД успешно")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к БД: {e}")
            return False
    
    def update_order_status(self, order_id, status):
        """Обновление статуса заказа"""
        with self.session_scope() as session:
            order = session.query(Order).filter_by(id=order_id).first()
            if order:
                order.status = status
                return True
            return False
    
    def get_all_users(self):
        """Получить всех пользователей"""
        try:
            with self.session_scope() as session:  # Используем session_scope вместо прямого доступа к Session
                users = session.query(User).all()
                # Отключаем объекты от сессии чтобы избежать проблем с lazy loading
                for user in users:
                    session.expunge(user)
                return users
        except Exception as e:
            logging.error(f"Ошибка при получении пользователей: {e}")
        return []

    def update_user_characteristic(self, telegram_id, characteristic):
        """Обновить характеристику пользователя"""
        try:
            with self.session_scope() as session:  # Используем session_scope
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    user.characteristics = characteristic
                    return True
            return False
        except Exception as e:
            logging.error(f"Ошибка при обновлении характеристики: {e}")
            return False
    

    
# Глобальный экземпляр менеджера БД
db_manager = DatabaseManager()