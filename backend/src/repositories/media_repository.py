from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlmodel import Session, select, delete, update
from sqlalchemy.exc import SQLAlchemyError

from src.models import Media

class MediaRepository:
    def __init__(self, session: Session):
        self.session = session

    def ListAllMedia(self) -> List[Media]:
        """Возвращает список всех медиаэлементов."""
        stmt = select(Media)
        return self.session.exec(stmt).all()

    def GetMediaById(self, media_id: int) -> Optional[Media]:
        """Возвращает медиаэлемент по его ID или None, если не найден."""
        stmt = select(Media).where(Media.id == media_id)
        return self.session.exec(stmt).first()

    def ListMediaByArticle(self, article_id: int) -> List[Media]:
        """Возвращает все медиаэлементы для указанной статьи."""
        stmt = select(Media).where(Media.article_id == article_id).order_by(Media.sort_order)
        return self.session.exec(stmt).all()

    def CreateMedia(self, article_id: int, media_type: str, url: str, sort_order: int = 0) -> Media:
        """Создаёт новый медиаэлемент для статьи."""
        media = Media(
            article_id=article_id,
            media_type=media_type,
            url=url,
            sort_order=sort_order
        )
        self.session.add(media)
        self.session.commit()
        self.session.refresh(media)
        return media

    def UpdateMedia(self, media_id: int, data: Dict[str, Any]) -> Optional[Media]:
        """Обновляет поля медиаэлемента по переданному словарю data."""
        media = self.GetMediaById(media_id)
        if not media:
            return None
        for field, value in data.items():
            if hasattr(media, field):
                setattr(media, field, value)
        self.session.add(media)
        self.session.commit()
        self.session.refresh(media)
        return media

    def DeleteMedia(self, media_id: int) -> bool:
        """Удаляет медиаэлемент по ID. Возвращает True, если удаление прошло успешно."""
        try:
            stmt = delete(Media).where(Media.id == media_id)
            result = self.session.exec(stmt)
            self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def ExportMedia(self) -> List[Dict[str, Any]]:
        """Экспортирует все медиа в формат JSON-подобного списка."""
        media_list = self.ListAllMedia()
        return [
            {
                "id": m.id,
                "article_id": m.article_id,
                "media_type": m.media_type,
                "url": m.url,
                "sort_order": m.sort_order
            }
            for m in media_list
        ]

    def ImportMedia(self, data: List[Dict[str, Any]]) -> List[Media]:
        """Импортирует медиа из JSON-подобного списка и возвращает созданные объекты."""
        created: List[Media] = []
        for item in data:
            media = Media(
                article_id=item.get("article_id"),
                media_type=item.get("media_type", "png"),
                url=item.get("url", ""),
                sort_order=item.get("sort_order", 0)
            )
            self.session.add(media)
            created.append(media)
        self.session.commit()
        for m in created:
            self.session.refresh(m)
        return created
