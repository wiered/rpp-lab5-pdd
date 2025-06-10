from typing import List, Optional, Dict, Any

from sqlmodel import Session, select, delete, update
from sqlalchemy.exc import SQLAlchemyError

from src.models import TestAnswer

class TestAnswerRepository:
    def __init__(self, session: Session):
        self.session = session

    def ListAllAnswers(self) -> List[TestAnswer]:
        """Возвращает список всех ответов пользователей на тесты."""
        stmt = select(TestAnswer)
        return self.session.exec(stmt).all()

    def GetTestAnswerById(self, answer_id: int) -> Optional[TestAnswer]:
        """Возвращает ответ по его ID или None, если не найден."""
        stmt = select(TestAnswer).where(TestAnswer.id == answer_id)
        return self.session.exec(stmt).first()

    def ListAnswersByResult(self, test_result_id: int) -> List[TestAnswer]:
        """Возвращает список ответов, связанных с конкретным результатом теста."""
        stmt = select(TestAnswer).where(TestAnswer.test_result_id == test_result_id)
        return self.session.exec(stmt).all()

    def ListAnswersByQuestion(self, question_id: int) -> List[TestAnswer]:
        """Возвращает все ответы на заданный вопрос по результатам тестов."""
        stmt = select(TestAnswer).where(TestAnswer.question_id == question_id)
        return self.session.exec(stmt).all()

    def CreateTestAnswer(
        self,
        test_result_id: int,
        question_id: int,
        selected_option_id: int
    ) -> TestAnswer:
        """Создаёт запись о выборе варианта ответа пользователем."""
        answer = TestAnswer(
            test_result_id=test_result_id,
            question_id=question_id,
            selected_option_id=selected_option_id
        )
        self.session.add(answer)
        self.session.commit()
        self.session.refresh(answer)
        return answer

    def UpdateTestAnswer(
        self,
        answer_id: int,
        data: Dict[str, Any]
    ) -> Optional[TestAnswer]:
        """Обновляет поля существующего ответа по переданному словарю."""
        answer = self.GetTestAnswerById(answer_id)
        if not answer:
            return None
        for field, value in data.items():
            if hasattr(answer, field):
                setattr(answer, field, value)
        self.session.add(answer)
        self.session.commit()
        self.session.refresh(answer)
        return answer

    def DeleteTestAnswer(self, answer_id: int) -> bool:
        """Удаляет ответ по ID. Возвращает True, если удаление успешно."""
        try:
            stmt = delete(TestAnswer).where(TestAnswer.id == answer_id)
            result = self.session.exec(stmt)
            self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def ExportTestAnswers(self) -> List[Dict[str, Any]]:
        """Экспортирует все ответы пользователей в JSON-подобный список."""
        answers = self.ListAllAnswers()
        return [
            {
                "id": ans.id,
                "test_result_id": ans.test_result_id,
                "question_id": ans.question_id,
                "selected_option_id": ans.selected_option_id
            }
            for ans in answers
        ]

    def ImportTestAnswers(
        self,
        data: List[Dict[str, Any]]
    ) -> List[TestAnswer]:
        """Импортирует ответы из JSON-подобного списка, возвращает созданные объекты."""
        created: List[TestAnswer] = []
        for item in data:
            answer = TestAnswer(
                test_result_id=item.get("test_result_id"),
                question_id=item.get("question_id"),
                selected_option_id=item.get("selected_option_id")
            )
            self.session.add(answer)
            created.append(answer)
        self.session.commit()
        for ans in created:
            self.session.refresh(ans)
        return created
