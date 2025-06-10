from typing import List, Optional, Dict, Any

from sqlmodel import Session, select, delete, update
from sqlalchemy.exc import SQLAlchemyError

from src.models import TestResult

class TestResultRepository:
    def __init__(self, session: Session):
        self.session = session

    def ListAllResults(self) -> List[TestResult]:
        """Возвращает список всех результатов тестов."""
        stmt = select(TestResult)
        return self.session.exec(stmt).all()

    def GetResultById(self, result_id: int) -> Optional[TestResult]:
        """Возвращает результат теста по ID или None, если не найден."""
        stmt = select(TestResult).where(TestResult.id == result_id)
        return self.session.exec(stmt).first()

    def ListResultsByUser(self, user_id: int) -> List[TestResult]:
        """Возвращает все результаты тестов для заданного пользователя."""
        stmt = select(TestResult).where(TestResult.user_id == user_id)
        return self.session.exec(stmt).all()

    def ListResultsByTest(self, test_id: int) -> List[TestResult]:
        """Возвращает все результаты для указанного теста."""
        stmt = select(TestResult).where(TestResult.test_id == test_id)
        return self.session.exec(stmt).all()

    def CreateTestResult(
        self,
        user_id: int,
        test_id: int,
        score: float,
        max_score: float,
        passed: bool
    ) -> TestResult:
        """Создаёт новый результат теста для пользователя."""
        result = TestResult(
            user_id=user_id,
            test_id=test_id,
            score=score,
            max_score=max_score,
            passed=passed
        )
        self.session.add(result)
        self.session.commit()
        self.session.refresh(result)
        return result

    def UpdateTestResult(
        self,
        result_id: int,
        data: Dict[str, Any]
    ) -> Optional[TestResult]:
        """Обновляет поля результата теста по переданному словарю."""
        result = self.GetResultById(result_id)
        if not result:
            return None
        for field, value in data.items():
            if hasattr(result, field):
                setattr(result, field, value)
        self.session.add(result)
        self.session.commit()
        self.session.refresh(result)
        return result

    def DeleteTestResult(self, result_id: int) -> bool:
        """Удаляет результат теста по ID. Возвращает True, если удаление прошло успешно."""
        try:
            stmt = delete(TestResult).where(TestResult.id == result_id)
            res = self.session.exec(stmt)
            self.session.commit()
            return res.rowcount > 0
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def ExportTestResults(self) -> List[Dict[str, Any]]:
        """Экспортирует все результаты тестов в формат JSON-подобных словарей."""
        results = self.ListAllResults()
        return [
            {
                "id": r.id,
                "user_id": r.user_id,
                "test_id": r.test_id,
                "score": float(r.score),
                "max_score": float(r.max_score),
                "passed": r.passed,
                "taken_at": r.taken_at.isoformat()
            }
            for r in results
        ]

    def ImportTestResults(
        self,
        data: List[Dict[str, Any]]
    ) -> List[TestResult]:
        """Импортирует результаты тестов из JSON-подобного списка и возвращает созданные объекты."""
        created: List[TestResult] = []
        for item in data:
            result = TestResult(
                user_id=item.get("user_id"),
                test_id=item.get("test_id"),
                score=item.get("score", 0),
                max_score=item.get("max_score", 0),
                passed=item.get("passed", False)
            )
            self.session.add(result)
            created.append(result)
        self.session.commit()
        for r in created:
            self.session.refresh(r)
        return created
