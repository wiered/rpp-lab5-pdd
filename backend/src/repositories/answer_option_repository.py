from typing import List, Optional, Dict, Any

from sqlmodel import Session, select, delete, update
from sqlalchemy.exc import SQLAlchemyError

from src.models import AnswerOption

class AnswerOptionRepository:
    def __init__(self, session: Session):
        self.session = session

    def ListAllOptions(self) -> List[AnswerOption]:
        """Возвращает список всех вариантов ответов."""
        stmt = select(AnswerOption)
        return self.session.exec(stmt).all()

    def GetOptionById(self, option_id: int) -> Optional[AnswerOption]:
        """Возвращает вариант ответа по его ID или None, если не найден."""
        stmt = select(AnswerOption).where(AnswerOption.id == option_id)
        return self.session.exec(stmt).first()

    def ListOptionsByQuestion(self, question_id: int) -> List[AnswerOption]:
        """Возвращает все варианты ответов для заданного вопроса."""
        stmt = select(AnswerOption).where(AnswerOption.question_id == question_id)
        return self.session.exec(stmt).all()

    def CreateOption(self, question_id: int, text: str, is_correct: bool = False) -> AnswerOption:
        """Создаёт новый вариант ответа для вопроса."""
        option = AnswerOption(question_id=question_id, text=text, is_correct=is_correct)
        self.session.add(option)
        self.session.commit()
        self.session.refresh(option)
        return option

    def UpdateOption(self, option_id: int, data: Dict[str, Any]) -> Optional[AnswerOption]:
        """Обновляет поля варианта ответа по переданному словарю."""
        option = self.GetOptionById(option_id)
        if not option:
            return None
        for field, value in data.items():
            if hasattr(option, field):
                setattr(option, field, value)
        self.session.add(option)
        self.session.commit()
        self.session.refresh(option)
        return option

    def DeleteOption(self, option_id: int) -> bool:
        """Удаляет вариант ответа по ID. Возвращает True, если удаление прошло успешно."""
        try:
            stmt = delete(AnswerOption).where(AnswerOption.id == option_id)
            result = self.session.exec(stmt)
            self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def ExportOptions(self) -> List[Dict[str, Any]]:
        """Экспортирует все варианты ответов в JSON-подобный список."""
        options = self.ListAllOptions()
        return [
            {"id": opt.id, "question_id": opt.question_id, "text": opt.text, "is_correct": opt.is_correct}
            for opt in options
        ]

    def ImportOptions(self, data: List[Dict[str, Any]]) -> List[AnswerOption]:
        """Импортирует варианты ответов из JSON-подобного списка."""
        created: List[AnswerOption] = []
        for item in data:
            option = AnswerOption(
                question_id=item.get("question_id"),
                text=item.get("text", ""),
                is_correct=item.get("is_correct", False)
            )
            self.session.add(option)
            created.append(option)
        self.session.commit()
        for opt in created:
            self.session.refresh(opt)
        return created
