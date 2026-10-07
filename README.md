# TaskFlow

TaskFlow - учебный portfolio-проект CRM на Python. Сервис помогает небольшой
команде хранить клиентов, вести заказы и отслеживать их статусы в одном рабочем
пространстве.

Проект демонстрирует навыки junior Python backend-разработчика:
FastAPI, REST API, JWT-авторизацию, роли пользователей, Pydantic, SQLAlchemy,
SQLite/PostgreSQL-совместимую структуру, web-интерфейс, Docker и pytest.

## Возможности

- регистрация и вход пользователя;
- JWT Bearer-авторизация;
- роли `admin` и `manager`;
- первый зарегистрированный пользователь становится администратором;
- создание, изменение и просмотр клиентов;
- создание заказов с суммой, описанием и статусом;
- перевод заказа по этапам `new -> in_progress -> done`;
- dashboard с числом клиентов, заказов и завершенной выручкой;
- REST API и Swagger/OpenAPI;
- адаптивная web-панель;
- автоматические тесты;
- запуск через PyCharm, Uvicorn или Docker Compose.

## Быстрый запуск в PyCharm

Открой в PyCharm папку:

```text
D:\PythonProjectXXX\TaskFlow
```

Выбери интерпретатор:

```text
D:\PythonProjectXXX\TaskFlow\.venv\Scripts\python.exe
```

Если окружение еще не создано, выполни в терминале PyCharm:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Затем открой файл `run.py` и нажми зеленую кнопку **Run**. Приложение будет
доступно на:

- web-панель: `http://127.0.0.1:8001`;
- Swagger: `http://127.0.0.1:8001/docs`;
- health endpoint: `http://127.0.0.1:8001/api/health`.

Альтернативный запуск:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

## Первый сценарий

1. Открой `http://127.0.0.1:8001`.
2. Перейди на вкладку `Регистрация`.
3. Создай первый аккаунт. Он получит роль администратора.
4. Добавь клиента.
5. Создай заказ для клиента.
6. Нажимай кнопку статуса, чтобы перевести заказ из нового в работу и затем в
   завершенные.
7. Посмотри, как dashboard пересчитывает активные заказы и выручку.

## API-примеры

Зарегистрировать пользователя:

```powershell
$body = @{
    email = "admin@example.com"
    full_name = "Admin User"
    password = "StrongPass123"
} | ConvertTo-Json

$session = Invoke-RestMethod `
    -Uri http://127.0.0.1:8001/api/auth/register `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

Сохранить токен в переменную:

```powershell
$headers = @{ Authorization = "Bearer $($session.access_token)" }
```

Добавить клиента:

```powershell
$clientBody = @{
    name = "Иван Петров"
    company = "ООО Север"
    email = "ivan@example.com"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://127.0.0.1:8001/api/clients `
    -Method Post `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $clientBody
```

Получить заказы:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/orders -Headers $headers
```

Полное описание endpoints находится в [docs/api.md](docs/api.md) и Swagger.

## Тесты

```powershell
python -m pytest
```

Тесты проверяют регистрацию, логин, JWT-доступ, роли, валидацию, создание
клиента, создание заказа, обновление статуса, dashboard и дубликаты email.

## Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Приложение откроется на `http://127.0.0.1:8001`.

Остановить контейнер:

```powershell
docker compose down
```

## Структура проекта

```text
TaskFlow/
|-- app/
|   |-- api/routes.py       # endpoints регистрации, клиентов и заказов
|   |-- config.py           # настройки приложения
|   |-- database.py         # SQLAlchemy engine и таблицы
|   |-- models.py           # User, Client, Order
|   |-- schemas.py          # Pydantic-модели запросов и ответов
|   |-- security.py         # пароли, JWT и роли
|   `-- main.py             # создание FastAPI-приложения
|-- web/                    # интерфейс CRM
|-- tests/                  # API-тесты
|-- docs/                   # учебная документация
|-- data/                   # локальная база, не коммитится
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
`-- run.py
```

## Как рассказывать работодателю

> TaskFlow - CRM-сервис для клиентов и заказов. Я реализовал REST API на
> FastAPI, JWT-авторизацию, роли администратора и менеджера, валидацию через
> Pydantic, работу с SQLAlchemy, dashboard, web-панель, Docker и pytest-тесты.

Основной пользовательский сценарий: менеджер входит в систему, добавляет
клиента, создает заказ, меняет его статус, а dashboard показывает текущую
загрузку и завершенную выручку.

## Учебная версия и дальнейшее развитие

Сейчас для простого запуска используется SQLite. Архитектура сохраняет путь к
PostgreSQL через `DATABASE_URL`. Для production-версии стоит добавить Alembic,
PostgreSQL, восстановление пароля, refresh-токены, аудит изменений, пагинацию,
уведомления и CI в GitHub Actions.

Подробные материалы:

- [Архитектура](docs/architecture.md)
- [Описание API](docs/api.md)
- [Учебный маршрут](docs/learning-guide.md)
- [Запуск и troubleshooting](docs/runbook.md)

