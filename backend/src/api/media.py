from typing import Generator, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from src.database import db
from src.models import Media as MediaModel
from src.repositories.media_repository import MediaRepository
from src.api.auth import get_current_user

router = APIRouter(prefix="/media", tags=["media"])

def get_db() -> Generator[Session, None, None]:
    yield from db.get_session()

# Pydantic-схемы
class MediaRead(BaseModel):
    id: int
    article_id: int
    media_type: str
    url: str
    sort_order: int

    model_config = {
        "from_attributes": True
    }

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

# --- Эндпоинты ---

@router.get("/", response_model=List[MediaRead])
def list_media(
    article_id: Optional[int] = None,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Список медиа. Если указан query-параметр ?article_id=, возвращает только для этой статьи.
    """
    repo = MediaRepository(session)
    if article_id is None:
        return repo.ListAllMedia()
    return repo.ListMediaByArticle(article_id)

@router.get("/{media_id}", response_model=MediaRead)
def get_media_by_id(
    media_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Получить медиа по ID."""
    repo = MediaRepository(session)
    media = repo.GetMediaById(media_id)
    if not media:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Media not found")
    return media

@router.get("/article/{article_id}", response_model=List[MediaRead])
def list_media_by_article(
    article_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Получить медиа по ID."""
    repo = MediaRepository(session)
    media = repo.ListMediaByArticle(article_id)
    if not media:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Media not found")
    return media

@router.post("/", response_model=MediaRead, status_code=status.HTTP_201_CREATED)
def create_media(
    payload: MediaCreate,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Создать новый медиаэлемент."""
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = MediaRepository(session)
    return repo.CreateMedia(
        article_id=payload.article_id,
        media_type=payload.media_type,
        url=payload.url,
        sort_order=payload.sort_order,
    )

@router.put("/{media_id}", response_model=MediaRead)
def update_media(
    media_id: int,
    payload: MediaUpdate,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Обновить медиа."""
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = MediaRepository(session)
    updated = repo.UpdateMedia(media_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Media not found")
    return updated

@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Удалить медиа."""
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = MediaRepository(session)
    success = repo.DeleteMedia(media_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Media not found")
    return
