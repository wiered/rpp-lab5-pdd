"""This is db module.

This module handles dealing with postgre database.
"""

__all__ = ["DataBase"]
__version__ = "1.0"
__author__ = "Wiered"

import os
from datetime import datetime
from typing import Generator, List

import src.models as models
import src.utils as utils
from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine, select

load_dotenv()

class DataBase:
    def __init__(self, dbname, user, host, password, port = 5432):
        self.dbname = dbname
        self.user = user
        self.host = host
        self.password = password
        self.port = port

        # SQLModel/SQLAlchemy engine
        self._sqlalchemy_url = (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.dbname}"
        )
        self.engine = create_engine(self._sqlalchemy_url, echo=True)

    def getSession(self) -> Session:
        """
        Возвращает новый объект Session для работы с моделями SQLModel.
        """
        return Session(self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        session = Session(self.engine)
        try:
            yield session
        finally:
            session.close()

    # ROLES
    def roleExists(self, name: str) -> bool:
        session = self.getSession()
        return not session.exec(select(models.Role).where(models.Role.name == name)).first()

    def createRole(self, name: str) -> models.Role:
        session = self.getSession()

        role = models.Role(name=name)
        session.add(role)
        session.commit()
        session.refresh(role)

        return role

    def getRoleByName(self, name: str) -> models.Role | None:
        session = self.getSession()

        return session.exec(select(models.Role).where(models.Role.name == name)).first()

    def ensureRoles(self, names: List[str]) -> None:
        """Создаёт все роли из списка, если их нет."""
        for name in names:
            if not self.roleExists(name):
                self.createRole(name)

    # UTILS
    def createAllTables(self) -> None:
        """
        Создаёт в базе все таблицы, описанные в SQLModel-моделях.
        """
        SQLModel.metadata.create_all(self.engine)

    def dropAllTables(self) -> None:
        """
        Удаляет из базы все таблицы, описанные в SQLModel-моделях.
        """
        SQLModel.metadata.drop_all(self.engine)

db = DataBase(
    os.environ.get("DB_NAME"),
    os.environ.get("DB_USER"),
    os.environ.get("DB_HOST"),
    os.environ.get("DB_PASSWORD"),
    os.environ.get("DB_PORT"),
    )
