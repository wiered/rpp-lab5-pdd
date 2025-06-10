from typing import List, Optional, Dict, Any

from sqlmodel import Session, select, delete, update
from sqlalchemy.exc import SQLAlchemyError

from src.models import Question

class QuestionRepository:
    def __init__(self, session: Session):
        self.session = session

    def ListAllQuestions(self) -> List[Question]:
        """Возвращает список всех вопросов."""
        stmt = select(Question)
        return self.session.exec(stmt).all()

    def GetQuestionById(self, question_id: int) -> Optional[Question]:
        """Возвращает вопрос по ID или None, если не найден."""
        stmt = select(Question).where(Question.id == question_id)
        return self.session.exec(stmt).first()

    def ListQuestionsByTest(self, test_id: int) -> List[Question]:
        """Возвращает список вопросов для заданного теста."""
        stmt = select(Question).where(Question.test_id == test_id)
        return self.session.exec(stmt).all()

    def CreateQuestion(self, test_id: int, text: str, weight: int = 1) -> Question:
        """Создаёт новый вопрос в указанном тесте."""
        question = Question(test_id=test_id, text=text, weight=weight)
        self.session.add(question)
        self.session.commit()
        self.session.refresh(question)
        return question

    def UpdateQuestion(self, question_id: int, data: Dict[str, Any]) -> Optional[Question]:
        """Обновляет поля вопроса по переданному словарю data."""
        question = self.GetQuestionById(question_id)
        if not question:
            return None
        for field, value in data.items():
            if hasattr(question, field):
                setattr(question, field, value)
        self.session.add(question)
        self.session.commit()
        self.session.refresh(question)
        return question

    def DeleteQuestion(self, question_id: int) -> bool:
        """Удаляет вопрос по ID. Возвращает True, если удаление прошло успешно."""
        try:
            stmt = delete(Question).where(Question.id == question_id)
            result = self.session.exec(stmt)
            self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def ExportQuestions(self) -> List[Dict[str, Any]]:
        """Экспортирует все вопросы в формат JSON-подобных словарей."""
        questions = self.ListAllQuestions()
        return [
            {"id": q.id, "test_id": q.test_id, "text": q.text, "weight": q.weight}
            for q in questions
        ]

    def ImportQuestions(self, data: List[Dict[str, Any]]) -> List[Question]:
        """Импортирует вопросы из JSON-подобного списка и возвращает созданные объекты."""
        created: List[Question] = []
        for item in data:
            question = Question(
                test_id=item.get("test_id"),
                text=item.get("text", ""),
                weight=item.get("weight", 1)
            )
            self.session.add(question)
            created.append(question)
        self.session.commit()
        for q in created:
            self.session.refresh(q)
        return created
