from abc import ABC
from typing import List, Dict, Any, Iterator

from .abc_tester import (
    BaseTester
    )




class WebTester(BaseTester, ABC):
    def __init__(
        self,
        test_id: int,
        category_id: int,
        title: str,
        max_attempts: int,
        questions: List[Dict] = None
    ):
        """
        questions: list of dicts, each of shape:
        {
          'question': {id, test_id, text, weight},
          'options': [{id, question_id, text, is_correct}, ...]
        }
        """
        self.test_id = test_id
        self.category_id = category_id
        self.title = title
        self.max_attempts = max_attempts

        # internal storage of question dicts
        self._questions: List[Dict[str, Any]] = []
        print(questions)
        for item in (questions or []):
            try:
                q = item['question']
            except KeyError:
                q = item
            opts = item['options']
            self._questions.append({
                'id':             q['id'],
                'test_id':        q.get('test_id'),
                'text':           q['text'],
                'weight':         q.get('weight'),
                'options':        opts,
                # 'answer' will be added once user answers
            })

        # iterator cursor
        self._idx = 0

    @property
    def questions(self) -> List[Dict[str, Any]]:
        """List of question dictionaries (with possible 'answer' keys)."""
        return self._questions

    @property
    def answers(self) -> Dict[str, Any]:
        """
        Returns a mapping of question_id -> answer (whatever was saved),
        only including questions that have been answered.
        """
        return {
            str(q['id']): q['answer']
            for q in self._questions
            if 'answer' in q
        }

    def _reset_iterator(self) -> None:
        """(Re)start iteration from the first question."""
        self._idx = 0

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        self._reset_iterator()
        return self

    def __next__(self) -> Dict[str, Any]:
        """Return next question dict, or raise StopIteration."""
        if self._idx >= len(self._questions):
            raise StopIteration
        q = self._questions[self._idx]
        self._idx += 1
        return q

    def get_question(self, question_id: str) -> Dict[str, Any]:
        """Lookup a question by its id."""
        for q in self._questions:
            if str(q['id']) == str(question_id):
                return q
        raise KeyError(f"No question found with id {question_id!r}")

    def get_answer_text(self, question_id: str, answer: Any) -> List[str]:
        """
        Given a question_id and an answer value (option id or text),
        return [question_text, user_answer_text].
        """
        q = self.get_question(question_id)
        question_text = q['text']
        # find the matching option
        for opt in q['options']:
            if str(opt['id']) == str(answer) or opt['text'] == answer:
                return [question_text, opt['text']]
        raise ValueError(f"Answer {answer!r} not found among options for question {question_id}")

    def answer(self, question_id: str, answer: Any) -> None:
        """
        Save the user's answer (option id or text) into the question dict
        under the key 'answer'.
        """
        q = self.get_question(question_id)
        q['answer'] = answer

    def results(self) -> Dict[str, Any]:
        """Return the same mapping as .answers."""
        return self.answers

