# /src/api/assignments.py

from typing import Generator, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from src.database import db
from src.models import Assignment as AssignmentModel
from src.repositories.assignment_repository import AssignmentRepository
from src.api.auth import get_current_user

router = APIRouter(prefix="/assignments", tags=["assignments"])

def get_db() -> Generator[Session, None, None]:
    yield from db.get_session()

# Pydantic-схемы
class AssignmentRead(BaseModel):
    id: int
    assigned_by: int
    category_id: int
    user_id: Optional[int]
    group_id: Optional[int]
    assigned_at: datetime

    class Config:
        orm_mode = True

class AssignmentCreateUser(BaseModel):
    assigned_by: int
    category_id: int
    user_id: int
    assigned_at: Optional[datetime] = None

class AssignmentCreateGroup(BaseModel):
    assigned_by: int
    category_id: int
    group_id: int
    assigned_at: Optional[datetime] = None

class AssignmentUpdate(BaseModel):
    user_id: Optional[int] = None
    group_id: Optional[int] = None

class AssignmentImport(BaseModel):
    assigned_by: int
    category_id: int
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    assigned_at: Optional[datetime] = None

# --- Эндпоинты ---

@router.get("/", response_model=List[AssignmentRead])
def list_assignments(
    user_id: Optional[int] = None,
    group_id: Optional[int] = None,
    category_id: Optional[int] = None,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Список назначений. Фильтрация по user_id, group_id или category_id.
    """
    repo = AssignmentRepository(session)
    if user_id is not None:
        return repo.ListAssignmentsByUser(user_id)
    if group_id is not None:
        return repo.ListAssignmentsByGroup(group_id)
    if category_id is not None:
        return repo.ListAssignmentsByCategory(category_id)
    return repo.ListAllAssignments()

@router.get("/{assignment_id}", response_model=AssignmentRead)
def get_assignment(
    assignment_id: int,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Получить назначение по ID."""
    repo = AssignmentRepository(session)
    assg = repo.GetAssignmentById(assignment_id)
    if not assg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    return assg

@router.post("/user", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment_user(
    payload: AssignmentCreateUser,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Назначить категорию конкретному пользователю."""
    repo = AssignmentRepository(session)
    return repo.CreateAssignmentForUser(
        assigned_by=payload.assigned_by,
        category_id=payload.category_id,
        user_id=payload.user_id,
        assigned_at=payload.assigned_at,
    )

@router.post("/group", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment_group(
    payload: AssignmentCreateGroup,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Назначить категорию группе."""
    repo = AssignmentRepository(session)
    return repo.CreateAssignmentForGroup(
        assigned_by=payload.assigned_by,
        category_id=payload.category_id,
        group_id=payload.group_id,
        assigned_at=payload.assigned_at,
    )

@router.put("/{assignment_id}", response_model=AssignmentRead)
def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Обновить назначение (user_id или group_id)."""
    repo = AssignmentRepository(session)
    updated = repo.UpdateAssignment(assignment_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    return updated

@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int,
    session: Session =  Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Удалить назначение по ID."""
    repo = AssignmentRepository(session)
    success = repo.DeleteAssignment(assignment_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    return

