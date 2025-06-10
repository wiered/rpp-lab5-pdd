from typing import List, Optional, Dict, Any

from sqlmodel import Session, select, delete, update
from sqlalchemy.exc import SQLAlchemyError

from src.models import Role

class RoleRepository:
    def __init__(self, session: Session):
        self.session = session

    def ListAllRoles(self) -> List[Role]:
        """Возвращает список всех ролей."""
        stmt = select(Role)
        return self.session.exec(stmt).all()

    def UpdateRole(self, role_id: int, new_name: str) -> Optional[Role]:
        """
        Переименовывает роль с указанным ID. Возвращает обновлённый объект или None, если не найден.
        """
        stmt = select(Role).where(Role.id == role_id)
        role = self.session.exec(stmt).first()
        if not role:
            return None
        try:
            stmt_update = update(Role).where(Role.id == role_id).values(name=new_name)
            self.session.exec(stmt_update)
            self.session.commit()
            # Обновляем атрибуты и возвращаем
            role.name = new_name
            self.session.refresh(role)
            return role
        except SQLAlchemyError:
            self.session.rollback()
            return None

    def DeleteRole(self, role_id: int) -> bool:
        """
        Удаляет роль по ID. Возвращает True, если удаление успешно.
        """
        try:
            stmt_delete = delete(Role).where(Role.id == role_id)
            result = self.session.exec(stmt_delete)
            self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def ExportRoles(self) -> List[Dict[str, Any]]:
        """Экспортирует роли в формат JSON-подобных словарей."""
        roles = self.ListAllRoles()
        return [{"id": r.id, "name": r.name} for r in roles]

    def ImportRoles(self, data: List[Dict[str, Any]]) -> List[Role]:
        """Импортирует роли из JSON-подобного списка и возвращает созданные объекты."""
        created: List[Role] = []
        for item in data:
            name = item.get("name")
            if name and not self.RoleExists(name):
                role = Role(name=name)
                self.session.add(role)
                created.append(role)
        self.session.commit()
        for r in created:
            self.session.refresh(r)
        return created
