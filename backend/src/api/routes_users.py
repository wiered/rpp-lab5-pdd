# /src/api/auth.py

import os
from datetime import datetime, timedelta, timezone
from typing import Generator, List, Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlmodel import Session, select
from src.api.auth import get_current_user
from src.database import db
from src.models import Progress as ProgressModel
from src.models import Role, User
from src.repositories.progress_repository import ProgressRepository
from src.repositories.user_repository import UserRepository

# Настройки JWT
SECRET_KEY = os.getenv("JWT_SECRET", "your-very-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Настраиваем Argon2
ph = PasswordHasher(
    time_cost=3,         # число итераций
    memory_cost=64 * 1024,  # 64 MiB
    parallelism=2        # число потоков
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db() -> Generator[Session, None, None]:
    yield from db.get_session()

# Pydantic-схемы
class UserRegister(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserRead(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    role: str
    created_at: datetime

# Утилиты работы с паролем
def hash_password(password: str) -> str:
    """
    Возвращает Argon2-хеш пароля, включая соль и параметры.
    """
    return ph.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """
    Проверяет, соответствует ли plain-пароль сохранённому хешу.
    """
    try:
        return ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False

# Утилита для создания JWT
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session =  Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.exec(select(User).where(User.username == username)).first()
    if not user:
        raise credentials_exception
    return user

# Эндпоинт регистрации
@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister):
    with db.getSession() as session:
        # Проверяем, что username свободен
        existing = session.exec(
            select(User).where(User.username == user_in.username)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Берём роль student
        role = session.exec(
            select(Role).where(Role.name == "student")
        ).first()
        if not role:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Role 'student' is not configured")

        # Создаём пользователя с Argon2-хешем пароля
        user = User(
            username=user_in.username,
            password_hash=hash_password(user_in.password),
            role_id=role.id
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Генерируем JWT
        token = create_access_token(
            {"sub": user.username, "role": role.name},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

    return {"access_token": token}

# Эндпоинт логина
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with db.getSession() as session:
        user = session.exec(
            select(User).where(User.username == form_data.username)
        ).first()
        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        token = create_access_token(
            {"sub": user.username, "role": user.role.name},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
    return {"access_token": token}

@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return UserRead(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role.name,
        created_at=current_user.created_at,
    )

# /src/api/users.py

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

# /src/api/progress.py

router = APIRouter(prefix="/progress", tags=["progress"])

def get_db() -> Generator[Session, None, None]:
    yield from db.get_session()

# Pydantic-схемы
class ProgressRead(BaseModel):
    id: int
    user_id: int
    article_id: int
    status: str
    updated_at: datetime

    class Config:
        orm_mode = True

class ProgressCreate(BaseModel):
    user_id: int
    article_id: int
    status: Optional[str] = "not_started"

class ProgressUpdate(BaseModel):
    user_id: int
    article_id: int
    status: str

class ProgressImport(BaseModel):
    user_id: int
    article_id: int
    status: str
    updated_at: Optional[datetime] = None

# --- Эндпоинты ---

@router.get("/", response_model=List[ProgressRead])
def list_progress(
    user_id: Optional[int] = None,
    article_id: Optional[int] = None,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Список записей прогресса.
    Фильтрация по user_id или category_id необязательна.
    """
    repo = ProgressRepository(session)
    if user_id is not None and article_id is not None:
        pr = repo.GetProgressByUserAndArticle(user_id, article_id)
        return [pr] if pr else []
    if user_id is not None:
        return repo.ListProgressByUser(user_id)
    if article_id is not None:
        return repo.ListProgressByArticle(article_id)
    return repo.ListAllProgress()

@router.get("/{progress_id}", response_model=ProgressRead)
def get_progress(
    progress_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Получить запись прогресса по ID."""
    repo = ProgressRepository(session)
    prog = repo.GetProgressById(progress_id)
    if not prog:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Progress not found")
    return prog

@router.post("/", response_model=ProgressRead, status_code=status.HTTP_201_CREATED)
def create_progress(
    payload: ProgressCreate,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Создать новую запись прогресса."""
    repo = ProgressRepository(session)
    prog = repo.CreateProgress(
        user_id=payload.user_id,
        article_id=payload.article_id,
        status=payload.status,
    )
    return prog

@router.put("/", response_model=ProgressRead)
def update_progress(
    payload: ProgressUpdate,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Обновить статус прогресса для пользователем и категорией."""
    repo = ProgressRepository(session)
    updated = repo.UpdateProgress(
        user_id=payload.user_id,
        article_id=payload.article_id,
        status=payload.status,
    )
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Progress not found for given user/category")
    return updated

@router.delete("/{progress_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_progress(
    progress_id: int,
    session: Session =  Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Удалить запись прогресса по ID."""
    repo = ProgressRepository(session)
    success = repo.DeleteProgress(progress_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Progress not found")
    return

