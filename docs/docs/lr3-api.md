## 📡 Примеры запросов

#### 🔐 Регистрация

```bash
curl -X POST "http://127.0.0.1:8000/auth/register" \
-H "Content-Type: application/json" \
-d '{"username": "testuser", "email": "test@example.com", "password": "secret"}'
```

#### 🔑 Авторизация

```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=testuser&password=secret"
```

#### 📂 Получить категории

```bash
curl -X GET "http://127.0.0.1:8000/finance/categories" \
-H "Authorization: Bearer $JWT_TOKEN"
```

#### 🧾 Синхронный парсинг категорий

```bash
curl -X POST http://localhost:8000/finance/categories/parse \
     -H "Content-Type: application/json" \
     -d '{"urls": ["https://assistentus.ru/okved/razdel-a/", "https://assistentus.ru/okved/razdel-b/"]}'
```

#### 🕒 Асинхронный парсинг (через Celery)

```bash
curl -X POST http://localhost:8000/finance/categories/parse_async \
     -H "Content-Type: application/json" \
     -d '{"urls": ["https://assistentus.ru/okved/razdel-c/", "https://assistentus.ru/okved/razdel-d/"]}'
```

#### 🔄 Проверка статуса задачи

```bash
curl -X GET http://localhost:8000/finance/categories/parse_tasks/TASK_ID
```