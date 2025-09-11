import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Импортируем модели для создания таблиц
from src.myconfbot.models import Base, Customer, Order, Product, Category, OrderStatus, CustomerCharacteristic
from src.myconfbot.config import Config


class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # Создаем папку data если её нет
            os.makedirs('data', exist_ok=True)
            
            # Используем фиксированный путь к БД
            self.engine = create_engine('sqlite:///data/confbot.db')
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            self._initialized = True
    
    def init_db(self):
        """Инициализация базы данных"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Получение сессии БД"""
        return self.Session()
    
    def close_session(self):
        """Закрытие сессии"""
        self.Session.remove()

    def add_customer(self, telegram_id, first_name, username=None, phone=None):
        """Добавление нового клиента"""
        session = self.get_session()
        try:
            customer = Customer(
                telegram_id=telegram_id,
                first_name=first_name,
                username=username,
                phone=phone,
                characteristic=CustomerCharacteristic.NEW
            )
            session.add(customer)
            session.commit()
            return customer
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session()

    def get_customer_by_telegram_id(self, telegram_id):
        """Поиск клиента по telegram_id"""
        session = self.get_session()
        try:
            return session.query(Customer).filter_by(telegram_id=telegram_id).first()
        finally:
            self.close_session()

    def update_customer_characteristic(self, telegram_id, characteristic):
        """Обновление характеристики клиента"""
        session = self.get_session()
        try:
            customer = session.query(Customer).filter_by(telegram_id=telegram_id).first()
            if customer:
                customer.characteristic = characteristic
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session()

    def add_admin(self, telegram_id, first_name, username=None, phone=None, address=None):
        """Добавление нового администратора"""
        session = self.get_session()
        try:
            from src.myconfbot.models import Admin  # Импорт внутри метода чтобы избежать циклических импортов
            
            admin = Admin(
                telegram_id=telegram_id,
                first_name=first_name,
                username=username,
                phone=phone,
                address=address
            )
            session.add(admin)
            session.commit()
            return admin
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session()

    def get_admin_by_telegram_id(self, telegram_id):
        """Поиск администратора по telegram_id"""
        session = self.get_session()
        try:
            from src.myconfbot.models import Admin
            return session.query(Admin).filter_by(telegram_id=telegram_id).first()
        finally:
            self.close_session()

    def is_admin(self, telegram_id):
        """Проверка, является ли пользователь администратором"""
        return self.get_admin_by_telegram_id(telegram_id) is not None

# Глобальный экземпляр менеджера БД
db_manager = DatabaseManager()