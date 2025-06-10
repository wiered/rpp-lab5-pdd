from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlmodel import Session, select, delete, update
from sqlalchemy.exc import SQLAlchemyError

from src.models import Progress

class ProgressRepository:
    def __init__(self, session: Session):
        self.session = session

    def ListAllProgress(self) -> List[Progress]:
        """Возвращает все записи прогресса."""
        stmt = select(Progress)
        return self.session.exec(stmt).all()

    def GetProgressById(self, progress_id: int) -> Optional[Progress]:
        """Возвращает запись прогресса по ID или None."""
        stmt = select(Progress).where(Progress.id == progress_id)
        return self.session.exec(stmt).first()

    def ListProgressByUser(self, user_id: int) -> List[Progress]:
        """Возвращает прогресс для заданного пользователя."""
        stmt = select(Progress).where(Progress.user_id == user_id)
        return self.session.exec(stmt).all()

    def ListProgressByArticle(self, article_id: int) -> List[Progress]:
        """Возвращает все записи прогресса по категории."""
        stmt = select(Progress).where(Progress.article_id == article_id)
        return self.session.exec(stmt).all()

    def GetProgressByUserAndArticle(self, user_id: int, article_id: int) -> Optional[Progress]:
        """Возвращает прогресс конкретного пользователя по конкретной категории."""
        stmt = select(Progress).where(
            (Progress.user_id == user_id) &
            (Progress.article_id == article_id)
        )
        return self.session.exec(stmt).first()

    def CreateProgress(
        self,
        user_id: int,
        article_id: int,
        status: str = "not_started",
        updated_at: Optional[datetime] = None
    ) -> Progress:
        """Создаёт новую запись прогресса для пользователя и категории."""
        progress = Progress(
            user_id=user_id,
            article_id=article_id,
            status=status,
            updated_at=updated_at or datetime.now(timezone.utc)
        )
        self.session.add(progress)
        self.session.commit()
        self.session.refresh(progress)
        return progress

    def UpdateProgress(
        self,
        user_id: int,
        article_id: int,
        status: Optional[str] = None,
        updated_at: Optional[datetime] = None
    ) -> Optional[Progress]:
        """Обновляет статус прогресса для заданного пользователя и категории."""
        progress = self.GetProgressByUserAndArticle(user_id, article_id)
        if not progress:
            return None
        if status is not None:
            setattr(progress, "status", status)
        if updated_at is not None:
            setattr(progress, "updated_at", updated_at)
        else:
            setattr(progress, "updated_at", datetime.now(timezone.utc))
        self.session.add(progress)
        self.session.commit()
        self.session.refresh(progress)
        return progress

    def DeleteProgress(self, progress_id: int) -> bool:
        """Удаляет запись прогресса по ID. Возвращает True при успехе."""
        try:
            stmt = delete(Progress).where(Progress.id == progress_id)
            result = self.session.exec(stmt)
            self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def ExportProgress(self) -> List[Dict[str, Any]]:
        """Экспортирует все записи прогресса в формат JSON-подобный список."""
        items = self.ListAllProgress()
        return [
            {
                "id": p.id,
                "user_id": p.user_id,
                "article_id": p.article_id,
                "status": p.status,
                "updated_at": p.updated_at.isoformat()
            }
            for p in items
        ]

    def ImportProgress(self, data: List[Dict[str, Any]]) -> List[Progress]:
        """Импортирует записи прогресса из JSON-подобного списка, возвращает созданные объекты."""
        created: List[Progress] = []
        for item in data:
            # допустимые статусы: not_started, in_progress, done
            progress = Progress(
                user_id=item.get("user_id"),
                article_id=item.get("article_id"),
                status=item.get("status", "not_started"),
                updated_at=datetime.fromisoformat(item.get("updated_at")) if item.get("updated_at") else datetime.now(timezone.utc)
            )
            self.session.add(progress)
            created.append(progress)
        self.session.commit()
        for p in created:
            self.session.refresh(p)
        return created
