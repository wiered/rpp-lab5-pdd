# /src/api/articles.py

from typing import Generator, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from src.database import db
from src.models import Article
from src.repositories.article_repository import ArticleRepository
from src.api.auth import get_current_user  # dependency

router = APIRouter(prefix="/articles", tags=["articles"])

def get_db() -> Generator[Session, None, None]:
    yield from db.get_session()

# Pydantic-схемы

class ArticleRead(BaseModel):
    id: int
    category_id: int
    title: str
    content: str
    content_type: str
    created_at: datetime

    class Config:
        orm_mode = True

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

# Эндпоинты

@router.get("/", response_model=List[ArticleRead])
def list_articles(
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Список всех статей.
    """
    repo = ArticleRepository(session)
    return repo.ListAllArticles()

@router.get("/{article_id}", response_model=ArticleRead)
def get_article(
    article_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Получить статью по ID.
    """
    repo = ArticleRepository(session)
    article = repo.GetArticleById(article_id)
    if not article:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Article not found")
    return article

@router.get("/category/{category_id}", response_model=List[ArticleRead])
def list_by_category(
    category_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Список статей заданной категории.
    """
    repo = ArticleRepository(session)
    return repo.ListArticlesByCategory(category_id)

@router.post("/", response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
def create_article(
    payload: ArticleCreate,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Создать новую статью.
    """
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = ArticleRepository(session)
    return repo.CreateArticle(
        category_id=payload.category_id,
        title=payload.title,
        content=payload.content,
        content_type=payload.content_type,
    )

@router.put("/{article_id}", response_model=ArticleRead)
def update_article(
    article_id: int,
    payload: ArticleUpdate,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Обновить статью.
    """
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = ArticleRepository(session)
    updated = repo.UpdateArticle(article_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Article not found")
    return updated

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Удалить статью.
    """
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = ArticleRepository(session)
    success = repo.DeleteArticle(article_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Article not found")
    return
