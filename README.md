# BezBazara

Сайт вопросов и ответов на Django (VK Education, курс по вебу).
Домашнее задание 2: views с данными-заглушками, маршрутизация, шаблоны и пагинация. Базы данных и логики пока нет.

## Запуск локально

Нужен Python 3.12 или новее.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py runserver
```

Сайт будет доступен на http://localhost:8000/. Остановить сервер: `Ctrl+C`.

## Запуск через Docker Compose

Нужен установленный Docker.

```bash
cp .env.example .env
docker compose up --build
```

Сайт будет доступен на http://localhost:8000/. Остановить: `Ctrl+C`, затем `docker compose down`.

Код проекта подключен в контейнер как volume, поэтому изменения файлов сразу видны в контейнере. Загруженные файлы (`media/`) хранятся в отдельном volume и не пропадают при пересборке.

## Страницы

| URL | Имя маршрута | Описание |
|-----|--------------|----------|
| `/` | `index` | Новые вопросы |
| `/hot/` | `hot` | Лучшие вопросы |
| `/tag/<имя>/` | `tag` | Вопросы по тегу |
| `/question/<id>/` | `question` | Вопрос и список ответов |
| `/ask/` | `ask` | Создание вопроса |
| `/login/` | `login` | Вход |
| `/signup/` | `signup` | Регистрация |
| `/profile/` | `profile` | Редактирование профиля |

Списки разбиты на страницы параметром `?page=N`. Неверное значение заменяется на первую или последнюю страницу.

## Структура

```
application/            настройки проекта и корневой urls.py
core/                   пользовательские страницы (вход, регистрация, профиль), базовый шаблон
  templates/core/       base.html и подшаблоны (includes/)
  static/core/          css, шрифты, изображения
  utils.py              функция paginate()
questions/              вопросы (списки, страница вопроса, создание)
  templates/questions/  шаблоны страниц вопросов
manage.py
requirements.txt
Dockerfile, docker-compose.yml
.env.example            пример переменных окружения
```
