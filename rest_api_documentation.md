## 📘 Общая REST API документация

---

### /articles

```python
class ArticleRead(BaseModel):
    id: int
    category_id: int
    title: str
    content: str
    content_type: str
    created_at: datetime

class ArticleCreate(BaseModel):
    category_id: int
    title: str
    content: str
    content_type: str  # 'markdown' or 'html'

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    content_type: Optional[str] = None

class ArticleImport(BaseModel):
    category_id: int
    title: str
    content: str
    content_type: str
```

GET /articles/
Описание: Получить список всех статей
Ответ: 200 OK — список ArticleRead

GET /articles/{article\_id}
Описание: Получить статью по ID
Параметры: article\_id
Ответ: 200 OK — ArticleRead; 404 — не найдено

GET /articles/category/{category\_id}
Описание: Получить статьи по категории
Параметры: category\_id
Ответ: 200 OK — список ArticleRead

POST /articles/
Описание: Создать статью (только для admin)
Тело: category\_id, title, content, content\_type
Ответ: 201 Created — ArticleRead; 403 — доступ запрещён

PUT /articles/{article\_id}
Описание: Обновить статью (только для admin)
Параметры: article\_id
Тело: title?, content?, content\_type?
Ответ: 200 OK — ArticleRead; 404; 403

DELETE /articles/{article\_id}
Описание: Удалить статью (только для admin)
Параметры: article\_id
Ответ: 204; 404; 403

---

### /assignments

```python
class AssignmentRead(BaseModel):
    id: int
    assigned_by: int
    category_id: int
    user_id: Optional[int]
    group_id: Optional[int]
    assigned_at: datetime

class AssignmentCreateUser(BaseModel):
    assigned_by: int
    category_id: int
    user_id: int
    assigned_at: Optional[datetime] = None

class AssignmentCreateGroup(BaseModel):
    assigned_by: int
    category_id: int
    group_id: int
    assigned_at: Optional[datetime] = None

class AssignmentUpdate(BaseModel):
    user_id: Optional[int] = None
    group_id: Optional[int] = None

class AssignmentImport(BaseModel):
    assigned_by: int
    category_id: int
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    assigned_at: Optional[datetime] = None
```

GET /assignments/
Описание: Получить список назначений; фильтрация по user\_id, group\_id, category\_id
Ответ: 200 OK — список AssignmentRead

GET /assignments/{assignment\_id}
Описание: Получить назначение по ID
Ответ: 200 OK — AssignmentRead; 404

POST /assignments/user
Описание: Назначить категорию пользователю
Ответ: 201 — AssignmentRead

POST /assignments/group
Описание: Назначить категорию группе
Ответ: 201 — AssignmentRead

PUT /assignments/{assignment\_id}
Описание: Обновить назначение
Ответ: 200 — AssignmentRead; 404

DELETE /assignments/{assignment\_id}
Описание: Удалить назначение
Ответ: 204; 404

---

### /auth

```python
class UserRegister(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserRead(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    role: str
    created_at: datetime
```

POST /auth/register
Описание: Регистрация нового пользователя
Тело: username, password
Ответ: 201 — access\_token

POST /auth/login
Описание: Авторизация
Тело: username, password
Ответ: 200 — access\_token; 401

GET /auth/me
Описание: Получить данные текущего пользователя
Ответ: 200 — UserRead; 401

---

### /categories
```python
class CategoryRead(BaseModel):
    id: int
    title: str
    parent_id: Optional[int]

class CategoryCreate(BaseModel):
    title: str
    parent_id: Optional[int] = None

class CategoryUpdate(BaseModel):
    title: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryImport(BaseModel):
    title: str
    parent_id: Optional[int] = None

# В ответе на /categories/tree возвращаем вложенные узлы
class CategoryTreeNode(BaseModel):
    id: int
    title: str
    children: List["CategoryTreeNode"] = []
```

GET /categories/
Описание: Плоский список категорий
Ответ: 200 — список CategoryRead

GET /categories/tree
Описание: Дерево категорий
Ответ: 200 — список CategoryTreeNode

GET /categories/{category\_id}
Описание: Категория по ID
Ответ: 200 — CategoryRead; 404

POST /categories/
Описание: Создать категорию (admin)
Ответ: 201 — CategoryRead; 403

