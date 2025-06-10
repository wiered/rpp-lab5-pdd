# /src/api/test_results.py

from typing import Generator, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from src.database import db
from src.models import TestResult as TestResultModel, TestAnswer as TestAnswerModel
from src.repositories.test_result_repository import TestResultRepository
from src.repositories.test_answer_repository import TestAnswerRepository
from src.api.auth import get_current_user

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
