# src/api/roles.py

from typing import Generator, List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from src.database import db
from src.api.auth import get_current_user
from src.models import Role
from src.repositories.role_repository import RoleRepository

router = APIRouter(prefix="/roles", tags=["roles"])


def get_db() -> Generator[Session, None, None]:
    """
    Зависимость для получения SQLModel Session.
    """
    yield from db.get_session()


#
# Pydantic-схемы для Role
#
class RoleRead(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }


class RoleUpdate(BaseModel):
    name: str


class RoleImport(BaseModel):
    name: str


#
# Эндпоинты
#
@router.get("/", response_model=List[RoleRead])
def list_roles(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Плоский список всех ролей.
    """
    repository = RoleRepository(db)
    roles = repository.ListAllRoles()
    return [RoleRead.model_validate(r) for r in roles]


@router.get("/{role_id}", response_model=RoleRead)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Получить одну роль по ID.
    """
    # Если в репозитории нет метода GetRoleById, делаем запрос напрямую
    stmt = select(Role).where(Role.id == role_id)
    role = db.exec(stmt).first()
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    return RoleRead.model_validate(role)


@router.put("/{role_id}", response_model=RoleRead)
def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Переименовать роль: обновить её name.
    """
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repository = RoleRepository(db)
    updated = repository.UpdateRole(role_id, payload.name)
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found or rename failed")
    return RoleRead.model_validate(updated)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Удалить роль по ID.
    """
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repository = RoleRepository(db)
    success = repository.DeleteRole(role_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    return  # 204 No Content


@router.get("/export", response_model=List[Dict[str, Any]])
def export_roles(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Экспортировать все роли в JSON-подобный список.
    """
    repository = RoleRepository(db)
    data = repository.ExportRoles()
    return data


@router.post(
    "/import",
    response_model=List[RoleRead],
    status_code=status.HTTP_201_CREATED,
)
def import_roles(
    payload: List[RoleImport],
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Импортировать роли из списка JSON-объектов.
    Тело запроса: [{"name": "role1"}, {"name": "role2"}, ...]
    """
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repository = RoleRepository(db)
    # Преобразуем список Pydantic-моделей в список словарей
    raw_data = [item.model_dump() for item in payload]
    created_roles = repository.ImportRoles(raw_data)
    return [RoleRead.model_validate(r) for r in created_roles]