PUT /categories/{category\_id}
Описание: Обновить категорию (admin)
Ответ: 200 — CategoryRead; 404; 403

DELETE /categories/{category\_id}
Описание: Удалить категорию (admin)
Ответ: 204; 404; 403

---

### /media

```python
class MediaRead(BaseModel):
    id: int
    article_id: int
    media_type: str
    url: str
    sort_order: int

class MediaCreate(BaseModel):
    article_id: int
    media_type: str    # 'svg', 'png' или 'webm'
    url: str
    sort_order: Optional[int] = 0

class MediaUpdate(BaseModel):
    media_type: Optional[str] = None
    url: Optional[str] = None
    sort_order: Optional[int] = None

class MediaImport(BaseModel):
    article_id: int
    media_type: str
    url: str
    sort_order: Optional[int] = 0
```

GET /media/
Описание: Список медиа; фильтр по article\_id
Ответ: 200 — список MediaRead

GET /media/{media\_id}
Описание: Медиа по ID
Ответ: 200 — MediaRead; 404

GET /media/article/{article\_id}
Описание: Медиа по article\_id
Ответ: 200 — список MediaRead; 404

POST /media/
Описание: Создать медиа (admin)
Ответ: 201 — MediaRead; 403

PUT /media/{media\_id}
Описание: Обновить медиа (admin)
Ответ: 200 — MediaRead; 404; 403

DELETE /media/{media\_id}
Описание: Удалить медиа (admin)
Ответ: 204; 404; 403

---

### /options

```python
class OptionRead(BaseModel):
    id: int
    question_id: int
    text: str
    is_correct: bool

class OptionCreate(BaseModel):
    question_id: int
    text: str
    is_correct: Optional[bool] = False

class OptionUpdate(BaseModel):
    text: Optional[str] = None
    is_correct: Optional[bool] = None

class OptionImport(BaseModel):
    question_id: int
    text: str
    is_correct: Optional[bool] = False
```

GET /options/
Описание: Список вариантов; можно фильтровать по question\_id
Ответ: 200 — список OptionRead

GET /options/{option\_id}
Описание: Вариант по ID
Ответ: 200 — OptionRead; 404

GET /options/question/{question\_id}
Описание: Варианты конкретного вопроса
Ответ: 200 — список OptionRead

POST /options/
Описание: Создать вариант
Ответ: 201 — OptionRead

PUT /options/{option\_id}
Описание: Обновить вариант
Ответ: 200 — OptionRead; 404

DELETE /options/{option\_id}
Описание: Удалить вариант
Ответ: 204; 404

---

### /progress

```python
class ProgressRead(BaseModel):
    id: int
    user_id: int
    category_id: int
    status: str
    updated_at: datetime

class ProgressCreate(BaseModel):
    user_id: int
    category_id: int
    status: Optional[str] = "not_started"

class ProgressUpdate(BaseModel):
    user_id: int
    category_id: int
    status: str

class ProgressImport(BaseModel):
    user_id: int
    category_id: int
    status: str
    updated_at: Optional[datetime] = None
```

GET /progress/
Описание: возвращает список записей прогресса. По желанию можно добавить к URL параметры ?user_id={число} и/или ?category_id={число}.
Тело запроса не требуется.

GET /progress/{progress_id}
Описание: возвращает одну запись прогресса по её идентификатору.
Параметр пути: progress_id (целое число).
Ответ: 200 — ProgressRead; 404

POST /progress/
Описание: создаёт новую запись прогресса.
Тело запроса (JSON) должно содержать:
• user_id (целое число, обязательное) – идентификатор пользователя;
• category_id (целое число, обязательное) – идентификатор категории;
• status (строка, необязательное, по умолчанию "not_started") – начальный статус.
Ответ: 201 — ProgressRead

PUT /progress/
Описание: обновляет существующую запись прогресса, найденную по сочетанию user_id и category_id, присваивая новый статус.
Тело запроса (JSON) должно содержать:
• user_id (целое число) – идентификатор пользователя;
• category_id (целое число) – идентификатор категории;
• status (строка) – новый статус (например, in_progress или completed).
Ответ: 200 — ProgressRead; 404

DELETE /progress/{progress_id}
Описание: удаляет запись прогресса по её идентификатору.
Параметр пути: progress_id (целое число).
Тело запроса не требуется.
Ответ: 204; 404

