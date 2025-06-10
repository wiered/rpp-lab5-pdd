from typing import List, Optional, Dict, Any

from sqlmodel import Session, select, delete, update
from sqlalchemy.exc import SQLAlchemyError

from src.models import Category

class CategoryRepository:
    def __init__(self, session: Session):
        self.session = session

    def ListAllCategories(self) -> List[Category]:
        """Возвращает список всех категорий."""
        stmt = select(Category)
        return self.session.exec(stmt).all()

    def GetCategoryById(self, category_id: int) -> Optional[Category]:
        """Возвращает категорию по ID или None, если не найдена."""
        stmt = select(Category).where(Category.id == category_id)
        return self.session.exec(stmt).first()

    def ListSubcategories(self, parent_id: Optional[int] = None) -> List[Category]:
        """Возвращает список прямых подкатегорий для данного parent_id (None для корневых)."""
        stmt = select(Category).where(Category.parent_id == parent_id)
        return self.session.exec(stmt).all()

    def CreateCategory(self, title: str, parent_id: Optional[int] = None) -> Category:
        """Создает новую категорию с необязательным родителем."""
        category = Category(title=title, parent_id=parent_id)
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return category

    def UpdateCategory(self, category_id: int, data: Dict[str, Any]) -> Optional[Category]:
        """Обновляет поля категории по переданному словарю data."""
        category = self.GetCategoryById(category_id)
        if not category:
            return None
        for field, value in data.items():
            if hasattr(category, field):
                setattr(category, field, value)
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return category

    def DeleteCategory(self, category_id: int) -> bool:
        """Удаляет категорию по ID. Возвращает True, если удаление успешно."""
        try:
            stmt = delete(Category).where(Category.id == category_id)
            result = self.session.exec(stmt)
            self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def GetCategoryTree(self) -> List[Dict[str, Any]]:
        """Возвращает дерево категорий в виде вложенных словарей."""
        categories = self.ListAllCategories()
        cat_map = {cat.id: {"id": cat.id, "title": cat.title, "children": []} for cat in categories}
        tree: List[Dict[str, Any]] = []
        for cat in categories:
            node = cat_map[cat.id]
            if cat.parent_id and cat.parent_id in cat_map:
                cat_map[cat.parent_id]["children"].append(node)
            else:
                tree.append(node)
        return tree
