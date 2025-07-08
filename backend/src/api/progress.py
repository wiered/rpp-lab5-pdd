import logging
from typing import Generator, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from src.database import db
from src.models import Progress as ProgressModel
from src.repositories.progress_repository import ProgressRepository
from src.api.auth import get_current_user

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(levelname)s:     %(name)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

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
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Список записей прогресса.
    Фильтрация по user_id или category_id необязательна.
    """
    logger.info(
        "Listing progress: user_id=%s, article_id=%s, requester=%s",
        user_id, article_id, current_user.id
    )
    if user_id != current_user.id and current_user.role.name != "admin":
        logger.warning("Access denied for listing progress by user %s", current_user.id)
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = ProgressRepository(session)
    try:
        if user_id is not None and article_id is not None:
            pr = repo.GetProgressByUserAndArticle(user_id, article_id)
            result = [pr] if pr else []
        elif user_id is not None:
            result = repo.ListProgressByUser(user_id)
        elif article_id is not None:
            result = repo.ListProgressByArticle(article_id)
        else:
            result = repo.ListAllProgress()
        logger.info("Found %d progress records", len(result))
        return result
    except Exception as e:
        logger.exception("Error listing progress")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error")

@router.get("/{progress_id}", response_model=ProgressRead)
def get_progress(
    progress_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Получить запись прогресса по ID."""
    logger.info(
        "Getting progress id=%s requested by user=%s",
        progress_id, current_user.id
    )

    if current_user.role.name != "admin":
        logger.warning(
            "Non-admin user %s attempted to get progress %s",
            current_user.id, progress_id
        )
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = ProgressRepository(session)
    progress = repo.GetProgressById(progress_id)

    if not progress:
        logger.warning("Progress id=%s not found", progress_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Progress not found")

    if progress.user_id != current_user.id:
        logger.warning(
            "User %s unauthorized for progress %s",
            current_user.id, progress_id
        )
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    logger.info(
        "Returning progress id=%s to user=%s",
        progress_id, current_user.id
    )
    return progress

@router.post("/", response_model=ProgressRead, status_code=status.HTTP_201_CREATED)
def create_progress(
    payload: ProgressCreate,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Создать новую запись прогресса."""
    logger.info(
        "Creating progress for user=%s, article=%s, status=%s requested by user=%s",
        payload.user_id, payload.article_id, payload.status, current_user.id
    )

    if current_user.role.name != "admin" and payload.user_id != current_user.id:
        logger.warning(
            "User %s forbidden to create progress for user %s",
            current_user.id, payload.user_id
        )
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = ProgressRepository(session)
    try:
        prog = repo.CreateProgress(
            user_id=payload.user_id,
            article_id=payload.article_id,
            status=payload.status,
        )
        logger.info("Created progress id=%s", prog.id)
        return prog
    except Exception as e:
        logger.exception("Error creating progress: %s", e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error")

@router.put("/", response_model=ProgressRead)
def update_progress(
    payload: ProgressUpdate,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Обновить статус прогресса для пользователем и категорией."""
    logger.info(
        "Updating progress for user=%s, article=%s to status=%s by requester=%s",
        payload.user_id, payload.article_id, payload.status, current_user.id
    )

    if current_user.role.name != "admin" and payload.user_id != current_user.id:
        logger.warning(
            "User %s forbidden to update progress for user %s",
            current_user.id, payload.user_id
        )
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = ProgressRepository(session)
    try:
        updated = repo.UpdateProgress(
            user_id=payload.user_id,
            article_id=payload.article_id,
            status=payload.status,
        )
        if not updated:
            logger.warning(
                "Progress not found for user=%s, article=%s",
                payload.user_id, payload.article_id
            )
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Progress not found for given user/category")
        logger.info("Updated progress id=%s", updated.id)
        return updated
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error updating progress")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error")

@router.delete("/{progress_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_progress(
    progress_id: int,
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Удалить запись прогресса по ID."""
    logger.info(
        "Deleting progress id=%s requested by user=%s",
        progress_id, current_user.id
    )

    if current_user.role.name != "admin":
        logger.warning(
            "Non-admin user %s attempted to delete progress %s",
            current_user.id, progress_id
        )
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = ProgressRepository(session)
    try:
        success = repo.DeleteProgress(progress_id)
        if not success:
            logger.warning("Progress id=%s not found for deletion", progress_id)
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Progress not found")
        logger.info("Deleted progress id=%s", progress_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error deleting progress")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error")
