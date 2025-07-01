# /src/api/test_results.py

from datetime import datetime
from typing import Generator, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session

import src.models as models
import src.repositories as repos
from src.api.auth import get_current_user
from src.database import db
from src.models import Test as TestModel
from src.models import TestAnswer as TestAnswerModel
from src.models import TestResult as TestResultModel
from src.repositories.test_answer_repository import TestAnswerRepository
from src.repositories.test_result_repository import TestResultRepository

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

def _get_test_full(
    test_id: int,
    session: Session = Depends(get_db)
):
    """
    Получить «полный» тест: сам Test + все Questions + все AnswerOptions.
    Параметры:
    - test_id: идентификатор теста.
    """

    test_repo = repos.TestRepository(session)
    question_repo = repos.QuestionRepository(session)
    option_repo = repos.AnswerOptionRepository(session)

    # 1) Проверяем, существует ли тест
    test: TestModel | None = test_repo.GetTestById(test_id)  # допустим, у репозитория есть метод GetTestById
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test с id={test_id} не найден"
        )

    # 2) Получаем все вопросы, относящиеся к этому тесту
    #    Предполагается, что есть метод list_questions_by_test (или аналогичный).
    questions: list[models.QuestionModel] = question_repo.ListQuestionsByTest(test_id)

    # 3) Для каждого вопроса получаем его варианты
    full_questions: list[models.QuestionModel] = []
    for q in questions:
        opts = option_repo.ListOptionsByQuestion(q.id)
        # Вручную прикрепляем список вариантов к вопросу, чтобы Pydantic смог сериализовать вложенный список
        q.options = opts
        full_questions.append(q)

    # 4) Прикрепляем список вопросов (с уже вложенными вариантами) к самому тесту
    test.questions = full_questions

    return test

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
    if current_user.role.name != "admin" and user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

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

    if current_user.role.name != "admin" and result.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

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
    answers = answer_repo.ListAnswersByResult(result_id)
    if not answers:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test result not found")

    test_result = answers[0].test_result_id
    test_result = TestResultRepository(session).GetResultById(test_result)
    if current_user.role.name != "admin" and test_result.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    return answers

@router.post("/", response_model=TestResultRead, status_code=status.HTTP_201_CREATED)
def create_test_result(
    payload: TestResultCreate,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Создает результат теста и ответы.
    """
    if current_user.role.name != "admin" and payload.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    tests_repo = repos.TestRepository(session)
    if not tests_repo.GetTestById(payload.test_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test not found")

    full_test = _get_test_full(payload.test_id, session)

    # создаем результат
    result_repo = TestResultRepository(session)
    result = result_repo.CreateTestResult(
        user_id=payload.user_id,
        test_id=payload.test_id,
        score=payload.score,
        max_score=payload.max_score,
        passed=payload.passed,
    )

    # for validation
    valid_question_ids = {q.id for q in full_test.questions}
    options_by_question = {
        q.id: {opt.id for opt in q.options}
        for q in full_test.questions
    }

    # # создаем ответы
    answer_repo = TestAnswerRepository(session)

    for ans in payload.answers:
        if ans.question_id not in valid_question_ids:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f"Question {ans.question_id} not found in this test"
            )

        if ans.selected_option_id not in options_by_question[ans.question_id]:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid option {ans.selected_option_id} for question {ans.question_id}"
                )


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
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    result_repo = TestResultRepository(session)
    success = result_repo.DeleteTestResult(result_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test result not found")
    return
