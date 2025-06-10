# /src/api/tests.py

from typing import Generator, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from src.database import db
from src.models import Test as TestModel, Question as QuestionModel, AnswerOption as AnswerOptionModel
from src.models import Test as TestModel
from src.repositories.test_repository import TestRepository
from src.repositories.question_repository import QuestionRepository
from src.repositories.answer_option_repository import AnswerOptionRepository
from src.api.auth import get_current_user

router = APIRouter(prefix="/tests", tags=["tests"])

def get_db() -> Generator[Session, None, None]:
    yield from db.get_session()

# Pydantic-схемы
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

# -----------------------------------------
# 1) Сначала определим модели Pydantic для вложенной валидации
# -----------------------------------------

# 1.1. Модель для варианта ответа при создании (внутри вложенной структуры)
class OptionNestedCreate(BaseModel):
    text: str
    is_correct: Optional[bool] = False

# 1.2. Модель для вопроса при создании (внутри вложенной структуры)
class QuestionNestedCreate(BaseModel):
    text: str
    weight: Optional[int] = 1
    options: List[OptionNestedCreate]

# 1.3. Модель «полного» теста при создании
class TestFullCreate(BaseModel):
    category_id: int
    title: str
    max_attempts: Optional[int] = 3
    questions: List[QuestionNestedCreate]

# -----------------------------------------
# 2) Определим модели Pydantic для «полного» ответа (Test + вложенные Questions + вложенные Options)
# -----------------------------------------

# 2.1. Модель для чтения варианта ответа (копируем из options.py)
class OptionRead(BaseModel):
    id: int
    question_id: int
    text: str
    is_correct: bool

    class Config:
        orm_mode = True

# 2.2. Модель для чтения вопроса вместе со списком вариантов
class QuestionReadWithOptions(BaseModel):
    id: int
    test_id: int
    text: str
    weight: int
    options: List[OptionRead]  # сюда будут вложены варианты

    class Config:
        orm_mode = True

# 2.3. Модель для чтения полного теста вместе со всеми вопросами (и их вариантами)
class TestReadWithQuestions(BaseModel):
    id: int
    category_id: int
    title: str
    max_attempts: int
    questions: List[QuestionReadWithOptions]  # сюда будут вложены вопросы

    class Config:
        orm_mode = True

# --- Эндпоинты ---

