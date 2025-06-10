# /src/api/categories.py

from typing import Generator, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from src.database import db
from src.api.auth import get_current_user
from src.models import Category
from src.repositories.category_repository import CategoryRepository

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