---

### /questions

```python
class QuestionRead(BaseModel):
    id: int
    test_id: int
    text: str
    weight: int

class QuestionCreate(BaseModel):
    test_id: int
    text: str
    weight: Optional[int] = 1

class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    weight: Optional[int] = None

class QuestionImport(BaseModel):
    test_id: int
    text: str
    weight: Optional[int] = 1
```

GET /questions/
Описание: Все вопросы
Ответ: 200 — список QuestionRead

GET /questions/{question\_id}
Описание: Вопрос по ID
Ответ: 200 — QuestionRead; 404

GET /questions/test/{test\_id}
Описание: Вопросы теста
Ответ: 200 — список QuestionRead

POST /questions/
Описание: Создать вопрос
Ответ: 201 — QuestionRead

PUT /questions/{question\_id}
Описание: Обновить вопрос
Ответ: 200 — QuestionRead; 404

DELETE /questions/{question\_id}
Описание: Удалить вопрос
Ответ: 204; 404

---

### /test-results

```python
class TestAnswerRead(BaseModel):
    id: int
    test_result_id: int
    question_id: int
    selected_option_id: int

    class Config:
        orm_mode = True

class TestResultRead(BaseModel):
    id: int
    user_id: int
    test_id: int
    score: float
    max_score: float
    passed: bool
    taken_at: datetime

    class Config:
        orm_mode = True

class AnswerIn(BaseModel):
    question_id: int
    selected_option_id: int

class TestResultCreate(BaseModel):
    user_id: int
    test_id: int
    score: float
    max_score: float
    passed: bool
    answers: List[AnswerIn]
```

GET /test-results/
Описание: возвращает список результатов тестов. При желании можно добавить к URL параметры ?user_id={число} или ?test_id={число}. Если указан user_id, возвращаются только результаты этого пользователя; иначе, если указан test_id, — только результаты этого теста; если оба не указаны, возвращаются все результаты.
Тело запроса не требуется.

GET /test-results/{result_id}
Описание: возвращает один результат теста по его идентификатору result_id.
Параметр пути: result_id (целое число).
Тело запроса не требуется.

GET /test-results/{result_id}/answers
Описание: возвращает список ответов, связанных с указанным результатом теста.
Параметр пути: result_id (целое число).
Тело запроса не требуется.

POST /test-results/
Описание: создаёт новый результат теста и все его ответы.
Тело запроса (JSON) должно содержать:
• user_id (целое число) – идентификатор пользователя;
• test_id (целое число) – идентификатор теста;
• score (число с плавающей точкой) – баллы, набранные при прохождении;
• max_score (число с плавающей точкой) – максимально возможные баллы;
• passed (логическое) – true, если тест считается пройденным;
• answers – массив объектов, каждый из которых содержит question_id (целое число) и selected_option_id (целое число).

DELETE /test-results/{result\_id}
Описание: Удалить результат
Ответ: 204; 404

---

### /tests

```python
# Pydantic-модели для /tests

from typing import List, Optional
from pydantic import BaseModel

# ────────────────────────────────────────────────────────────────────────────────
# Существующие модели
# ────────────────────────────────────────────────────────────────────────────────

class TestRead(BaseModel):
    id: int
    category_id: int
    title: str
    max_attempts: int

    class Config:
        orm_mode = True

class TestCreate(BaseModel):
    category_id: int
    title: str
    max_attempts: Optional[int] = 3

class TestUpdate(BaseModel):
    title: Optional[str] = None
    max_attempts: Optional[int] = None

class TestImport(BaseModel):
    category_id: int
    title: str
    max_attempts: Optional[int] = 3

# ────────────────────────────────────────────────────────────────────────────────
# Новые модели для "полного" теста (создание и чтение)
# ────────────────────────────────────────────────────────────────────────────────

class OptionNestedCreate(BaseModel):
    text: str
    is_correct: Optional[bool] = False

class QuestionNestedCreate(BaseModel):
    text: str
    weight: Optional[int] = 1
    options: List[OptionNestedCreate]

class TestFullCreate(BaseModel):
    category_id: int
    title: str
    max_attempts: Optional[int] = 3
    questions: List[QuestionNestedCreate]

class OptionRead(BaseModel):
    id: int
    question_id: int
    text: str
    is_correct: bool

    class Config:
        orm_mode = True

class QuestionReadWithOptions(BaseModel):
    id: int
    test_id: int
    text: str
    weight: int
    options: List[OptionRead]

    class Config:
        orm_mode = True

class TestReadWithQuestions(BaseModel):
    id: int
    category_id: int
    title: str
    max_attempts: int
    questions: List[QuestionReadWithOptions]

    class Config:
        orm_mode = True
```

