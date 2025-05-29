# Stock Market API

Полный бэкенд для симуляции фондового рынка на Python + FastAPI + PostgreSQL + Docker.

## Структура
- `.env.example` — пример переменных окружения.
- `requirements.txt` — зависимости.
- `Dockerfile`, `docker-compose.yml` — контейнеризация и обратный прокси для HTTPS.
- `app/` — исходный код сервера.
- `alembic/` — миграции базы данных.
- `openapi.json` — спецификация OpenAPI (скачайте по вашей ссылке и поместите в корень проекта).

## Запуск
1. Скопируйте `.env.example` в `.env` и настройте.
2. Поместите скачанный `openapi.json` в корень проекта.
3. Сборка и запуск:
   ```bash
   docker-compose up --build
   ```
4. Сервер доступен по `https://localhost/`, документация — `/docs` и `/openapi.json`.