@router.get("/", response_model=List[TestRead])
def list_tests(
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Список всех тестов.
    """
    repo = TestRepository(session)
    return repo.ListAllTests()

@router.get("/{test_id}", response_model=TestRead)
def get_test(
    test_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Получить тест по ID."""
    repo = TestRepository(session)
    test = repo.GetTestById(test_id)
    if not test:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test not found")
    return test

@router.get("/category/{category_id}", response_model=List[TestRead])
def list_by_category(
    category_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Список тестов для заданной категории."""
    repo = TestRepository(session)
    return repo.ListTestsByCategory(category_id)

@router.post("/", response_model=TestRead, status_code=status.HTTP_201_CREATED)
def create_test(
    payload: TestCreate,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Создать новый тест."""
    repo = TestRepository(session)
    return repo.CreateTest(
        category_id=payload.category_id,
        title=payload.title,
        max_attempts=payload.max_attempts,
    )

@router.put("/{test_id}", response_model=TestRead)
def update_test(
    test_id: int,
    payload: TestUpdate,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Обновить тест."""
    repo = TestRepository(session)
    updated = repo.UpdateTest(test_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test not found")
    return updated

@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test(
    test_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Удалить тест."""
    repo = TestRepository(session)
    success = repo.DeleteTest(test_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test not found")
    return

@router.post("/import", response_model=List[TestRead])
def import_tests(
    payload: List[TestImport],
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Массовый импорт тестов из JSON-массива."""
    repo = TestRepository(session)
    created = repo.ImportTests([item.dict() for item in payload])
    return created

@router.get("/export", response_model=List[TestRead])
def export_tests(
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Массовый экспорт тестов."""
    repo = TestRepository(session)
    return repo.ExportTests()

@router.post(
    "/full",
    response_model=TestReadWithQuestions,
    status_code=status.HTTP_201_CREATED
)
def create_test_full(
    payload: TestFullCreate,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Создать тест вместе со всеми вопросами и вариантами ответов одним запросом.
    Структура payload:
    {
      "category_id": 1,
      "title": "Название теста",
      "max_attempts": 3,
      "questions": [
        {
          "text": "Вопрос 1?",
          "weight": 2,
          "options": [
            {"text": "Вариант 1", "is_correct": false},
            {"text": "Вариант 2", "is_correct": true},
            ...
          ]
        },
        {
          "text": "Вопрос 2?",
          "weight": 1,
          "options": [
            {"text": "Вариант A", "is_correct": true},
            {"text": "Вариант B", "is_correct": false},
            ...
          ]
        },
        ...
      ]
    }
    """

    # 3.1. Репозитории
    test_repo = TestRepository(session)
    question_repo = QuestionRepository(session)
    option_repo = AnswerOptionRepository(session)

    # 3.2. В рамках сессии SQLModel создаём Test
    test = test_repo.CreateTest(
        category_id=payload.category_id,
        title=payload.title,
        max_attempts=payload.max_attempts
    )

    # 3.3. Создаём все вопросы и их варианты
    created_questions: List[QuestionModel] = []
    for question_data in payload.questions:
        # а) создаём вопрос
        q = question_repo.CreateQuestion(
            test_id=test.id,
            text=question_data.text,
            weight=question_data.weight
        )

        # б) для каждого вопроса создаём все варианты ответов
        created_options: List[AnswerOptionModel] = []
        for option_data in question_data.options:
            opt = option_repo.CreateOption(
                question_id=q.id,
                text=option_data.text,
                is_correct=option_data.is_correct
            )
            created_options.append(opt)

        # в) прикрепляем к объекту q список опций (для возврата)
        #     Обратите внимание: при стандартном поведении SQLModel (если у вас настроены отношения),
        #     можно было бы просто считать q вместе с зависимыми options через join,
        #     но здесь мы вручную присваиваем, чтобы среди возвращаемых Pydantic-моделей
        #     сработал orm_mode и вложенные списки «options» отображались.
        q.options = created_options
        created_questions.append(q)

    # 3.4. К тесту добавляем список созданных вопросов
    test.questions = created_questions

    # 3.5. Возвращаем «полный» тест вместе с вопросами и опциями
    return test

@router.get(
    "/full/{test_id}",
    response_model=TestReadWithQuestions,
    status_code=status.HTTP_200_OK,
)
def get_test_full(
    test_id: int,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Получить «полный» тест: сам Test + все Questions + все AnswerOptions.
    Параметры:
    - test_id: идентификатор теста.
    """

    test_repo = TestRepository(session)
    question_repo = QuestionRepository(session)
    option_repo = AnswerOptionRepository(session)

    # 1) Проверяем, существует ли тест
    test: TestModel | None = test_repo.GetTestById(test_id)  # допустим, у репозитория есть метод GetTestById
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test с id={test_id} не найден"
        )

    # 2) Получаем все вопросы, относящиеся к этому тесту
    #    Предполагается, что есть метод list_questions_by_test (или аналогичный).
    questions: list[QuestionModel] = question_repo.ListQuestionsByTest(test_id)

    # 3) Для каждого вопроса получаем его варианты
    full_questions: list[QuestionModel] = []
    for q in questions:
        opts = option_repo.ListOptionsByQuestion(q.id)
        # Вручную прикрепляем список вариантов к вопросу, чтобы Pydantic смог сериализовать вложенный список
        q.options = opts
        full_questions.append(q)

    # 4) Прикрепляем список вопросов (с уже вложенными вариантами) к самому тесту
    test.questions = full_questions

    return test