GET    /tests/
Описание: Все тесты
Ответ:
  200 — List[TestRead]

GET    /tests/{test_id}
Описание: Тест по ID
Ответ:
  200 — TestRead
  404 — { "detail": "Test not found" }

GET    /tests/category/{category_id}
Описание: Тесты по категории
Ответ:
  200 — List[TestRead]

POST   /tests/
Описание: Создать тест
Тело запроса: TestCreate
Ответ:
  201 — TestRead

PUT    /tests/{test_id}
Описание: Обновить тест
Тело запроса: TestUpdate
Ответ:
  200 — TestRead
  404 — { "detail": "Test not found" }

DELETE /tests/{test_id}
Описание: Удалить тест
Ответ:
  204 — (пусто)
  404 — { "detail": "Test not found" }

POST   /tests/import
Описание: Массовый импорт тестов
Тело запроса: List[TestImport]  # список импортируемых тестов
Ответ:
  200 — List[TestRead]

GET    /tests/export
Описание: Массовый экспорт тестов
Ответ:
  200 — List[TestRead]

POST   /tests/full
Описание: Создать тест вместе со всеми вопросами и вариантами ответов одним запросом.
Тело запроса: TestFullCreate
  {
    "category_id": int,
    "title": str,
    "max_attempts": int,
    "questions": [
      {
        "text": str,
        "weight": int,
        "options": [
          { "text": str, "is_correct": bool },
          ...
        ]
      },
      ...
    ]
  }
Ответ:
  201 — TestReadWithQuestions
  Пример тела ответа:
  {
    "id": 42,
    "category_id": 5,
    "title": "Название теста",
    "max_attempts": 3,
    "questions": [
      {
        "id": 101,
        "test_id": 42,
        "text": "Вопрос 1?",
        "weight": 2,
        "options": [
          { "id": 1001, "question_id": 101, "text": "Вариант A", "is_correct": false },
          { "id": 1002, "question_id": 101, "text": "Вариант B", "is_correct": true },
          ...
        ]
      },
      ...
    ]
  }

GET    /tests/full/{test_id}
Описание: Получить полный тест вместе со всеми вопросами и вариантами ответов.
Ответ:
  200 — TestReadWithQuestions
  Пример тела ответа:
  {
    "id": 42,
    "category_id": 5,
    "title": "Название теста",
    "max_attempts": 3,
    "questions": [
      {
        "id": 101,
        "test_id": 42,
        "text": "Вопрос 1?",
        "weight": 2,
        "options": [
          { "id": 1001, "question_id": 101, "text": "Вариант A", "is_correct": false },
          { "id": 1002, "question_id": 101, "text": "Вариант B", "is_correct": true },
          ...
        ]
      },
      ...
    ]
  }
  404 — { "detail": "Test с id={test_id} не найден" }


---

### /users

```python
class UserRead(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    role_id: int
    created_at: datetime

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role_id: Optional[int] = None

class UserExport(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    role_id: int
    created_at: str  # ISO datetime

class UserImport(BaseModel):
    username: str
    password_hash: Optional[str] = ""
    role_id: int
    full_name: Optional[str] = None
```

GET /users/
Описание: Список пользователей (только admin); фильтрация по роли
Ответ: 200 — список UserRead; 403

GET /users/{user\_id}
Описание: Пользователь по ID
Ответ: 200 — UserRead; 404

PUT /users/{user\_id}
Описание: Обновить пользователя
Ответ: 200 — UserRead; 404

DELETE /users/{user\_id}
Описание: Удалить пользователя (admin)
Ответ: 204; 404; 403

POST /users/export
Описание: Экспорт пользователей (admin)
Ответ: 200 — список UserExport; 403

POST /users/import
Описание: Импорт пользователей (admin)
Ответ: 200 — список UserRead; 403
