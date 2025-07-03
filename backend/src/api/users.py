# /src/api/users.py

import os
from typing import Generator, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel
from sqlmodel import Session, select

from src.database import db
from src.api.auth import get_current_user
from src.models import User
from src.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])

def get_db() -> Generator[Session, None, None]:
    yield from db.get_session()

# Pydantic schemas

class UserRead(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    role_id: int
    created_at: datetime

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role_id: Optional[int] = None

class UserExport(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    role_id: int
    created_at: str  # ISO datetime

class UserImport(BaseModel):
    username: str
    password_hash: Optional[str] = ""
    role_id: int
    full_name: Optional[str] = None

# --- Endpoints ---

@router.get("/", response_model=List[UserRead])
def list_users(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 1000
):
    """
    Список пользователей.
    Если указан параметр ?role=student|teacher|admin — фильтрация по роли.
    """
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    if limit > 1000:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Limit must be <= 1000")

    repo = UserRepository(db)
    if role:
        users = repo.listByRole(role, limit)
    else:
        users = repo.listAllUsers(limit)
    return [
        UserRead(
            id=u.id,
            username=u.username,
            full_name=u.full_name,
            role_id=u.role_id,
            created_at=u.created_at,
        )
        for u in users
    ]

@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Получить пользователя по ID.
    """

    repo = UserRepository(db)
    user = repo.getUserById(user_id)  # slight typo; correct below

    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    return UserRead(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role_id=user.role_id,
        created_at=user.created_at,
    )

@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Обновить пользователя: full_name и/или role_id.
    """
    repo = UserRepository(db)
    data_model = data.model_dump(exclude_unset=True)

    if data.model_dump(exclude_unset=True) == {}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")

    if user_id != current_user.id and current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    if current_user.role.name != "admin" and data_model.get("role_id") != None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    user_object = repo.updateUser(user_id, data.model_dump(exclude_unset=True))

    if not user_object:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    return UserRead(
        id=user_object.id,
        username=user_object.username,
        full_name=user_object.full_name,
        role_id=user_object.role_id,
        created_at=user_object.created_at,
    )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Удалить пользователя по ID.
    """
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = UserRepository(db)
    success = repo.deleteUser(user_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return

@router.post("/export", response_model=List[UserExport])
def export_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Экспорт всех пользователей для Admin.
    """
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = UserRepository(db)
    data = repo.exportUsers()
    return [UserExport(**item) for item in data]
