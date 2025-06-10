# /src/api/categories.py

from datetime import datetime
from typing import Generator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session
from src.api.auth import get_current_user  # dependency
from src.database import db
from src.models import Article
from src.models import Assignment as AssignmentModel
from src.models import Category
from src.models import Media as MediaModel
from src.repositories.article_repository import ArticleRepository
from src.repositories.assignment_repository import AssignmentRepository
from src.repositories.category_repository import CategoryRepository
from src.repositories.media_repository import MediaRepository

router = APIRouter(prefix="/categories", tags=["categories"])

def get_db() -> Generator[Session, None, None]:
    yield from db.get_session()

# Pydantic-схемы
class CategoryRead(BaseModel):
    id: int
    title: str
    parent_id: Optional[int]

    model_config = {
        "from_attributes": True
    }

class CategoryCreate(BaseModel):
    title: str
    parent_id: Optional[int] = None

class CategoryUpdate(BaseModel):
    title: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryImport(BaseModel):
    title: str
    parent_id: Optional[int] = None

# В ответе на /categories/tree возвращаем вложенные узлы
class CategoryTreeNode(BaseModel):
    id: int
    title: str
    children: List["CategoryTreeNode"] = []

    class Config:
        orm_mode = True

CategoryTreeNode.model_rebuild()

# --- Эндпоинты ---

@router.get("/", response_model=List[CategoryRead])
def list_categories(
    db: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Плоский список всех категорий.
    """
    repository = CategoryRepository(db)
    categorys = repository.ListAllCategories()
    return [CategoryRead.model_validate(c) for c in categorys]

@router.get("/tree", response_model=List[CategoryTreeNode])
def get_category_tree(
    db: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Дерево категорий (вложенность).
    """
    repository = CategoryRepository(db)
    tree = repository.GetCategoryTree()
    # дерево уже в виде списка словарей {id,title,children}
    return tree

@router.get("/{category_id}", response_model=CategoryRead)
def get_category(
    category_id: int,
    db: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Получить одну категорию по ID.
    """
    repository = CategoryRepository(db)
    category = repository.GetCategoryById(category_id)
    if not category:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    return CategoryRead.model_validate(category)

@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Создать новую категорию.
    """
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repository = CategoryRepository(db)
    category = repository.CreateCategory(title=payload.title, parent_id=payload.parent_id)
    return CategoryRead.model_validate(category)

@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Обновить категорию: title и/или parent_id.
    """
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repository = CategoryRepository(db)
    updated = repository.UpdateCategory(category_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    return CategoryRead.model_validate(updated)

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Удалить категорию по ID.
    """
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repository = CategoryRepository(db)
    success = repository.DeleteCategory(category_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    return

# /src/api/articles.py

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

# /src/api/assignments.py



router = APIRouter(prefix="/assignments", tags=["assignments"])

def get_db() -> Generator[Session, None, None]:
    yield from db.get_session()

# Pydantic-схемы
class AssignmentRead(BaseModel):
    id: int
    assigned_by: int
    category_id: int
    user_id: Optional[int]
    group_id: Optional[int]
    assigned_at: datetime

    class Config:
        orm_mode = True

class AssignmentCreateUser(BaseModel):
    assigned_by: int
    category_id: int
    user_id: int
    assigned_at: Optional[datetime] = None

class AssignmentCreateGroup(BaseModel):
    assigned_by: int
    category_id: int
    group_id: int
    assigned_at: Optional[datetime] = None

class AssignmentUpdate(BaseModel):
    user_id: Optional[int] = None
    group_id: Optional[int] = None

class AssignmentImport(BaseModel):
    assigned_by: int
    category_id: int
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    assigned_at: Optional[datetime] = None

# --- Эндпоинты ---

@router.get("/", response_model=List[AssignmentRead])
def list_assignments(
    user_id: Optional[int] = None,
    group_id: Optional[int] = None,
    category_id: Optional[int] = None,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Список назначений. Фильтрация по user_id, group_id или category_id.
    """
    repo = AssignmentRepository(session)
    if user_id is not None:
        return repo.ListAssignmentsByUser(user_id)
    if group_id is not None:
        return repo.ListAssignmentsByGroup(group_id)
    if category_id is not None:
        return repo.ListAssignmentsByCategory(category_id)
    return repo.ListAllAssignments()

@router.get("/{assignment_id}", response_model=AssignmentRead)
def get_assignment(
    assignment_id: int,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Получить назначение по ID."""
    repo = AssignmentRepository(session)
    assg = repo.GetAssignmentById(assignment_id)
    if not assg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    return assg

@router.post("/user", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment_user(
    payload: AssignmentCreateUser,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Назначить категорию конкретному пользователю."""
    repo = AssignmentRepository(session)
    return repo.CreateAssignmentForUser(
        assigned_by=payload.assigned_by,
        category_id=payload.category_id,
        user_id=payload.user_id,
        assigned_at=payload.assigned_at,
    )

@router.post("/group", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment_group(
    payload: AssignmentCreateGroup,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Назначить категорию группе."""
    repo = AssignmentRepository(session)
    return repo.CreateAssignmentForGroup(
        assigned_by=payload.assigned_by,
        category_id=payload.category_id,
        group_id=payload.group_id,
        assigned_at=payload.assigned_at,
    )

@router.put("/{assignment_id}", response_model=AssignmentRead)
def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Обновить назначение (user_id или group_id)."""
    repo = AssignmentRepository(session)
    updated = repo.UpdateAssignment(assignment_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    return updated

@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Удалить назначение по ID."""
    repo = AssignmentRepository(session)
    success = repo.DeleteAssignment(assignment_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    return

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
def list_media_by_article(
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

