﻿# /src/api/users.py

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
):
    """
    Список пользователей.
    Если указан параметр ?role=student|teacher|admin — фильтрация по роли.
    """
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = UserRepository(db)
    if role:
        users = repo.listByRole(role)
    else:
        users = repo.listAllUsers()
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
    print("Update user:", user_id, data)
    repo = UserRepository(db)
    updated = repo.updateUser(user_id, data.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    return UserRead(
        id=updated.id,
        username=updated.username,
        full_name=updated.full_name,
        role_id=updated.role_id,
        created_at=updated.created_at,
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

@router.post("/import", response_model=List[UserRead])
def import_users(
    payload: List[UserImport] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Импорт пользователей из JSON-массива.
    """
    if current_user.role.name != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    repo = UserRepository(db)
    created = repo.importUsers([BaseModel.model_dump(item) for item in payload])
    return [
        UserRead(
            id=u.id,
            username=u.username,
            full_name=u.full_name,
            role_id=u.role_id,
            created_at=u.created_at,
        )
        for u in created
    ]
