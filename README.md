# MyConfBot - Бот для мастера-кондитера

Telegram бот для приема заказов и консультаций по кондитерским изделиям. С админкой

Это мой учебный бот. Создавался с помощью лекций Skillbox и ИИ.
Мои требования:

1. Использовать uv
2. Создать структуру проекта с учетом современных тенденций
3. Использовать dotenv
4. Библиотека pyTelegramBotAPI, в дальнейшем возможно, миграция на python-telegram-bot, с асинхронностью
5. Использовать логирование
6. Использовать DB (скорее всего начну с SQLite, ради опыта может мигрирую на Postgre)
7. По возможности, простое управление БД через веб-интерфейс (но это другой проект)
8. Практиковать тестирование Pytest
9.

## Установка

1. Клонируйте репозиторий
2. Установите зависимости: `uv sync`
3. Переименуй файл `.env.exemle` в `.env` и добавьте токен бота и другие параметры
4. Запустите: `uv run python -m myconfbot`

## Функциональность

- Прием заказов
- Показ рецептов
- Информация об услугах
- Контактная информация

Структура файлов на 10.09.2025

```text
myconfbot
├─ .python-version
├─ config
├─ pyproject.toml
├─ README.md
├─ src
│  └─ myconfbot
│     ├─ bot.py
│     ├─ config.py
│     ├─ handlers
│     │  ├─ main_handlers.py
│     │  ├─ order_handlers.py
│     │  ├─ recipe_handlers.py
│     │  └─ __init__.py
│     ├─ keyboards
│     ├─ models
│     ├─ utils
│     │  └─ __init__.py
│     ├─ __init__.py
│     └─ __main__.py
├─ tests
└─ uv.lock

```

## 11.09.25

```
myconfbot
├─ config
├─ data
│  └─ confbot.db
├─ pyproject.toml
├─ README.md
├─ src
│  └─ myconfbot
│     ├─ bot.py
│     ├─ config.py
│     ├─ handlers
│     │  ├─ admin_handlers.py
│     │  ├─ main_handlers.py
│     │  ├─ order_handlers.py
│     │  ├─ recipe_handlers.py
│     │  └─ __init__.py
│     ├─ init_db.py
│     ├─ keyboards
│     ├─ models
│     │  └─ __init__.py
│     ├─ states
│     ├─ utils
│     │  ├─ database.py
│     │  └─ __init__.py
│     ├─ __init__.py
│     └─ __main__.py
├─ tests
└─ uv.lock

```

сделано:

- В папке data добавил confbot.db база SQLite
- Инициализация через init_db.py

```shell
uv run python -m src.myconfbot.init_db
```

- Добавил админ панель, команда `/admin` в телеграм-боте. Пока только без взаимодействия с DB

## 11.09.25

- Приветственный текст и контактная информация подгружаются из файлов `data/welcome.md` и `data/contacts.md`. Это Markdown файлы
- Их создать и за дальнейшее редактирование отвечает файл src\myconfbot\utils\content_manager.py
  Для создания файлов, запустить код:

```shell
uv run python -m src.myconfbot.utils.content_manager
```

- Последующее редактирование доступно из админ панели

## 12.09.25

- Работал с главным меню
  - главное меню выполнено в Reply
  - всегда отображается
  - у клиентов пункты:
    '🎂 Сделать заказ',
    '📖 Рецепты',
    '💼 Услуги',
    '📞 Контакты',
    '🐱 Моя информация'
  - у админов добавляются кнопки:
    '📦 Заказы',
    '📊 Статистика',
    '🏪 Управление'
  - можно скрыть, расскрыть кнопкой
- Все остальные кнопки выполнены в Inline
- Отработал редактирование текстов:
  - "welcome.md" - текст приветствия при /start или /help
  - "services.md" - текст описывающий услуги предоставляемые мастером, при нажатии кнопки '💼 Услуги'
  - "contacts.md" - текст с контактной информацией, при нажатии кнопки '📞 Контакты'
- Для редактирования нужно пройти по кнопкам `Управление` > `Контент`
  - выбрать нужный файл `✏️ file.md` - редактирование. `👀 file.md` - предпросмотр содержимого с возможностью скачивания файла
  - !нужно написать подробную инструкцию с описанием работы с MarkdownV2 текстом
- Файлы `welcome.md`, `services.md`, `contacts.md`, при первом запуске создаются автоматически скриптом `src\myconfbot\utils\content_manager.py` в папке `data`. Если нужно вернуть дефолтное содержание файлов (или файла), достаточно удалить их из папки `data` и перезапустить сервер, скрипт автоматически создаст файлы с дефолтными текстами.

```
myconfbot
├─ config
├─ data
│  ├─ confbot.db
│  ├─ contacts.md
│  ├─ services.md
│  └─ welcome.md
├─ pyproject.toml
├─ README.md
├─ src
│  └─ myconfbot
│     ├─ bot.py
│     ├─ config.py
│     ├─ handlers
│     │  ├─ admin_handlers.py
│     │  ├─ main_handlers.py
│     │  ├─ order_handlers.py
│     │  ├─ recipe_handlers.py
│     │  └─ __init__.py
│     ├─ init_db.py
│     ├─ keyboards
│     ├─ models
│     │  └─ __init__.py
│     ├─ states
│     ├─ utils
│     │  ├─ content_manager.py
│     │  ├─ database.py
│     │  ├─ text_converter.py
│     │  └─ __init__.py
│     ├─ __init__.py
│     └─ __main__.py
├─ tests
└─ uv.lock

```

