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

11.09.25
```
myconfbot
├─ config
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
