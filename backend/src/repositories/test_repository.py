from typing import List, Optional, Dict, Any

from sqlmodel import Session, select, delete, update
from sqlalchemy.exc import SQLAlchemyError

from src.models import Test

class TestRepository:
    def __init__(self, session: Session):
        self.session = session

    def ListAllTests(self) -> List[Test]:
        """Возвращает список всех тестов."""
        stmt = select(Test)
        return self.session.exec(stmt).all()

    def GetTestById(self, test_id: int) -> Optional[Test]:
        """Возвращает тест по ID или None, если не найден."""
        stmt = select(Test).where(Test.id == test_id)
        return self.session.exec(stmt).first()

    def ListTestsByCategory(self, category_id: int) -> List[Test]:
        """Возвращает список тестов для заданной категории."""
        stmt = select(Test).where(Test.category_id == category_id)
        return self.session.exec(stmt).all()

    def CreateTest(self, category_id: int, title: str, max_attempts: int = 3) -> Test:
        """Создаёт новый тест в указанной категории."""
        test = Test(category_id=category_id, title=title, max_attempts=max_attempts)
        self.session.add(test)
        self.session.commit()
        self.session.refresh(test)
        return test

    def UpdateTest(self, test_id: int, data: Dict[str, Any]) -> Optional[Test]:
        """Обновляет поля теста по переданному словарю data."""
        test = self.GetTestById(test_id)
        if not test:
            return None
        for field, value in data.items():
            if hasattr(test, field):
                setattr(test, field, value)
        self.session.add(test)
        self.session.commit()
        self.session.refresh(test)
        return test

    def DeleteTest(self, test_id: int) -> bool:
        """Удаляет тест по ID. Возвращает True, если удаление успешно."""
        try:
            stmt = delete(Test).where(Test.id == test_id)
            result = self.session.exec(stmt)
            self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def ExportTests(self) -> List[Dict[str, Any]]:
        """Экспортирует все тесты в формат JSON-подобных словарей."""
        tests = self.ListAllTests()
        return [
            {"id": t.id, "category_id": t.category_id, "title": t.title, "max_attempts": t.max_attempts}
            for t in tests
        ]

    def ImportTests(self, data: List[Dict[str, Any]]) -> List[Test]:
        """Импортирует тесты из JSON-подобного списка и возвращает созданные объекты."""
        created: List[Test] = []
        for item in data:
            # ожидаем поля category_id, title, max_attempts
            test = Test(
                category_id=item.get("category_id"),
                title=item.get("title", ""),
                max_attempts=item.get("max_attempts", 3)
            )
            self.session.add(test)
            created.append(test)
        self.session.commit()
        for t in created:
            self.session.refresh(t)
        return created
