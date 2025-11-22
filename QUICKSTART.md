# Quick Start Guide для StudyFlow

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Запуск приложения

```bash
uvicorn app.main:app --reload
```

Приложение запустится на `http://localhost:8000`

### 3. Доступ к документации API

- Swagger UI: http://localhost:8000/docs

Обратите внимание на основные группы эндпоинтов:

- Authentication: `/api/v1/auth/*`
- Tasks: `/api/v1/tasks/*`
- TaskLists: `/api/v1/tasklists/*`
- Analytics: `/api/v1/analytics/*`

## Тестирование API

### Создание пользователя

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123",
    "name": "Test",
    "surname": "User"
  }'
```

### Получение JWT токена

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

Скопируйте `access_token` из ответа.

### Создание задачи

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Изучить FastAPI",
    "description": "Изучить основы создания REST API",
    "priority": 2,
    "category_id": 1
  }'
```

### Получение списка задач

```bash
curl -X GET "http://localhost:8000/api/v1/tasks/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Основные endpoint'ы

### Аутентификация

- `POST /api/v1/auth/register` - Регистрация пользователя
- `POST /api/v1/auth/login` - Вход, получение JWT токена
- `GET /api/v1/auth/me` - Информация о текущем пользователе

### Задачи

- `GET /api/v1/tasks/` - Список задач
- `POST /api/v1/tasks/` - Создать задачу
- `GET /api/v1/tasks/{id}` - Получить задачу
- `PUT /api/v1/tasks/{id}` - Обновить задачу
- `DELETE /api/v1/tasks/{id}` - Удалить задачу
- `POST /api/v1/tasks/{id}/complete` - Отметить как выполненную

### Подзадачи

Чтобы создать подзадачу, укажите parent_id в теле POST /api/v1/tasks/. Parent must belong to the same user.

Пример создания подзадачи:

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Subtask example",
    "parent_id": 1
  }'
```

## Аналитика продуктивности

### Получение метрик продуктивности

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/metrics?days_back=60" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Возвращает детальные метрики продуктивности:
- Продуктивность по дням недели
- Топ-дни недели по продуктивности
- Скользящие средние (7, 14, 28 дней)
- Индекс риска выгорания
- Данные по стрикам и выполненным задачам

### Получение полного дашборда аналитики

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/dashboard?days_back=60" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Возвращает полный дашборд с метриками, рекомендациями и предупреждениями о риске выгорания.

### Получение информации о риске выгорания

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/risk?days_back=60" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Возвращает информацию о категории риска (низкий/средний/высокий) и рекомендации по снижению нагрузки.

### Получение рекомендаций по продуктивности

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/recommendations?days_back=60" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Возвращает персонализированные рекомендации на основе анализа ваших самых продуктивных дней недели.

### Эндпоинты аналитики

- `GET /api/v1/analytics/metrics` - Получить метрики продуктивности
- `GET /api/v1/analytics/dashboard` - Получить полный дашборд аналитики с рекомендациями и предупреждениями
- `GET /api/v1/analytics/risk` - Получить информацию о риске выгорания
- `GET /api/v1/analytics/recommendations` - Получить рекомендации по продуктивности

**Параметры:**
- `days_back` (query, опционально) - Количество дней для анализа (по умолчанию: 60)

**Примечание:** Все эндпоинты аналитики требуют авторизации и анализируют данные только текущего пользователя.
