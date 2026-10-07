# Запуск и troubleshooting

## Запуск локально

```powershell
cd D:\PythonProjectXXX\TaskFlow
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

## Проверка сервиса

Открой `http://127.0.0.1:8001/api/health`. Ответ должен содержать:

```json
{
  "status": "ok",
  "service": "TaskFlow"
}
```

## Где база

По умолчанию SQLite-файл находится в `data/taskflow.db`. Он создается при первом
запуске и исключен из Git.

## Порт занят

Запусти приложение на другом порту:

```powershell
python -m uvicorn app.main:app --reload --port 8010
```

В этом случае web-панель будет на `http://127.0.0.1:8010`.

## Ошибка активации окружения

Можно не активировать `.venv`, а запускать интерпретатор напрямую:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

## Секреты

Не коммить файл `.env`, реальные пароли и production-secret. Для GitHub в
репозитории оставляй только `.env.example` с демонстрационными значениями.
