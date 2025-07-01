# /src/api/options.py

from typing import Generator, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from src.database import db
from src.models import AnswerOption as AnswerOptionModel
from src.repositories.answer_option_repository import AnswerOptionRepository
from src.api.auth import get_current_user

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
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

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
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

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
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = AnswerOptionRepository(session)
    success = repo.DeleteOption(option_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Option not found")
    return