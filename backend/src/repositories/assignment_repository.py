from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlmodel import Session, select, delete, update
from sqlalchemy.exc import SQLAlchemyError

from src.models import Assignment

class AssignmentRepository:
    def __init__(self, session: Session):
        self.session = session

    def ListAllAssignments(self) -> List[Assignment]:
        """Возвращает все назначения категорий."""
        stmt = select(Assignment)
        return self.session.exec(stmt).all()

    def GetAssignmentById(self, assignment_id: int) -> Optional[Assignment]:
        """Возвращает назначение по ID или None, если не найдено."""
        stmt = select(Assignment).where(Assignment.id == assignment_id)
        return self.session.exec(stmt).first()

    def ListAssignmentsByUser(self, user_id: int) -> List[Assignment]:
        """Возвращает назначения, сделанные для конкретного ученика (user_id)."""
        stmt = select(Assignment).where(Assignment.user_id == user_id)
        return self.session.exec(stmt).all()

    def ListAssignmentsByGroup(self, group_id: int) -> List[Assignment]:
        """Возвращает назначения для конкретной группы."""
        stmt = select(Assignment).where(Assignment.group_id == group_id)
        return self.session.exec(stmt).all()

    def ListAssignmentsByCategory(self, category_id: int) -> List[Assignment]:
        """Возвращает назначения по категории."""
        stmt = select(Assignment).where(Assignment.category_id == category_id)
        return self.session.exec(stmt).all()

    def CreateAssignmentForUser(
        self,
        assigned_by: int,
        category_id: int,
        user_id: int,
        assigned_at: Optional[datetime] = None
    ) -> Assignment:
        """Назначает категорию конкретному пользователю."""
        assignment = Assignment(
            assigned_by=assigned_by,
            category_id=category_id,
            user_id=user_id,
            group_id=None,
            assigned_at=assigned_at or datetime.now(timezone.utc)
        )
        self.session.add(assignment)
        self.session.commit()
        self.session.refresh(assignment)
        return assignment

    def CreateAssignmentForGroup(
        self,
        assigned_by: int,
        category_id: int,
        group_id: int,
        assigned_at: Optional[datetime] = None
    ) -> Assignment:
        """Назначает категорию всей группе."""
        assignment = Assignment(
            assigned_by=assigned_by,
            category_id=category_id,
            user_id=None,
            group_id=group_id,
            assigned_at=assigned_at or datetime.now(timezone.utc)
        )
        self.session.add(assignment)
        self.session.commit()
        self.session.refresh(assignment)
        return assignment

    def UpdateAssignment(
        self,
        assignment_id: int,
        data: Dict[str, Any]
    ) -> Optional[Assignment]:
        """Обновляет поля назначения по словарю data."""
        assignment = self.GetAssignmentById(assignment_id)
        if not assignment:
            return None
        for field, value in data.items():
            if hasattr(assignment, field):
                setattr(assignment, field, value)
        self.session.add(assignment)
        self.session.commit()
        self.session.refresh(assignment)
        return assignment

    def DeleteAssignment(self, assignment_id: int) -> bool:
        """Удаляет назначение по ID. Возвращает True при успешном удалении."""
        try:
            stmt = delete(Assignment).where(Assignment.id == assignment_id)
            result = self.session.exec(stmt)
            self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def ExportAssignments(self) -> List[Dict[str, Any]]:
        """Экспортирует назначения в JSON-подобный список."""
        assignments = self.ListAllAssignments()
        return [
            {
                "id": a.id,
                "assigned_by": a.assigned_by,
                "category_id": a.category_id,
                "user_id": a.user_id,
                "group_id": a.group_id,
                "assigned_at": a.assigned_at.isoformat()
            }
            for a in assignments
        ]

    def ImportAssignments(self, data: List[Dict[str, Any]]) -> List[Assignment]:
        """Импортирует назначения из JSON-подобного списка и возвращает созданные объекты."""
        created: List[Assignment] = []
        for item in data:
            assignment = Assignment(
                assigned_by=item.get("assigned_by"),
                category_id=item.get("category_id"),
                user_id=item.get("user_id"),
                group_id=item.get("group_id"),
                assigned_at=item.get("assigned_at")
            )
            self.session.add(assignment)
            created.append(assignment)
        self.session.commit()
        for a in created:
            self.session.refresh(a)
        return created