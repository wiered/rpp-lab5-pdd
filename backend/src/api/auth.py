﻿# /src/api/auth.py

import os
from datetime import datetime, timedelta, timezone
from typing import Generator, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from jose import jwt, JWTError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlmodel import Session, select
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from src.database import db
from src.models import User, Role

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

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session =  Depends(get_db)
) -> User:
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
