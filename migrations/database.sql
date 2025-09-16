-- Создание базы данных (выполняется отдельно)
-- CREATE DATABASE confectioner_bot;

-- Теперь подключаемся к созданной БД и создаем таблицы

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    telegram_username VARCHAR(100),
    full_name VARCHAR(200),
    phone VARCHAR(20),
    address TEXT,
    characteristics TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_admin BOOLEAN DEFAULT FALSE,
    photo_path VARCHAR(500)
);

-- Таблица категорий продукции
CREATE TABLE IF NOT EXISTS product_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Таблица продукции
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category_id INTEGER REFERENCES product_categories(id),
    cover_photo_path VARCHAR(500),
    short_description TEXT,
    is_available BOOLEAN DEFAULT TRUE,
    measurement_unit VARCHAR(20) CHECK (measurement_unit IN ('weight', 'pieces', 'boxes')),
    quantity NUMERIC(10,2) DEFAULT 0,
    price NUMERIC(10,2) NOT NULL,
    prepayment_conditions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица статусов заказов
CREATE TABLE IF NOT EXISTS order_statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT
);

-- Таблица заказов
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    client_name VARCHAR(200) NOT NULL,
    client_phone VARCHAR(20) NOT NULL,
    delivery_address TEXT,
    product_id INTEGER REFERENCES products(id),
    weight_grams INTEGER,
    quantity INTEGER NOT NULL,
    delivery_type VARCHAR(20) CHECK (delivery_type IN ('courier', 'pickup')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ready_at TIMESTAMP,
    comments TEXT,
    total_cost NUMERIC(10,2) NOT NULL,
    status_id INTEGER REFERENCES order_statuses(id),
    status_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_reason TEXT,
    executor_id INTEGER REFERENCES users(id),
    payment_type VARCHAR(50) CHECK (payment_type IN (
        'prepayment_50', 
        'prepayment_100', 
        'payment_on_delivery_transfer',
        'payment_on_delivery_cash'
    )),
    payment_status VARCHAR(50) CHECK (payment_status IN (
        'awaiting_prepayment',
        'prepayment_received', 
        'awaiting_payment',
        'not_paid',
        'paid'
    )),
    completed_photo_path VARCHAR(500)
);

-- Таблица отзывов
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    client_name_visible BOOLEAN DEFAULT TRUE,
    order_id INTEGER REFERENCES orders(id),
    executor_id INTEGER REFERENCES users(id),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    photo_paths TEXT[] DEFAULT '{}'
);

-- Таблица категорий рецептов
CREATE TABLE IF NOT EXISTS recipe_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Таблица рецептов
CREATE TABLE IF NOT EXISTS recipes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category_id INTEGER REFERENCES recipe_categories(id),
    short_description TEXT,
    portions INTEGER,
    instructions TEXT,
    cooking_time INTERVAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    author_id INTEGER REFERENCES users(id),
    photo_paths TEXT[] DEFAULT '{}'
);

-- Таблица ингредиентов рецептов
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes(id) ON DELETE CASCADE,
    dish_part VARCHAR(100),
    ingredient_name VARCHAR(200) NOT NULL,
    measurement_unit VARCHAR(50) CHECK (measurement_unit IN (
        'grams', 'pieces', 'liters', 'milliliters', 
        'teaspoons', 'tablespoons', 'cups', 'pinch'
    )),
    quantity NUMERIC(10,2) NOT NULL
);

-- Вставка начальных данных
INSERT INTO order_statuses (name, description) VALUES
('created', 'Заказ оформлен клиентом, но ещё не обработан'),
('confirmed', 'Заказ проверен и подтверждён'),
('in_progress', 'Кондитер приступил к приготовлению'),
('awaiting_decoration', 'Основа готова, ждёт финальной отделки'),
('ready_for_pickup', 'Готов к выдаче/упакован'),
('in_delivery', 'Передан курьеру/в доставке'),
('completed', 'Клиент получил заказ'),
('cancelled', 'Заказ отменён'),
('paused', 'Заказ временно приостановлен'),
('problematic', 'Возникла проблема, требует внимания')
ON CONFLICT DO NOTHING;

INSERT INTO product_categories (name, description) VALUES
('Торты', 'Различные виды тортов'),
('Пирожные', 'Индивидуальные десерты'),
('Печенье', 'Различное печенье и кексы'),
('Пироги', 'Фруктовые и ягодные пироги')
ON CONFLICT DO NOTHING;

INSERT INTO recipe_categories (name, description) VALUES
('Торты', 'Рецепты тортов'),
('Пирожные', 'Рецепты пирожных'),
('Печенье', 'Рецепты печенья'),
('Основы', 'Базовые рецепты')
ON CONFLICT DO NOTHING;

-- Создание индексов для улучшения производительности
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_orders_status_id ON orders(status_id);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_recipes_category_id ON recipes(category_id);
CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_recipe_id ON recipe_ingredients(recipe_id);

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE TRIGGER update_products_updated_at 
    BEFORE UPDATE ON products 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();