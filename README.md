# BezBazara

Сайт вопросов и ответов на Django (VK Education, курс по вебу).
Домашнее задание 3: база данных PostgreSQL, модели, кастомные менеджеры, django-admin, скрипт наполнения данными fill_db, django-debug-toolbar.

## Запуск через Docker Compose

Нужен установленный Docker.

```bash
docker compose up --build
```

Сайт доступен на http://localhost:8000/, панель администратора — на http://localhost:8000/admin/. Остановить: `Ctrl+C`, затем `docker compose down`.

Данные базы сохраняются в volume `pg_data`. Загруженные файлы хранятся в volume `media_data`.

Вход в админку: логин `admin`, пароль `admin`. Создать нового суперпользователя:
```bash
docker compose exec web python manage.py createsuperuser
```

## Запуск локально

Нужен Python 3.12+ и запущенный PostgreSQL (например, `docker compose up -d db`).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Сайт доступен на http://localhost:8000/.

## Наполнение данными (fill_db)

Команда наполняет базу тестовыми данными без N+1 запросов:

```bash
python manage.py fill_db [ratio]
```

Через Docker:
```bash
docker compose exec web python manage.py fill_db 100
```

Пропорции:
- Пользователи: `ratio`
- Вопросы: `ratio * 10`
- Ответы: `ratio * 100`
- Теги: `ratio`
- Оценки: `ratio * 200`

Генератор тестовых данных (Faker) настроен на английский язык (`en_US`), чтобы тексты вопросов, ответов и теги выглядели естественно и соответствовали англоязычному интерфейсу сайта.

## Страницы

| URL | Имя маршрута | Описание |
|-----|--------------|----------|
| `/` | `index` | Список новых вопросов с пагинацией |
| `/hot/` | `hot` | Список лучших вопросов |
| `/tag/<tag_name>/` | `tag` | Список вопросов по тегу (404, если тег не найден) |
| `/question/<question_id>/` | `question` | Вопрос и список ответов (404, если не найден) |
| `/ask/` | `ask` | Форма создания вопроса |
| `/login/` | `login` | Форма входа |
| `/logout/` | `logout` | Выход из аккаунта |
| `/signup/` | `signup` | Форма регистрации |
| `/profile/` | `profile` | Редактирование профиля |
| `/admin/` | `admin` | Панель администратора (локализована на русский язык) |

При `DEBUG=True` на страницах сайта подключена панель `django-debug-toolbar`.

## Структура

```
application/            настройки проекта, wsgi/asgi и корневой urls.py
core/                   пользовательский функционал (профиль, вход, выход, регистрация), базовый шаблон
  templates/core/       base.html и подшаблоны (includes/)
  static/core/          стили, шрифты, картинки
  utils.py              функция пагинации paginate()
questions/              вопросы, ответы, теги, оценки
  templates/questions/  шаблоны страниц вопросов и ответов
  management/commands/  команда fill_db
docker-compose.yml      сервисы web и db (PostgreSQL 16)
Dockerfile              сборка образа python:3.12-slim
requirements.txt        зависимости проекта
.env.example            пример переменных окружения
```
