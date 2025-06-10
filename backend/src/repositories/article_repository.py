from typing import List, Optional, Dict, Any

from sqlmodel import Session, select, delete, update
from sqlalchemy.exc import SQLAlchemyError

from src.models import Article

class ArticleRepository:
    def __init__(self, session: Session):
        self.session = session

    def ListAllArticles(self) -> List[Article]:
        """Возвращает список всех статей."""
        stmt = select(Article)
        return self.session.exec(stmt).all()

    def GetArticleById(self, article_id: int) -> Optional[Article]:
        """Возвращает статью по её ID или None, если не найдена."""
        stmt = select(Article).where(Article.id == article_id)
        return self.session.exec(stmt).first()

    def ListArticlesByCategory(self, category_id: int) -> List[Article]:
        """Возвращает список статей для указанной категории."""
        stmt = select(Article).where(Article.category_id == category_id)
        return self.session.exec(stmt).all()

    def CreateArticle(
        self,
        category_id: int,
        title: str,
        content: str,
        content_type: str = "markdown"
    ) -> Article:
        """Создаёт новую статью в указанной категории."""
        article = Article(
            category_id=category_id,
            title=title,
            content=content,
            content_type=content_type
        )
        self.session.add(article)
        self.session.commit()
        self.session.refresh(article)
        return article

    def UpdateArticle(
        self,
        article_id: int,
        data: Dict[str, Any]
    ) -> Optional[Article]:
        """Обновляет поля статьи по переданному словарю data."""
        article = self.GetArticleById(article_id)
        if not article:
            return None
        for field, value in data.items():
            if hasattr(article, field):
                setattr(article, field, value)
        self.session.add(article)
        self.session.commit()
        self.session.refresh(article)
        return article

    def DeleteArticle(self, article_id: int) -> bool:
        """Удаляет статью по ID. Возвращает True, если удаление прошло успешно."""
        try:
            stmt = delete(Article).where(Article.id == article_id)
            result = self.session.exec(stmt)
            self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def ExportArticles(self) -> List[Dict[str, Any]]:
        """Экспортирует все статьи в формат JSON-подобных словарей."""
        articles = self.ListAllArticles()
        return [
            {
                "id": a.id,
                "category_id": a.category_id,
                "title": a.title,
                "content": a.content,
                "content_type": a.content_type,
                "created_at": a.created_at.isoformat()
            }
            for a in articles
        ]

    def ImportArticles(
        self,
        data: List[Dict[str, Any]]
    ) -> List[Article]:
        """Импортирует статьи из JSON-подобного списка и возвращает созданные объекты."""
        created: List[Article] = []
        for item in data:
            article = Article(
                category_id=item.get("category_id"),
                title=item.get("title", ""),
                content=item.get("content", ""),
                content_type=item.get("content_type", "markdown")
            )
            self.session.add(article)
            created.append(article)
        self.session.commit()
        for a in created:
            self.session.refresh(a)
        return created
