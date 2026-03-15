# TenderHack Backend

## Быстрый старт

### 1. Настройка переменных окружения

Скопируй `.env.example` в `.env` и при необходимости измени значения:

```bash
cp .env.example .env
```

### 2. Запуск основного приложения

```bash
make run
```

Поднимает: PostgreSQL + Ollama (с моделью `qwen3-embedding:0.6b`) + FastAPI приложение.

Документация после запуска:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. Дополнительные сервисы

**Qdrant** (векторная БД):
```bash
docker compose -f docker-compose.qd.yml up -d
```
Доступен на: http://localhost:6333

**Ollama с кастомными моделями:**
```bash
LLM_MODEL=llama3.2:3b EMBEDDING_MODEL=qwen3-embedding:0.6b \
  docker compose -f docker-compose.ml.yml up -d
```

### 4. Тесты и линтинг

```bash
make test   # запуск тестов
make lint   # проверка кода (ruff)
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `OLLAMA_MODEL` | `qwen3-embedding:0.6b` | Модель для эмбеддингов |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | URL Ollama (внутри Docker) |
| `DATABASE_URL` | `postgresql+psycopg://...` | Строка подключения к БД |
| `LLM_MODEL` | — | LLM модель для docker-compose.ml.yml |
| `EMBEDDING_MODEL` | — | Embedding модель для docker-compose.ml.yml |
