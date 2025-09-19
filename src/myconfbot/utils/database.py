import os
import sqlite3
import logging
from typing import Optional, Dict, List
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from dotenv import load_dotenv

# Импортируем модели для создания таблиц
from src.myconfbot.models import Base, Order, Product, Category, OrderStatus, User, ProductPhoto
from src.myconfbot.config import Config

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            self.logger.error(f"Ошибка при получении пользователей: {e}")
            return []
        finally:
            session.close()
                
    def update_user_characteristic(self, telegram_id: int, characteristic: str) -> bool:
        """Обновить характеристику пользователя"""
        session = None
        try:
            session = self._Session()
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.characteristics = characteristic
                session.commit()
                return True
            return False
        except Exception as e:
            if session: 
                session.rollback()
            logger.error(f"Ошибка при обновлении характеристики: {e}")
            return False
        finally:
            if session:
                session.close()
        
    # --- Методы для работы с заказами ---
    
    def get_orders_by_status(self, status_list: list) -> list:
        """Получить заказы по статусу"""
        try:
            session = self._Session()
            orders = session.query(Order).filter(Order.status.in_(status_list)).all()
            return orders
        except Exception as e:
            logger.error(f"Ошибка при получении заказов: {e}")
            return []
        finally:
            if session: 
                session.close()

    def get_orders_statistics(self) -> dict:
        """Получить статистику заказов"""
        try:
            session = self._Session()
            result = {
                'total': session.query(Order).count(),
                'completed': session.query(Order).filter(Order.status == OrderStatus.COMPLETED).count(),
                'in_progress': session.query(Order).filter(Order.status == OrderStatus.IN_PROGRESS).count(),
                'new': session.query(Order).filter(Order.status == OrderStatus.NEW).count(),
                'total_amount': session.query(func.sum(Order.total_amount)).scalar() or 0
            }
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return {'total': 0, 'completed': 0, 'in_progress': 0, 'new': 0, 'total_amount': 0}
        finally:
            if session: 
                session.close()
    

    def update_order_status(self, order_id: int, status: OrderStatus) -> bool:
        """Обновить статус заказа"""
        session = None  
        try:
            session = self._Session()
            order = session.query(Order).filter(Order.id == order_id).first()
            if order:
                order.status = status
                session.commit()
                return True
            return False
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Ошибка при обновлении статуса заказа: {e}")
            return False
        finally:
            if session: 
                session.close()
        
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
    
    def _raw_postgres(self, query: str, params: tuple):
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
    
    def _raw_sqlite(self, query: str, params: tuple):
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
    
    # --- Методы для работы с продукцийе и категориями ---

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

    # --- Методы для работы с фотографиями продукции ---

    def add_product_photo(self, product_id: int, photo_path: str, is_main: bool = False) -> bool:
        """Добавление фото товара"""
        try:
            with self.session_scope() as session:
                # Если устанавливаем как основное, сбрасываем предыдущее
                if is_main:
                    session.query(ProductPhoto).filter_by(product_id=product_id, is_main=True).update({'is_main': False})
                
                photo = ProductPhoto(
                    product_id=product_id,
                    photo_path=photo_path,
                    is_main=is_main
                )
                session.add(photo)
                return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении фото товара: {e}")
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