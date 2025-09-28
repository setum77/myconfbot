# src\myconfbot\utils\database.py

import logging
logger = logging.getLogger(__name__)

import os
import sqlite3
import logging
from typing import Optional, Dict, List
from src.myconfbot.config import Config
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from datetime import datetime
from dotenv import load_dotenv

# Импортируем модели для создания таблиц
from .models import Base, Order, Product, Category, OrderStatus, User, ProductPhoto, OrderStatusEnum

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
        os.makedirs('data', exist_ok=True)
        if not self._initialized:
            self.use_postgres = os.getenv('USE_POSTGRES', 'false').lower() == 'true'
            self._initialize_engine()
            self._create_tables()
            self._initialized = True
    
    def _initialize_engine(self):
        """Инициализация движка БД в зависимости от настроек"""
        try:
            if self.use_postgres:
                self._setup_postgresql()
                self._current_db_type = 'postgresql'
            else:
                self._setup_sqlite()
                self._current_db_type = 'sqlite'
            
            logger.info(f"✓ Используется {self._current_db_type} база данных")
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise
    
    def _setup_postgresql(self):
        """Настройка PostgreSQL соединения"""
        try:
            db_user = os.getenv('DB_USER')
            db_password = os.getenv('DB_PASSWORD')
            db_host = os.getenv('DB_HOST')
            db_port = os.getenv('DB_PORT')
            db_name = os.getenv('DB_NAME')
            
            if not all([db_user, db_password, db_host, db_port, db_name]):
                raise ValueError("Не все переменные окружения для PostgreSQL заданы")
            
            self._engine = create_engine(
                f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",
                pool_pre_ping=True,  # Проверка соединения перед использованием
                echo=False  # Установите True для отладки SQL запросов
            )
            self._Session = scoped_session(sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False
            ))
            
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}")
            raise
    
    def _setup_sqlite(self):
        """Настройка SQLite соединения"""
        try:
            os.makedirs('data', exist_ok=True)
            self._engine = create_engine(
                'sqlite:///data/confbot.db',
                connect_args={'check_same_thread': False}  # Для многопоточности
            )
            self._Session = scoped_session(sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False
            ))
        except Exception as e:
            logger.error(f"❌ Ошибка настройки SQLite: {e}")
            raise
    
    def _create_tables(self):
        """Создание таблиц в базе данных"""
        try:
            Base.metadata.create_all(self._engine)
            logger.info(f"✓ Таблицы созданы/проверены в {self._current_db_type}")
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблиц: {e}")
            raise
    
    def switch_database(self, use_postgres: bool):
        """Переключение между базами данных"""
        if self.use_postgres == use_postgres:
            logger.warning(f"⚠️  Уже используется {'PostgreSQL' if use_postgres else 'SQLite'}")
            return False
        
        try:
            old_session = self._Session
            self.use_postgres = use_postgres
            self._initialize_engine()
            
            if old_session:
                old_session.remove()
            
            logger.info(f"🔄 Успешно переключено на {'PostgreSQL' if use_postgres else 'SQLite'}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка переключения БД: {e}")
            return False
    
    def switch_to_postgresql(self):
        """Переключение на PostgreSQL"""
        return self.switch_database(True)
    
    def switch_to_sqlite(self):
        """Переключение на SQLite"""
        return self.switch_database(False)
    
    def get_db_type(self):
        """Получение типа текущей БД"""
        return self._current_db_type
    
    def init_db(self):
        """Инициализация базы данных (алиас для обратной совместимости)"""
        self._create_tables()
    
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
            logger.error(f"Ошибка в сессии БД: {e}")
            raise
        finally:
            session.close()

    def execute_query(self, query: str, params: dict = None, fetch_one: bool = False):
        """Выполнение SQL запроса с возвращением результата"""
        try:
            with self.session_scope() as session:
                result = session.execute(text(query), params or {})
                
                if query.strip().upper().startswith('SELECT'):
                    if fetch_one:
                        row = result.fetchone()
                        return dict(row._mapping) if row else None
                    else:
                        rows = result.fetchall()
                        return [dict(row._mapping) for row in rows]
                else:
                    session.commit()
                    return result.rowcount
                    
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            return None
    
    # def execute_query(self, query: str, params: tuple = None, fetch_one: bool = False):
        
        
        # """Выполнение SQL запроса с возвращением результата"""
        # try:
        #     with self.session_scope() as session:
        #         # Преобразуем параметры в словарь, если они переданы как кортеж
        #         if isinstance(params, tuple):
        #             # Создаем словарь параметров с именами :param1, :param2 и т.д.
        #             params_dict = {f'param{i}': value for i, value in enumerate(params, 1)}
        #             # Заменяем плейсхолдеры в запросе
        #             query = query.replace('%s', ':param1').replace('?', ':param1')
        #             for i in range(2, len(params) + 1):
        #                 query = query.replace('%s', f':param{i}').replace('?', f':param{i}')
        #         else:
        #             params_dict = params or {}
                
        #         result = session.execute(text(query), params_dict)
                
        #         if query.strip().upper().startswith('SELECT'):
        #             if fetch_one:
        #                 row = result.fetchone()
        #                 return dict(row._mapping) if row else None
        #             else:
        #                 rows = result.fetchall()
        #                 return [dict(row._mapping) for row in rows]
        #         else:
        #             session.commit()
        #             return result.rowcount
                    
        # except Exception as e:
        #     logger.error(f"Ошибка выполнения запроса: {e}")
        #     raise
    
    # --- Методы для работы с пользователями ---
    
    def add_user(self, telegram_id: int, full_name: str, telegram_username: str = None, 
                phone: str = None, is_admin: bool = False) -> User:
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
    
    def get_user_info(self, telegram_id: int) -> Optional[Dict]:
        """Получить информацию о пользователе в виде словаря"""
        with self._Session() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                return {
                    'id': user.id,
                    'telegram_id': user.telegram_id,
                    'full_name': user.full_name,
                    'telegram_username': user.telegram_username,
                    'is_admin': user.is_admin,
                    'phone': user.phone,
                    'address': user.address,
                    'characteristics': user.characteristics,
                    'photo_path': user.photo_path,
                    'created_at': user.created_at
                }
            return None
    
    def get_all_users_info(self) -> List[dict]:
        """Получить информацию о всех пользователях в виде списка словарей"""
        with self._Session() as session:
            users = session.query(User).all()
            return [
                {
                    'id': user.id,
                    'telegram_id': user.telegram_id,
                    'full_name': user.full_name,
                    'telegram_username': user.telegram_username,
                    'is_admin': user.is_admin,
                    'phone': user.phone,
                    'address': user.address,
                    'characteristics': user.characteristics,
                    'photo_path': user.photo_path,
                    'created_at': user.created_at
                }
                for user in users
            ]
    
    def get_user_by_telegram_id(self, telegram_id: int) -> User:
        """Поиск пользователя по telegram_id"""
        with self.session_scope() as session:
            return session.query(User).filter_by(telegram_id=telegram_id).first()
    
    def get_or_create_user(self, telegram_id: int, full_name: str, 
                          telegram_username: str = None) -> User:
        """Получить пользователя или создать нового"""
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            user = self.add_user(telegram_id, full_name, telegram_username)
        return user
    
    def is_admin(self, telegram_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        user = self.get_user_by_telegram_id(telegram_id)
        return user.is_admin if user else False
    
    def update_user_info(self, telegram_id: int, **kwargs) -> bool:
        """Обновление информации пользователя"""
        with self.session_scope() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key) and value is not None:
                        setattr(user, key, value)
                return True
            return False
    
    def get_all_users(self) -> list:
        """Получить всех пользователей"""
        try:
            session = self._Session()
            users = session.query(User).all()
            return users
        except Exception as e:
            logger.error(f"Ошибка при получении пользователей: {e}")
            return []
        finally:
            session.close()



    def update_user_characteristic(self, telegram_id: int, characteristic: str) -> bool:
        """Обновить характеристику пользователя"""
        try:
            with self.session_scope() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    user.characteristics = characteristic
                    return True
                return False
        except Exception as e:
            logger.error(f"Ошибка при обновлении характеристики: {e}")
            return False
                
    # def update_user_characteristic(self, telegram_id: int, characteristic: str) -> bool:
    #     """Обновить характеристику пользователя"""
    #     session = None
    #     try:
    #         session = self._Session()
    #         user = session.query(User).filter(User.telegram_id == telegram_id).first()
    #         if user:
    #             user.characteristics = characteristic
    #             session.commit()
    #             return True
    #         return False
    #     except Exception as e:
    #         if session: 
    #             session.rollback()
    #         logger.error(f"Ошибка при обновлении характеристики: {e}")
    #         return False
    #     finally:
    #         if session:
    #             session.close()
        
    # --- Методы для работы с заказами ---

    def create_order(self, order_data: dict) -> Optional[Order]:
        """Создание нового заказа"""
        try:
            with self.session_scope() as session:
                order = Order(
                    user_id=order_data['user_id'],
                    product_id=order_data['product_id'],
                    quantity=order_data.get('quantity', 1),
                    weight_grams=order_data.get('weight_grams'),
                    delivery_type=order_data.get('delivery_type'),
                    delivery_address=order_data.get('delivery_address'),
                    ready_at=order_data.get('ready_at'),
                    total_cost=order_data.get('total_cost'),
                    payment_type=order_data.get('payment_type'),
                    payment_status=order_data.get('payment_status', 'Не оплачен'),
                    admin_notes=order_data.get('admin_notes')
                )
                session.add(order)
                session.flush()  # Получаем ID заказа
                
                # Создаем начальный статус заказа
                initial_status = OrderStatus(
                    order_id=order.id,
                    status=OrderStatusEnum.CREATED.value,
                    created_at=datetime.utcnow()
                )
                session.add(initial_status)
                
                return order
        except Exception as e:
            logger.error(f"Ошибка при создании заказа: {e}")
            return None

    def get_orders_by_user(self, user_id: int) -> List[dict]:
        """Получить заказы пользователя"""
        try:
            with self.session_scope() as session:
                orders = session.query(Order).filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
                return [
                    {
                        'id': order.id,
                        'product_name': order.product.name,
                        'quantity': order.quantity,
                        'total_cost': float(order.total_cost) if order.total_cost else 0,
                        'created_at': order.created_at,
                        'delivery_type': order.delivery_type,
                        'payment_status': order.payment_status,
                        'current_status': self.get_current_order_status(order.id)
                    }
                    for order in orders
                ]
        except Exception as e:
            logger.error(f"Ошибка при получении заказов пользователя: {e}")
            return []

    def get_current_order_status(self, order_id: int) -> str:
        """Получить текущий статус заказа"""
        try:
            with self.session_scope() as session:
                last_status = session.query(OrderStatus).filter_by(
                    order_id=order_id
                ).order_by(OrderStatus.created_at.desc()).first()
                
                return last_status.status if last_status else OrderStatusEnum.CREATED.value
        except Exception as e:
            logger.error(f"Ошибка при получении статуса заказа: {e}")
            return OrderStatusEnum.CREATED.value

    def update_order_status(self, order_id: int, status: OrderStatusEnum, photo_path: str = None) -> bool:
        """Обновить статус заказа"""
        try:
            with self.session_scope() as session:
                # Создаем новую запись в истории статусов
                order_status = OrderStatus(
                    order_id=order_id,
                    status=status.value,
                    photo_path=photo_path,
                    created_at=datetime.utcnow()
                )
                session.add(order_status)
                return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса заказа: {e}")
            return False

    def get_orders_by_status(self, status: OrderStatusEnum) -> list:
        """Получить заказы по статусу"""
        try:
            with self.session_scope() as session:
                # Находим заказы с указанным последним статусом
                subquery = session.query(
                    OrderStatus.order_id,
                    sa.func.max(OrderStatus.created_at).label('max_date')
                ).group_by(OrderStatus.order_id).subquery()
                
                orders_with_status = session.query(Order).join(
                    OrderStatus
                ).join(
                    subquery,
                    sa.and_(
                        OrderStatus.order_id == subquery.c.order_id,
                        OrderStatus.created_at == subquery.c.max_date
                    )
                ).filter(OrderStatus.status == status.value).all()
                
                return orders_with_status
        except Exception as e:
            logger.error(f"Ошибка при получении заказов по статусу: {e}")
            return []

    def get_orders_statistics(self) -> dict:
        """Получить статистику заказов"""
        try:
            with self.session_scope() as session:
                # Подзапрос для получения последнего статуса каждого заказа
                subquery = session.query(
                    OrderStatus.order_id,
                    sa.func.max(OrderStatus.created_at).label('max_date')
                ).group_by(OrderStatus.order_id).subquery()
                
                # Запрос для получения последних статусов
                last_statuses = session.query(
                    OrderStatus.order_id,
                    OrderStatus.status
                ).join(
                    subquery,
                    sa.and_(
                        OrderStatus.order_id == subquery.c.order_id,
                        OrderStatus.created_at == subquery.c.max_date
                    )
                ).subquery()
                
                # Статистика по статусам
                status_stats = session.query(
                    last_statuses.c.status,
                    sa.func.count(last_statuses.c.order_id)
                ).group_by(last_statuses.c.status).all()
                
                result = {
                    'total': session.query(Order).count(),
                    'total_amount': session.query(sa.func.sum(Order.total_cost)).scalar() or 0
                }
                
                # Добавляем статистику по каждому статусу
                for status_enum in OrderStatusEnum:
                    result[status_enum.name.lower()] = 0
                
                for status_name, count in status_stats:
                    for status_enum in OrderStatusEnum:
                        if status_enum.value == status_name:
                            result[status_enum.name.lower()] = count
                            break
                
                return result
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return {'total': 0, 'total_amount': 0}
        
    # --- Raw SQL методы для совместимости ---
    
    def raw_execute(self, query: str, params: tuple = None):
        """Выполнение raw SQL запроса"""
        try:
            if self.use_postgres:
                return self._raw_postgres(query, params)
            else:
                return self._raw_sqlite(query, params)
        except Exception as e:
            logger.error(f"Ошибка выполнения raw SQL: {e}")
            raise
    
    # def _raw_postgres(self, query: str, params: tuple):
    #     """Raw запрос для PostgreSQL"""
    #     import psycopg2
    #     from psycopg2.extras import RealDictCursor
        
    #     conn = psycopg2.connect(
    #         host=os.getenv('DB_HOST'),
    #         database=os.getenv('DB_NAME'),
    #         user=os.getenv('DB_USER'),
    #         password=os.getenv('DB_PASSWORD'),
    #         port=os.getenv('DB_PORT')
    #     )
        
    #     try:
    #         with conn.cursor(cursor_factory=RealDictCursor) as cur:
    #             cur.execute(query, params)
    #             if query.strip().upper().startswith('SELECT'):
    #                 return cur.fetchall()
    #             else:
    #                 conn.commit()
    #                 return cur.rowcount
    #     finally:
    #         conn.close()
    
    # def _raw_sqlite(self, query: str, params: tuple):
    #     """Raw запрос для SQLite"""
    #     conn = sqlite3.connect('data/confbot.db')
    #     conn.row_factory = sqlite3.Row
        
    #     try:
    #         cur = conn.cursor()
    #         cur.execute(query, params)
            
    #         if query.strip().upper().startswith('SELECT'):
    #             result = cur.fetchall()
    #             return [dict(row) for row in result]
    #         else:
    #             conn.commit()
    #             return cur.rowcount
    #     finally:
    #         conn.close()
    
    def get_user_raw(self, telegram_id: int):
        """Получение пользователя через raw SQL"""
        if self.use_postgres:
            query = "SELECT * FROM users WHERE telegram_id = %s"
        else:
            query = "SELECT * FROM users WHERE telegram_id = ?"
        
        result = self.raw_execute(query, (telegram_id,))
        return result[0] if result else None
    
    def test_connection(self) -> bool:
        """Тестирование подключения к БД"""
        try:
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))
            logger.info("✅ Подключение к БД успешно")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            return False
        
    # --- Методы для работы с примечаниями к заказам ---

    def add_order_note(self, order_id: int, user_id: int, note_text: str) -> bool:
        """Добавить примечание к заказу"""
        try:
            with self.session_scope() as session:
                note = OrderNote(
                    order_id=order_id,
                    user_id=user_id,
                    note_text=note_text,
                    created_at=datetime.utcnow()
                )
                session.add(note)
                return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении примечания к заказу: {e}")
            return False

    def get_order_notes(self, order_id: int) -> List[dict]:
        """Получить примечания к заказу"""
        try:
            with self.session_scope() as session:
                notes = session.query(OrderNote).filter_by(
                    order_id=order_id
                ).order_by(OrderNote.created_at).all()
                
                return [
                    {
                        'id': note.id,
                        'user_name': note.user.full_name,
                        'note_text': note.note_text,
                        'created_at': note.created_at
                    }
                    for note in notes
                ]
        except Exception as e:
            logger.error(f"Ошибка при получении примечаний к заказу: {e}")
            return []
    
    # --- Методы для работы с продукцийе и категориями ---

    def add_product(self, product_data: dict) -> bool:
        """Добавить новый товар"""
        try:
            session = self._Session()
            product = Product(
                name=product_data.get('name'),
                category_id=product_data.get('category_id'),
                cover_photo_path=product_data.get('cover_photo_path', ''),
                short_description=product_data.get('short_description', ''),
                is_available=product_data.get('is_available', True),
                measurement_unit=product_data.get('measurement_unit', 'шт'),
                quantity=product_data.get('quantity', 0),
                price=product_data.get('price', 0),
                prepayment_conditions=product_data.get('prepayment_conditions', '')
            )
            session.add(product)
            session.commit()
            logger.info(f"Товар '{product.name}' успешно добавлен с ID {product.id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при добавлении товара: {e}")
            return False
        finally:
            session.close()

    # -- НАЧАЛО УПРАВЛЕНИЕ КАТЕГОРИЯМИ
    
    def add_category(self, name: str, description: str = '') -> bool:
        """Добавить новую категорию"""
        try:
            session = self._Session()
            
            # Проверяем, существует ли уже категория с таким названием
            existing_category = session.query(Category).filter_by(name=name).first()
            if existing_category:
                logger.warning(f"Категория с названием '{name}' уже существует")
                return False
            
            category = Category(
                name=name,
                description=description
            )
            session.add(category)
            session.commit()
            logger.info(f"Категория '{name}' успешно добавлена")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при добавлении категории: {e}")
            return False
        finally:
            session.close()

    # def add_category(self, name: str, description: str = "") -> bool:
    #     """Добавить категорию"""
    #     try:
    #         self.cursor.execute(
    #             "INSERT INTO categories (name, description) VALUES (?, ?)",
    #             (name, description)
    #         )
    #         self.conn.commit()
    #         return True
    #     except Exception as e:
    #         logger.error(f"Ошибка при добавлении категории: {e}")
    #         return False

    # def get_category_by_id(self, category_id: int) -> Optional[dict]:
    #     """Получить категорию по ID"""
    #     try:
    #         return self.session.query(Category).filter(Category.id == category_id).first()
    #     except Exception as e:
    #         logger.error(f"Ошибка при получении категории {category_id}: {e}")
    #         return None
    
    def get_category_by_id(self, category_id: int) -> Optional[dict]:
        """Получить категорию по ID"""
        try:
            with self.session_scope() as session:
                category = session.query(Category).filter_by(id=category_id).first()
                if category:
                    return {
                        'id': category.id,
                        'name': category.name,
                        'description': category.description,
                        'created_at': category.created_at,
                    }
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении товара: {e}")
            return None
    
    # def get_category_by_id(self, category_id: int) -> Optional[dict]:
    #     """Получить категорию по ID"""
    #     try:
    #         self.cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
    #         result = self.cursor.fetchone()
    #         return dict(result) if result else None
    #     except Exception as e:
    #         logger.error(f"Ошибка при получении категории по ID {category_id}: {e}")
    #         return None

    # def get_all_categories(self):
    #     """Получить все категории"""
    #     try:
    #         return self.session.query(Category).order_by(Category.name).all()
    #     except Exception as e:
    #         logger.error(f"Ошибка при получении категорий: {e}")
    #         return []

    def get_all_categories(self) -> List[dict]:
        """Получить все категории"""
        try:
            session = self._Session()
            categories = session.query(Category).order_by(Category.name).all()
            return [
                {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description
                }
                for category in categories
            ]
        except Exception as e:
            logger.error(f"Ошибка при получении категорий: {e}")
            return []
        finally:
            session.close()

    # def get_all_categories(self) -> List[dict]:
    #     """Получить все категории"""
    #     try:
    #         self.cursor.execute("SELECT * FROM categories ORDER BY name")
    #         results = self.cursor.fetchall()
    #         return [dict(row) for row in results]
    #     except Exception as e:
    #         logger.error(f"Ошибка при получении категорий: {e}")
    #         return []

    # def update_category_name(self, category_id: int, new_name: str) -> bool:
    #     """Обновить название категории"""
    #     try:
    #         category = self._get_category_by_id(category_id)
    #         if category:
    #             category.name = new_name
    #             self.session.commit()
    #             return True
    #         return False
    #     except Exception as e:
    #         logger.error(f"Ошибка при обновлении названия категории {category_id}: {e}")
    #         self.session.rollback()
    #         return False

    # def update_category_description(self, category_id: int, new_description: str) -> bool:
    #     """Обновить описание категории"""
    #     try:
    #         category = self._get_category_by_id(category_id)
    #         if category:
    #             category.description = new_description
    #             self.session.commit()
    #             return True
    #         return False
    #     except Exception as e:
    #         logger.error(f"Ошибка при обновлении описания категории {category_id}: {e}")
    #         self.session.rollback()
    #         return False

    def update_category_field(self, category_id: int, field: str, value: str) -> bool:
        """Обновление поля категории"""
        try:
            with self.session_scope() as session:
                category = session.query(Category).filter_by(id=category_id).first()
                if category:
                    if hasattr(category, field):
                        setattr(category, field, value)
                        return True
                return False
        except Exception as e:
            logger.error(f"Ошибка при обновлении поля категории {category_id}.{field}: {e}")
            return False
        
    def _delete_category(self, category_id: int) -> bool:
        """Удалить категорию"""
        try:
            with self.session_scope() as session:
                # Получаем категорию
                category = session.query(Category).filter_by(id=category_id).first()
                if category:
                    # Обнуляем category_id у связанных товаров
                    products = session.query(Product).filter_by(category_id=category_id).all()
                    for product in products:
                        product.category_id = None
                    
                    # Удаляем категорию
                    session.delete(category)
                    return True
                return False
        except Exception as e:
            logger.error(f"Ошибка при удалении категории {category_id}: {e}")
            return False

    # -- КОНЕЦ УПРАВЛЕНИЯ КАТЕГОРИЯМИ --

    def add_product_returning_id(self, product_data: dict) -> int:
        """Добавление товара и возвращение ID с использованием ORM"""
        try:
            with self.session_scope() as session:
                product = Product(
                    name=product_data.get('name'),
                    category_id=product_data.get('category_id'),
                    cover_photo_path=product_data.get('cover_photo_path', ''),
                    short_description=product_data.get('short_description', ''),
                    price=float(product_data.get('price', 0)),
                    is_available=bool(product_data.get('is_available', True)),
                    measurement_unit=product_data.get('measurement_unit', 'шт'),
                    quantity=float(product_data.get('quantity', 0)),
                    prepayment_conditions=product_data.get('prepayment_conditions', '')
                )
                session.add(product)
                session.flush()  # Получаем ID без коммита
                product_id = product.id
                return product_id
                
        except Exception as e:
            logger.error(f"Ошибка при добавлении товара: {e}")
            return None

    def update_product(self, product_id: int, product_data: dict) -> bool:
        """Обновление товара"""
        try:
            query = """
                UPDATE products 
                SET cover_photo_path = %s, additional_photos = %s
                WHERE id = %s
            """
            # Конвертируем список фото в JSON или текст
            additional_photos = product_data.get('additional_photos', [])
            photos_str = ','.join(additional_photos)  # или используйте json.dumps()
            
            params = (
                product_data.get('cover_photo_path', ''),
                photos_str,
                product_id
            )
            
            self.execute_query(query, params)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении товара: {e}")
            return False
    
    # def update_product_field(self, product_id: int, field: str, value) -> bool:
    #     """Обновление конкретного поля товара"""
    #     try:
    #         query = f"UPDATE products SET {field} = %s, updated_at = NOW() WHERE id = %s"
    #         # self.execute_query(query, (value, product_id))
    #         with self.Session() as session:
    #             session.execute(text(query), {'value': value, 'product_id': product_id})
    #             session.commit()
    #         return True
    #     except Exception as e:
    #         logger.error(f"Ошибка при обновлении поля {field}: {e}")
    #         return False

    def update_product_field(self, product_id: int, field: str, value) -> bool:
        """Обновление конкретного поля товара"""
        logger.info(f"Начало обновления: product_id={product_id}, field={field}, value={value}")
        try:
            # Защита от попытки обновить поле id
            if field == 'id':
                logger.error("Попытка обновить поле id запрещена")
                return False
                
            with self.session_scope() as session:
                product = session.query(Product).filter_by(id=product_id).first()
                if not product:
                    logger.error(f"Товар с ID {product_id} не найден")
                    return False
                    
                # Обновляем поле
                if hasattr(product, field):
                    setattr(product, field, value)
                    product.updated_at = datetime.utcnow()
                else:
                    logger.error(f"Поле {field} не существует в модели Product")
                    return False
                    
                session.commit()
            
            logger.info(f"Поле {field} товара {product_id} обновлено на: {value}")
            return True
            
        except Exception as e:
            error_msg = f"Ошибка при обновлении поля {field} товара {product_id}: {e}"
            logger.error(error_msg)
            return False
    
    def delete_product(self, product_id: int) -> bool:
        """Удаление товара из базы данных"""
        logger.info(f"DEBUG: DatabaseManager.delete_product called for {product_id}")
        try:
            with self.session_scope() as session:
                # Сначала удаляем фотографии
                photos_deleted = session.query(ProductPhoto).filter_by(product_id=product_id).delete()
                print(f"DEBUG: Deleted {photos_deleted} photos from database")
                # Затем удаляем товар
                product = session.query(Product).filter_by(id=product_id).first()
                if product:
                    session.delete(product)
                    print(f"DEBUG: Product {product_id} marked for deletion")
                    return True
            print(f"DEBUG: Product {product_id} not found in database")
            return False
        except Exception as e:
            logger.error(f"Ошибка при удалении товара: {e}")
            return False

    # --- Методы для работы с фотографиями продукции ---

    def add_product_photo(self, product_id: int, photo_path: str, is_main: bool = False) -> bool:
        """Добавление фото товара в БД"""
        try:
            logger.info(f"🔍 ДЕБАГ: add_product_photo called: product_id={product_id}, path={photo_path}, is_main={is_main}")
            
            with self.session_scope() as session:
                # Получаем максимальный order_index для этого товара
                max_order = session.query(func.max(ProductPhoto.order_index)).filter(
                    ProductPhoto.product_id == product_id
                ).scalar() or 0
                
                photo = ProductPhoto(
                    product_id=product_id,
                    photo_path=photo_path,
                    is_main=is_main,
                    order_index=max_order + 1  # Исправлено: было display_order
                )
                
                session.add(photo)
                session.commit()
                logger.info(f"✅ ДЕБАГ: Фото успешно добавлено в БД, ID: {photo.id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка в сессии БД: {e}")
            logger.error(f"❌ ДЕБАГ: Ошибка: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False                                                            

    def get_product_photos(self, product_id: int) -> List[dict]:
        """Получение всех фото товара"""
        try:
            with self.session_scope() as session:
                # photos = session.query(ProductPhoto).filter_by(product_id=product_id).order_by(ProductPhoto.id).all()
                photos = session.query(ProductPhoto).filter_by(product_id=product_id).order_by(ProductPhoto.is_main.desc(), ProductPhoto.id).all()

                return [
                    {
                        'id': photo.id,
                        'photo_path': photo.photo_path,
                        'is_main': photo.is_main
                    }
                    for photo in photos
                ]
        except Exception as e:
            logger.error(f"Ошибка при получении фото товара: {e}")
            return []

    def set_main_photo(self, product_id: int, photo_path: str) -> bool:
        """Установка основного фото"""
        try:
            with self.session_scope() as session:
                # Сбрасываем все is_main для этого товара
                session.query(ProductPhoto).filter_by(product_id=product_id).update({'is_main': False})
                
                # Устанавливаем новое основное фото
                photo = session.query(ProductPhoto).filter_by(product_id=product_id, photo_path=photo_path).first()
                if photo:
                    photo.is_main = True
                    return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при установке основного фото: {e}")
            return False

    def update_product_cover_photo(self, product_id: int, cover_photo_path: str) -> bool:
        """Обновление cover_photo_path в продукте"""
        try:
            with self.session_scope() as session:
                product = session.query(Product).filter_by(id=product_id).first()
                if product:
                    product.cover_photo_path = cover_photo_path
                    return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при обновлении основного фото: {e}")
            return False
    
    # --- Методы для вывода списка товаров ---

    # В класс DatabaseManager добавим методы:

    def get_products_by_category(self, category_id: int) -> List[dict]:
        """Получить товары по категории"""
        try:
            with self.session_scope() as session:
                products = session.query(Product).filter_by(category_id=category_id).order_by(Product.name).all()
                return [
                    {
                        'id': product.id,
                        'name': product.name,
                        'category_id': product.category_id,
                        'cover_photo_path': product.cover_photo_path,
                        'short_description': product.short_description,
                        'price': float(product.price),
                        'is_available': product.is_available,
                        'measurement_unit': product.measurement_unit,
                        'quantity': float(product.quantity),
                        'prepayment_conditions': product.prepayment_conditions,
                        'created_at': product.created_at,
                        'updated_at': product.updated_at
                    }
                    for product in products
                ]
        except Exception as e:
            logger.error(f"Ошибка при получении товаров по категории: {e}")
            return []

    def get_product_by_id(self, product_id: int) -> Optional[dict]:
        """Получить товар по ID"""
        try:
            with self.session_scope() as session:
                product = session.query(Product).filter_by(id=product_id).first()
                if product:
                    category = session.query(Category).filter_by(id=product.category_id).first()
                    return {
                        'id': product.id,
                        'name': product.name,
                        'category_id': product.category_id,
                        'category_name': category.name if category else 'Неизвестно',
                        'cover_photo_path': product.cover_photo_path,
                        'short_description': product.short_description,
                        'price': float(product.price),
                        'is_available': product.is_available,
                        'measurement_unit': product.measurement_unit,
                        'quantity': float(product.quantity),
                        'prepayment_conditions': product.prepayment_conditions,
                        'created_at': product.created_at,
                        'updated_at': product.updated_at
                    }
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении товара: {e}")
            return None

# Глобальный экземпляр менеджера БД
db_manager = DatabaseManager()