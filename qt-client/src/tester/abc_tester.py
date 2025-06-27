from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Tuple
from dataclasses import dataclass

class BaseTester(ABC, Iterator[Dict[str, Any]]):
    """
    Абстрактный интерфейс теста.
    Позволяет по-очереди выдавать экземпляры Question
    и сохранять ответы.
    """

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        self._reset_iterator()
        return self

    @property
    def questions(self) -> List[Dict[str, Any]  ]:
        ...

    @property
    def answers(self) -> Dict[str, Any]:
        ...

    @abstractmethod
    def _reset_iterator(self) -> None:
        """Сбросить счётчик на начало теста."""
        ...

    @abstractmethod
    def __next__(self) -> Dict[str, Any]:
        """Вернуть следующий вопрос."""
        ...

    @abstractmethod
    def get_question(self, question_id: str) -> Dict[str, Any]:
        """Возвращает вопрос по его id

        Args:
            question_id (str): id вопроса

        Returns:
            Question: вопрос
        """
        ...

    @abstractmethod
    def get_answer_text(self, question_id: str, answer: str) -> List[str]:
        """Возвращает картеж в виде списка [Текст вопроса, текст ответа юзера]

        Args:
            question_id (str): id вопроса
            answer (str): ответ юзера

        Returns:
            List[str, str]: [Текст вопроса, текст ответа юзера]
        """
        ...

    @abstractmethod
    def answer(self, question_id: str, answer: Any) -> None:
        """
        Сохранить ответ (строка из options или число).
        """
        ...

    @abstractmethod
    def results(self) -> Dict[str, Any]:
        """Вернуть словарь {question_id: answer}."""
        ...

