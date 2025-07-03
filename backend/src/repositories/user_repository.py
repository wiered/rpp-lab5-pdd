from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, delete, update
from sqlalchemy.exc import SQLAlchemyError
from src.models import User, Role

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def userExists(self, username: str) -> bool:
        return not self.session.exec(
                select(User).where(User.username == username)
            ).first()

    def createUser(self, username: str, passwordHash: str, roleName: str) -> User:
        role = self.getRoleByName(roleName)
        user = User(username=username, password_hash=passwordHash, role=role)

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    def getUserByUsername(self, username: str) -> User | None:
        return self.session.exec(select(User).where(User.username == username)).first()

    def getUserById(self, id: int) -> User | None:
        return self.session.exec(select(User).where(User.id == id)).first()

    def updateUser(self, user_id: int, data: Dict[str, Any]) -> Optional[User]:
        """
        Обновляет поля пользователя по переданному словарю data.
        Возвращает обновлённый объект или None, если не найден.
        """
        stmt = select(User).where(User.id == user_id)
        user = self.session.exec(stmt).first()
        if not user:
            return None
        for field, value in data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def deleteUser(self, user_id: int) -> bool:
        """Удаляет пользователя по ID. Возвращает True, если удаление прошло успешно."""
        try:
            stmt = delete(User).where(User.id == user_id)
            result = self.session.exec(stmt)
            self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            self.session.rollback()
            return False

    # --- Дополнительные CRUD-методы ---
    def listAllUsers(self, limit) -> List[User]:
        """Возвращает список всех пользователей."""
        statement = select(User).limit(limit)
        return self.session.exec(statement).all()

    def listByRole(self, role_name: str, limit: int = 1000) -> List[User]:
        """Возвращает список пользователей определённой роли."""
        stmt_role = select(Role).where(Role.name == role_name)
        role = self.session.exec(stmt_role).first()
        if not role:
            return []
        stmt = select(User).where(User.role_id == role.id).limit(limit)
        return self.session.exec(stmt).all()

    def changePassword(self, user_id: int, new_hash: str) -> bool:
        """Меняет пароль пользователя на новый хеш. Возвращает True при успехе."""
        try:
            stmt = update(User).where(User.id == user_id).values(password_hash=new_hash)
            result = self.session.exec(stmt)
            self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def assignRole(self, user_id: int, role_name: str) -> bool:
        """Назначает пользователю новую роль по имени. Возвращает True при успехе."""
        stmt_role = select(Role).where(Role.name == role_name)
        role = self.session.exec(stmt_role).first()
        if not role:
            return False
        try:
            stmt = update(User).where(User.id == user_id).values(role_id=role.id)
            result = self.session.exec(stmt)
            self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            self.session.rollback()
            return False

    # --- Методы для импорта/экспорта JSON ---
    def exportUsers(self) -> List[Dict[str, Any]]:
        """Экспортирует всех пользователей в список словарей для JSON."""
        users = self.listAllUsers()
        return [
            {
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "role_id": u.role_id,
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ]

    def importUsers(self, data: List[Dict[str, Any]]) -> List[User]:
        """Импортирует пользователей из списка словарей, возвращает созданные объекты."""
        created = []
        for item in data:
            if not self.user_exists(item["username"]):
                user = User(
                    username=item["username"],
                    password_hash=item.get("password_hash", ""),
                    role_id=item.get("role_id", None),
                    full_name=item.get("full_name", None)
                )
                self.session.add(user)
                created.append(user)
        self.session.commit()
        for u in created:
            self.session.refresh(u)
        return created