## 13.09.25

- После небольших раздумий (и с небольшими трудностями с сессиями в SQLite в проекте scan_vpn) решил изменить БД. Выбор пал PostgreSQL. Это мой первый практический опыт с этой БД.

## 16.09.25

- переход на PostreSQL произведен на ветке feature/database-migration переключение БД через .env параметр USE_POSTGRES=true
- там же, в .env, другие параметры подключения к Postgres
- изменил работу кнопки "Моя информация", теперь называется "Мой профиль". По нажатию выводится информация:
  - Фотография
  - Имя
  - Username telegram
  - Телефон
  - Адрес
  - Статус (админ или клиент)
- Кнопки:
  - Изменить имя
  - Изменить телефон
  - Изменить адрес
  - Изменить фото
- У админов в меню "Управление" появилась кнопка "Пользователи", по нажатию выходит список пользователей, отсортированный по статусу (сначала админы, затем клиенты).
- По нажатию по строке пользователя выходит информация:
  - Фотография
  - id telegram
  - Статус
  - Имя
  - Телефон
  - name telegram
  - Характеристика
  - Дата регистрации
- Кнопки:
  - Добавить характеристику (можно сделать заметки, уточнения, доп-ую информацию)
  - Заказы (действие пока в разработке)

## 16.09.25

- Сливаю в майн и начинаю перестраивать архитектуру проекта, 
- так как в хендлерах просто - куча-мала

## 16.09.25 22.51

Временная структура файлов

```
myconfbot
├─ config
├─ pyproject.toml
├─ README.md
├─ src
│  └─ myconfbot
│     ├─ bot
│     │  ├─ confectionery_bot.py
│     │  └─ __init__.py
│     ├─ config.py
│     ├─ handlers
│     │  ├─ admin
│     │  │  ├─ admin_base.py
│     │  │  ├─ admin_main.py
│     │  │  ├─ content_management.py
│     │  │  ├─ order_management.py
│     │  │  ├─ product_management.py
│     │  │  ├─ stats_management.py
│     │  │  ├─ user_management.py
│     │  │  └─ __init__.py
│     │  ├─ base_handler.py
│     │  ├─ shared
│     │  │  ├─ states_manager.py
│     │  │  ├─ utils.py
│     │  │  └─ __init__.py
│     │  ├─ user
│     │  │  ├─ auth_handlers.py
│     │  │  ├─ base_user_handler.py
│     │  │  ├─ main_handlers.py
│     │  │  ├─ order_creation.py
│     │  │  ├─ order_handlers.py
│     │  │  ├─ profile_handlers.py
│     │  │  ├─ recipe_handlers.py
│     │  │  └─ __init__.py
│     │  └─ __init__.py
│     ├─ keyboards
│     ├─ models
│     │  ├─ base.py
│     │  ├─ category.py
│     │  ├─ order.py
│     │  ├─ order_status.py
│     │  ├─ product.py
│     │  ├─ recipe.py
│     │  ├─ user.py
│     │  └─ __init__.py
│     ├─ services
│     │  ├─ auth_service.py
│     │  └─ user_service.py
│     ├─ states
│     ├─ utils
│     │  ├─ content_manager.py
│     │  ├─ database.py
│     │  ├─ text_converter.py
│     │  └─ __init__.py
│     ├─ __init__.py
│     └─ __main__.py
├─ tests
└─ uv.lock

```

## 19.09.2025

Большое обновление после перехода на PostgreSQL
- Исправлены ошибки с проверкой прав Админа
- В БД можно добавить категории товаров

- В БД можно добавить товары по категориям
  - Название name 
  - Категория category_id 
  - Фотография для обложки (выбор одной из загруженных) cover_photo_path
  - Краткое описание short_description 
  - Доступен ли к заказу is_available boolen
  - В чем измеряется measurement_unit 
  - Количество quantity 
  - Цена price 
  - prepayment_conditions 
  - Предоплата created_at 

- Можно Админ панели можно просматривать товары и категории

Проблема! Загрузка фотографий продукции пока не реализована

## 23.09.25
- Логирование привел к порядку. Настройки вынес в отдельный файл logging_config.py из config.py. Теперь единое логирование для всех модулей
- ! В дальнейшем нужно настроить очистку логов по времени (RotatingFileHandler + TimedRotatingFileHandler)
- models модели для БД хранились в папке src/myconfbot/models в разных файлах. Создал один src\myconfbot\utils\models.py
- в управлении продукцией добавил модуль - удаление продукта
- начал рефакторинг product_management.py - Менеджер управления продукцией - разрасся до 2300 строк, при этом еще не все методы реализованы. Разбил на части 
  - category_manager.py - управление категориями товаров
  - product_management.py - основной класс
  - product_constants.py - константы, клавиатуры
  - product_creator.py - создание товара
  - product_viewer.py - просмотр товаров
  - product_states.py - менеджер состояний
  - photo_manager.py - менеджер фотографий

## 24.09.25 
- category_manager.py - сделано
- product_viewer.py - сделано