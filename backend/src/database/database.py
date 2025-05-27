"""This is db module.

This module handles dealing with postgre database.
"""

__all__ = ["DB"]
__version__ = "0.1"
__author__ = "Wiered"

from datetime import datetime
from typing import List

import psycopg2
from sqlmodel import SQLModel, Session, create_engine, select

try:
    import models
    import utils
except:
    import src.models as models
    import src.utils as utils

class DataBase:
    def __init__(self, dbname, user, host, password, port = 5432):
        self.dbname = dbname
        self.user = user
        self.host = host
        self.password = password
        self.port = port

        self.conn = self._connectPsycopg2()
        self.cursor = self._getCursor()

        # SQLModel/SQLAlchemy engine
        self._sqlalchemy_url = (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.dbname}"
        )
        self.engine = create_engine(self._sqlalchemy_url, echo=True)

    def _connectPsycopg2(self):
        return psycopg2.connect(dbname=self.dbname, user=self.user, host=self.host, password=self.password, port=self.port)

    def _getCursor(self):
        return self.conn.cursor()

    def _commit(self):
        self.conn.commit()

    def _close(self):
        self._commit()
        self.cursor.close()
        self.conn.close()

    def _executeQuery(self, query, params):
        try:
            print("Executing Query: ")
            print(query)
            print("Params: ", params)
            self.cursor.execute(query, params)

            return self.cursor.fetchone()
        except Exception as e:

            print("Rolling back... ", e)
            self.conn.rollback()

            return False

    def getSession(self) -> Session:
        """
        Возвращает новый объект Session для работы с моделями SQLModel.
        """
        return Session(self.engine)

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

    # Users
    def userExists(self, username: str) -> bool:
        session = self.getSession()

        return not session.exec(
                select(models.User).where(models.User.username == username)
            ).first()

    def createUser(self, username: str, passwordHash: str, roleName: str) -> models.User:
        session = self.getSession()

        role = self.getRoleByName(roleName)
        user = models.User(username=username, password_hash=passwordHash, role=role)

        session.add(user)
        session.commit()
        session.refresh(user)

        return user

    def getUserByUsername(self, username: str) -> models.User | None:
        session = self.getSession()

        return session.exec(select(models.User).where(models.User.username == username)).first()

    # UTILS
    def createAllTables(self) -> None:
        """
        Создаёт в базе все таблицы, описанные в ваших SQLModel-моделях.
        Вызывает SQLModel.metadata.create_all(self.engine) –
        автоматически генерирует и выполняет DDL на создание таблиц.
        """
        SQLModel.metadata.create_all(self.engine)

    def dropAllTables(self) -> None:
        """
        Удаляет из базы все таблицы, описанные в ваших SQLModel-моделях.
        Вызывает SQLModel.metadata.drop_all(self.engine) –
        автоматически генерирует и выполняет DDL на удаление таблиц.
        """
        SQLModel.metadata.drop_all(self.engine)
