# /src/api/tests.py

from datetime import datetime
from typing import Generator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session
from src.api.auth import get_current_user
from src.database import db
from src.models import AnswerOption as AnswerOptionModel
from src.models import Question as QuestionModel
from src.models import Test as TestModel
from src.models import TestAnswer as TestAnswerModel
from src.models import TestResult as TestResultModel
from src.repositories.answer_option_repository import AnswerOptionRepository
from src.repositories.question_repository import QuestionRepository
from src.repositories.test_answer_repository import TestAnswerRepository
from src.repositories.test_repository import TestRepository
from src.repositories.test_result_repository import TestResultRepository

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

# /src/api/questions.py

router = APIRouter(prefix="/questions", tags=["questions"])

def get_db() -> Generator[Session, None, None]:
    yield from db.get_session()

# Pydantic-схемы
class QuestionRead(BaseModel):
    id: int
    test_id: int
    text: str
    weight: int

    class Config:
        orm_mode = True

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

# --- Эндпоинты ---

@router.get("/", response_model=List[QuestionRead])
def list_questions(
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Список всех вопросов.
    """
    repo = QuestionRepository(session)
    return repo.ListAllQuestions()

@router.get("/{question_id}", response_model=QuestionRead)
def get_question(
    question_id: int,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Получить вопрос по ID."""
    repo = QuestionRepository(session)
    question = repo.GetQuestionById(question_id)
    if not question:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")
    return question

@router.get("/test/{test_id}", response_model=List[QuestionRead])
def list_by_test(
    test_id: int,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Список вопросов указанного теста."""
    repo = QuestionRepository(session)
    return repo.ListQuestionsByTest(test_id)

@router.post("/", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
def create_question(
    payload: QuestionCreate,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Создать новый вопрос."""
    repo = QuestionRepository(session)
    return repo.CreateQuestion(
        test_id=payload.test_id,
        text=payload.text,
        weight=payload.weight,
    )

@router.put("/{question_id}", response_model=QuestionRead)
def update_question(
    question_id: int,
    payload: QuestionUpdate,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Обновить поля вопроса."""
    repo = QuestionRepository(session)
    updated = repo.UpdateQuestion(question_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")
    return updated

@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Удалить вопрос по ID."""
    repo = QuestionRepository(session)
    success = repo.DeleteQuestion(question_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")
    return

# /src/api/options.py

router = APIRouter(prefix="/options", tags=["options"])

def get_db() -> Generator[Session, None, None]:
    yield from db.get_session()

# Pydantic-схемы
class OptionRead(BaseModel):
    id: int
    question_id: int
    text: str
    is_correct: bool

    class Config:
        orm_mode = True

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

# --- Эндпоинты ---

@router.get("/", response_model=List[OptionRead])
def list_options(
    question_id: Optional[int] = None,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Список вариантов ответов. Если ?question_id= задан, фильтрует по вопросу.
    """
    repo = AnswerOptionRepository(session)
    if question_id is not None:
        return repo.ListOptionsByQuestion(question_id)
    return repo.ListAllOptions()

@router.get("/{option_id}", response_model=OptionRead)
def get_option(
    option_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Получить вариант ответа по ID."""
    repo = AnswerOptionRepository(session)
    opt = repo.GetOptionById(option_id)
    if not opt:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Option not found")
    return opt

@router.get("/question/{question_id}", response_model=List[OptionRead])
def list_by_question(
    question_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Список вариантов для конкретного вопроса."""
    repo = AnswerOptionRepository(session)
    return repo.ListOptionsByQuestion(question_id)

@router.post("/", response_model=OptionRead, status_code=status.HTTP_201_CREATED)
def create_option(
    payload: OptionCreate,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Создать новый вариант ответа."""
    repo = AnswerOptionRepository(session)
    return repo.CreateOption(
        question_id=payload.question_id,
        text=payload.text,
        is_correct=payload.is_correct,
    )

@router.put("/{option_id}", response_model=OptionRead)
def update_option(
    option_id: int,
    payload: OptionUpdate,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Обновить вариант ответа."""
    repo = AnswerOptionRepository(session)
    updated = repo.UpdateOption(option_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Option not found")
    return updated

@router.delete("/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_option(
    option_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Удалить вариант ответа."""
    repo = AnswerOptionRepository(session)
    success = repo.DeleteOption(option_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Option not found")
    return

# /src/api/test_results.py

router = APIRouter(prefix="/test-results", tags=["test-results"])

def get_db() -> Generator[Session, None, None]:
    yield from db.get_session()

# Pydantic-схемы
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

# --- Эндпоинты ---

@router.get("/", response_model=List[TestResultRead])
def list_test_results(
    user_id: Optional[int] = None,
    test_id: Optional[int] = None,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Список результатов тестов. По умолчанию все, либо фильтрация по user_id или test_id.
    """
    result_repo = TestResultRepository(session)
    if user_id is not None:
        results = result_repo.ListResultsByUser(user_id)
    elif test_id is not None:
        results = result_repo.ListResultsByTest(test_id)
    else:
        results = result_repo.ListAllResults()
    return results

@router.get("/{result_id}", response_model=TestResultRead)
def get_test_result(
    result_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Получить результат теста по ID."""
    result_repo = TestResultRepository(session)
    result = result_repo.GetResultById(result_id)
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test result not found")
    return result

@router.get("/{result_id}/answers", response_model=List[TestAnswerRead])
def list_result_answers(
    result_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Список ответов для данного результата теста."""
    answer_repo = TestAnswerRepository(session)
    return answer_repo.ListAnswersByResult(result_id)

@router.post("/", response_model=TestResultRead, status_code=status.HTTP_201_CREATED)
def create_test_result(
    payload: TestResultCreate,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Создает результат теста и ответы.
    """
    result_repo = TestResultRepository(session)
    answer_repo = TestAnswerRepository(session)
    # создаем результат
    result = result_repo.CreateTestResult(
        user_id=payload.user_id,
        test_id=payload.test_id,
        score=payload.score,
        max_score=payload.max_score,
        passed=payload.passed,
    )
    # создаем ответы
    for ans in payload.answers:
        answer_repo.CreateTestAnswer(
            test_result_id=result.id,
            question_id=ans.question_id,
            selected_option_id=ans.selected_option_id,
        )
    return result

@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_result(
    result_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Удалить результат теста (и ответы по каскаду)."""
    result_repo = TestResultRepository(session)
    success = result_repo.DeleteTestResult(result_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test result not found")
    return

