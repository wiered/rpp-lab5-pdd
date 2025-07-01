# /src/api/progress.py

from typing import Generator, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from src.database import db
from src.models import Progress as ProgressModel
from src.repositories.progress_repository import ProgressRepository
from src.api.auth import get_current_user

router = APIRouter(prefix="/progress", tags=["progress"])

def get_db() -> Generator[Session, None, None]:
    yield from db.get_session()

# Pydantic-схемы
class ProgressRead(BaseModel):
    id: int
    user_id: int
    article_id: int
    status: str
    updated_at: datetime

    class Config:
        orm_mode = True

class ProgressCreate(BaseModel):
    user_id: int
    article_id: int
    status: Optional[str] = "not_started"

class ProgressUpdate(BaseModel):
    user_id: int
    article_id: int
    status: str

class ProgressImport(BaseModel):
    user_id: int
    article_id: int
    status: str
    updated_at: Optional[datetime] = None

# --- Эндпоинты ---

@router.get("/", response_model=List[ProgressRead])
def list_progress(
    user_id: Optional[int] = None,
    article_id: Optional[int] = None,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Список записей прогресса.
    Фильтрация по user_id или category_id необязательна.
    """
    if not user_id != current_user.id and current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = ProgressRepository(session)
    if user_id is not None and article_id is not None:
        pr = repo.GetProgressByUserAndArticle(user_id, article_id)
        return [pr] if pr else []
    if user_id is not None:
        return repo.ListProgressByUser(user_id)
    if article_id is not None:
        return repo.ListProgressByArticle(article_id)
    return repo.ListAllProgress()

@router.get("/{progress_id}", response_model=ProgressRead)
def get_progress(
    progress_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Получить запись прогресса по ID."""

    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = ProgressRepository(session)
    progress = repo.GetProgressById(progress_id)

    if not progress:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Progress not found")

    if progress.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    return progress

@router.post("/", response_model=ProgressRead, status_code=status.HTTP_201_CREATED)
def create_progress(
    payload: ProgressCreate,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Создать новую запись прогресса."""
    if current_user.role.name != "admin" and payload.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = ProgressRepository(session)
    prog = repo.CreateProgress(
        user_id=payload.user_id,
        article_id=payload.article_id,
        status=payload.status,
    )
    return prog

@router.put("/", response_model=ProgressRead)
def update_progress(
    payload: ProgressUpdate,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Обновить статус прогресса для пользователем и категорией."""
    if current_user.role.name != "admin" and payload.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = ProgressRepository(session)
    updated = repo.UpdateProgress(
        user_id=payload.user_id,
        article_id=payload.article_id,
        status=payload.status,
    )
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Progress not found for given user/category")
    return updated

@router.delete("/{progress_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_progress(
    progress_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Удалить запись прогресса по ID."""
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = ProgressRepository(session)
    success = repo.DeleteProgress(progress_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Progress not found")
    return
