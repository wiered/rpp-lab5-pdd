# /src/api/questions.py

from typing import Generator, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from src.database import db
from src.models import Question as QuestionModel
from src.repositories.question_repository import QuestionRepository
from src.api.auth import get_current_user

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
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

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
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

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
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = QuestionRepository(session)
    success = repo.DeleteQuestion(question_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")
    return
