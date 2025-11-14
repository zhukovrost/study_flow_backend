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
