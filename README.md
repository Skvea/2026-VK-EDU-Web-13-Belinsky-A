# BezBazara

Сайт вопросов и ответов на Django (VK Education, курс по вебу).
Домашнее задание 4: авторизация и регистрация пользователей, формы django.forms и ModelForm, валидация данных и паролей, загрузка аватарок в MEDIA_ROOT, AJAX лайки/дизлайки и выбор правильного ответа.

## Запуск через Docker Compose

Нужен установленный Docker.

```bash
docker compose up --build
```

Сайт доступен на http://localhost:8000/, панель администратора — на http://localhost:8000/admin/. Остановить: `Ctrl+C`, затем `docker compose down`.

Данные базы сохраняются в volume `pg_data`. Загруженные аватарки хранятся в volume `media_data`.

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

Генератор тестовых данных (Faker) настроен на английский язык (`en_US`), чтобы тексты вопросов, ответов и теги соответствовали англоязычному интерфейсу сайта.

## Страницы и формы

| URL | Имя маршрута | Описание |
|-----|--------------|----------|
| `/` | `index` | Список новых вопросов с пагинацией |
| `/hot/` | `hot` | Список лучших вопросов |
| `/tag/<tag_name>/` | `tag` | Список вопросов по тегу (404, если тег не найден) |
| `/question/<question_id>/` | `question` | Вопрос, список ответов и форма добавления ответа (`ModelForm`) |
| `/ask/` | `ask` | Форма создания вопроса (`ModelForm`), доступна авторизованным |
| `/login/` | `login` | Форма входа с поддержкой и валидацией `?next=` |
| `/logout/` | `logout` | Выход из аккаунта с возвратом на текущую страницу |
| `/signup/` | `signup` | Форма регистрации с валидацией паролей и созданием Profile |
| `/profile/` | `profile` | Редактирование профиля и загрузка аватарок (`login_required`) |
| `/admin/` | `admin` | Панель администратора (локализована на русский язык) |

## AJAX эндпоинты

- `POST /api/vote/question/` — лайк / дизлайк вопроса (возврат нового рейтинга в JSON, повторный клик снимает голос).
- `POST /api/vote/answer/` — лайк / дизлайк ответа.
- `POST /api/answer/correct/` — выбор правильного ответа (доступен только автору вопроса, для остальных возвращается 403 Forbidden).

## Запуск тестов

```bash
python manage.py test
```

## Структура

```
application/            настройки проекта, wsgi/asgi и корневой urls.py
core/                   пользовательский функционал (профиль, вход, выход, регистрация), базовый шаблон
  forms.py              LoginForm, SignupForm, ProfileEditForm
  templates/core/       base.html и подшаблоны (includes/)
  static/core/          стили, скрипты (app.js), картинки
  utils.py              функция пагинации paginate()
questions/              вопросы, ответы, теги, оценки
  forms.py              QuestionForm, AnswerForm, VoteForm
  templates/questions/  шаблоны страниц вопросов и ответов
  management/commands/  команда fill_db
docker-compose.yml      сервисы web и db (PostgreSQL 16)
Dockerfile              сборка образа python:3.12-slim
requirements.txt        зависимости проекта
.env.example            пример переменных окружения
```
